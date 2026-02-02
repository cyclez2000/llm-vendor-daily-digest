from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

import yaml
from dateutil import tz

from .fetch import Source, dedupe_items, fetch_feed, filter_items_by_date
from .rss import build_rss
from .summarize import summarize_items


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
    return parser.parse_args(argv)


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

    all_items = []
    for source in sources:
        try:
            all_items.extend(fetch_feed(source, local_tz))
        except Exception as exc:
            print(f"Failed to fetch {source.name}: {exc}", file=sys.stderr)

    deduped_items = dedupe_items(all_items)
    items = filter_items_by_date(deduped_items, report_date)

    # Build an aggregated RSS feed from recent items (latest first).
    feed_items = sorted(deduped_items, key=lambda i: i.published, reverse=True)[:200]
    repo = os.getenv("GITHUB_REPOSITORY", "")
    channel_link = f"https://github.com/{repo}" if repo else "https://github.com/"
    feed_link = f"https://raw.githubusercontent.com/{repo}/master/feed.xml" if repo else None
    feed_xml = build_rss(
        feed_items,
        channel_title="LLM Vendor Daily Digest",
        channel_link=channel_link,
        channel_description="Aggregated RSS feed generated from vendor sources.",
        feed_link=feed_link,
    )
    (_repo_root() / "feed.xml").write_text(feed_xml, encoding="utf-8")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{report_date}.md"

    header = f"# Daily Digest / 日报摘要 ({report_date})\n\n"
    if not items:
        body = "No items found for this date. / 当日未找到相关条目。\n"
    else:
        body = summarize_items(items, report_date.isoformat())

    output_path.write_text(header + body, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
