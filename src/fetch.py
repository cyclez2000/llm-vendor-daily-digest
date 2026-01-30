from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import re

import feedparser
from dateutil import parser as date_parser
from dateutil import tz


@dataclass(frozen=True)
class Source:
    name: str
    rss: str
    site: str | None = None
    tags: list[str] | None = None


@dataclass
class Item:
    source: str
    title: str
    link: str
    published: datetime
    summary: str | None = None


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub("", text).replace("\n", " ").strip()


def _parse_published(entry: dict, local_tz: tz.tzfile | tz.tzlocal | None) -> datetime | None:
    for key in ("published", "updated", "created"):
        value = entry.get(key)
        if value:
            try:
                dt = date_parser.parse(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tz.UTC)
                if local_tz:
                    dt = dt.astimezone(local_tz)
                return dt
            except (ValueError, TypeError):
                continue
    return None


def fetch_feed(source: Source, local_tz: tz.tzfile | tz.tzlocal | None) -> list[Item]:
    feed = feedparser.parse(
        source.rss,
        request_headers={"User-Agent": "llm-vendor-daily/0.1"},
    )
    items: list[Item] = []
    for entry in feed.entries:
        published = _parse_published(entry, local_tz)
        if not published:
            continue
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        summary = entry.get("summary") or entry.get("description") or ""
        summary = _strip_html(summary) if summary else None
        if not title or not link:
            continue
        items.append(
            Item(
                source=source.name,
                title=title,
                link=link,
                published=published,
                summary=summary,
            )
        )
    return items


def dedupe_items(items: Iterable[Item]) -> list[Item]:
    seen: set[str] = set()
    deduped: list[Item] = []
    for item in items:
        key = f"{item.link}::{item.title}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def filter_items_by_date(items: Iterable[Item], target_date) -> list[Item]:
    filtered = [item for item in items if item.published.date() == target_date]
    filtered.sort(key=lambda i: i.published)
    return filtered