from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
import os
import re
import subprocess
import sys

import yaml
from dateutil import tz

from .fetch import Item, Source, dedupe_items, fetch_feed, filter_items_by_date
from .rss import build_rss
from .summarize import summarize_items

_DAILY_REPORT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


@dataclass
class SourceHealth:
    name: str
    total_items: int
    items_on_report_date: int
    latest_date: date | None
    error: str | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_sources(path: Path) -> list[Source]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_sources = data.get("sources", [])
    sources: list[Source] = []
    for item in raw_sources:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        rss = (item.get("rss") or "").strip()
        if not name or not rss:
            continue
        sources.append(
            Source(
                name=name,
                rss=rss,
                site=item.get("site"),
                tags=item.get("tags"),
            )
        )
    return sources


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM vendor daily digest")
    parser.add_argument(
        "--config",
        default=str(_repo_root() / "config" / "sources.yaml"),
        help="Path to sources.yaml",
    )
    parser.add_argument(
        "--output-dir",
        default=str(_repo_root() / "data" / "daily"),
        help="Directory for daily markdown reports",
    )
    parser.add_argument(
        "--date",
        help="Report date (YYYY-MM-DD). Defaults to yesterday in local time.",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=int(os.getenv("SOURCE_STALE_DAYS", "21")),
        help="A source is stale when latest item age exceeds this many days.",
    )
    parser.add_argument(
        "--feed-limit",
        type=int,
        default=int(os.getenv("DAILY_FEED_LIMIT", "60")),
        help="Maximum number of daily digest entries included in feed.xml.",
    )
    return parser.parse_args(argv)


def _resolve_repo_slug() -> str:
    repo = (os.getenv("GITHUB_REPOSITORY") or "").strip()
    if repo:
        return repo

    try:
        proc = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=_repo_root(),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""

    remote = proc.stdout.strip()
    if not remote:
        return ""

    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/.]+?)(?:\.git)?/?$", remote)
    if not match:
        return ""
    return match.group("slug")


def _strip_report_header(content: str) -> str:
    lines = content.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    return "\n".join(lines).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _build_daily_feed_items(
    output_dir: Path,
    repo_slug: str,
    local_tz: tz.tzfile | tz.tzlocal | None,
    limit: int,
) -> list[Item]:
    if not output_dir.exists():
        return []

    report_paths = [
        path
        for path in output_dir.iterdir()
        if path.is_file() and _DAILY_REPORT_RE.match(path.name)
    ]
    report_paths.sort(key=lambda p: p.name, reverse=True)

    items: list[Item] = []
    for path in report_paths[:limit]:
        try:
            report_date = datetime.strptime(path.stem, "%Y-%m-%d").date()
        except ValueError:
            continue

        link = (
            f"https://github.com/{repo_slug}/blob/master/data/daily/{path.name}"
            if repo_slug
            else "https://github.com/"
        )
        body = _strip_report_header(path.read_text(encoding="utf-8"))
        summary = _truncate(body, 12000) if body else "No digest content."
        published = datetime.combine(report_date, time(hour=12))
        if local_tz:
            published = published.replace(tzinfo=local_tz)

        items.append(
            Item(
                source="Daily Digest",
                title=f"Daily Digest / 日报摘要 ({report_date.isoformat()})",
                link=link,
                published=published,
                summary=summary,
            )
        )
    return items


def _print_source_health(rows: list[SourceHealth], report_date: date, stale_days: int) -> None:
    stale_days = max(stale_days, 0)
    print(f"Source health for {report_date.isoformat()} (stale > {stale_days} days):")
    stale_sources: list[str] = []
    empty_sources: list[str] = []
    error_sources: list[str] = []

    for row in sorted(rows, key=lambda r: r.name.lower()):
        if row.error:
            status = "error"
            error_sources.append(row.name)
            latest = "-"
            age_text = "-"
        elif row.latest_date is None or row.total_items == 0:
            status = "empty"
            empty_sources.append(row.name)
            latest = "-"
            age_text = "-"
        else:
            age_days = max((report_date - row.latest_date).days, 0)
            latest = row.latest_date.isoformat()
            age_text = str(age_days)
            if age_days > stale_days:
                status = "stale"
                stale_sources.append(row.name)
            else:
                status = "ok"

        line = (
            f"- {row.name}: status={status}, total={row.total_items}, "
            f"on_date={row.items_on_report_date}, latest={latest}, age_days={age_text}"
        )
        if row.error:
            line += f", error={_truncate(row.error, 200)}"
        print(line)

    print(
        "Health summary: "
        f"{len(rows)} sources, {len(stale_sources)} stale, "
        f"{len(empty_sources)} empty, {len(error_sources)} error."
    )


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    local_tz = tz.tzlocal()

    if args.date:
        try:
            report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid --date format, expected YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        report_date = (datetime.now(local_tz) - timedelta(days=1)).date()

    sources = _load_sources(Path(args.config))
    if not sources:
        print("No sources configured. Update config/sources.yaml.", file=sys.stderr)
        return 1

    all_items: list[Item] = []
    health_rows: list[SourceHealth] = []
    for source in sources:
        try:
            source_items = fetch_feed(source, local_tz)
            all_items.extend(source_items)
            latest = max((item.published.date() for item in source_items), default=None)
            items_on_report_date = sum(1 for item in source_items if item.published.date() == report_date)
            health_rows.append(
                SourceHealth(
                    name=source.name,
                    total_items=len(source_items),
                    items_on_report_date=items_on_report_date,
                    latest_date=latest,
                )
            )
        except Exception as exc:
            print(f"Failed to fetch {source.name}: {exc}", file=sys.stderr)
            health_rows.append(
                SourceHealth(
                    name=source.name,
                    total_items=0,
                    items_on_report_date=0,
                    latest_date=None,
                    error=str(exc),
                )
            )

    _print_source_health(health_rows, report_date, args.stale_days)

    deduped_items = dedupe_items(all_items)
    items = filter_items_by_date(deduped_items, report_date)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{report_date}.md"

    header = f"# Daily Digest / 日报摘要 ({report_date})\n\n"
    if not items:
        body = "No items found for this date. / 当日未找到相关条目。\n"
    else:
        body = summarize_items(items, report_date.isoformat())

    output_path.write_text(header + body, encoding="utf-8")

    repo_slug = _resolve_repo_slug()
    channel_link = f"https://github.com/{repo_slug}" if repo_slug else "https://github.com/"
    feed_link = (
        f"https://raw.githubusercontent.com/{repo_slug}/master/feed.xml"
        if repo_slug
        else None
    )
    feed_items = _build_daily_feed_items(
        output_dir=output_dir,
        repo_slug=repo_slug,
        local_tz=local_tz,
        limit=max(args.feed_limit, 1),
    )
    feed_xml = build_rss(
        feed_items,
        channel_title="LLM Vendor Daily Digest",
        channel_link=channel_link,
        channel_description="Bilingual daily digests generated from vendor sources.",
        feed_link=feed_link,
    )
    feed_path = _repo_root() / "feed.xml"
    feed_path.write_text(feed_xml, encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"Wrote {feed_path} with {len(feed_items)} daily entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
