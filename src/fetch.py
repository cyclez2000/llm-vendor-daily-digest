from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
import json
import re
from urllib.parse import parse_qs, urljoin, urlparse

import feedparser
from dateutil import parser as date_parser
from dateutil import tz
import requests
from bs4 import BeautifulSoup


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


def _parse_date_value(value: str | None, local_tz: tz.tzfile | tz.tzlocal | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = date_parser.parse(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.UTC)
        if local_tz:
            dt = dt.astimezone(local_tz)
        return dt
    except (ValueError, TypeError):
        return None


def _is_rsshub_transform(url: str) -> bool:
    return "/transform/html" in url or "/transform/json" in url


def _rsshub_params(url: str) -> tuple[str | None, dict[str, str]]:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    params = {k: v[0] for k, v in qs.items() if v}
    target = params.get("url")
    return target, params


def _select_first_text(node, selectors: str | None) -> str | None:
    if not selectors:
        return None
    for selector in [s.strip() for s in selectors.split(",") if s.strip()]:
        found = node.select_one(selector)
        if found:
            text = found.get_text(" ", strip=True)
            if text:
                return text
    return None


def _select_first_node(node, selector: str | None):
    if not selector:
        return None
    return node.select_one(selector)


def _parse_rsshub_html(
    source: Source, local_tz: tz.tzfile | tz.tzlocal | None, target_url: str, params: dict[str, str]
) -> list[Item]:
    resp = requests.get(target_url, headers={"User-Agent": "llm-vendor-daily/0.1"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    item_selector = params.get("item")
    items = soup.select(item_selector) if item_selector else []
    title_selector = params.get("itemTitle")
    link_selector = params.get("itemLink")
    link_attr = params.get("itemLinkAttr", "href")
    link_prefix = params.get("itemLinkPrefix")
    date_selector = params.get("itemPubDate")
    date_attr = params.get("itemPubDateAttr")
    desc_selector = params.get("itemDesc")
    desc_attr = params.get("itemDescAttr")

    results: list[Item] = []
    for node in items:
        title = _select_first_text(node, title_selector)
        if not title:
            continue

        link_node = _select_first_node(node, link_selector) if link_selector else None
        if link_node is None and getattr(node, "name", None) == "a":
            link_node = node
        link = link_node.get(link_attr) if link_node else None
        if not link:
            continue
        if link_prefix and not link.startswith("http"):
            link = urljoin(link_prefix, link)

        date_node = _select_first_node(node, date_selector) if date_selector else None
        if date_node is None:
            date_node = node.find("time")
        date_value = None
        if date_node is not None:
            if date_attr:
                date_value = date_node.get(date_attr)
            if not date_value:
                date_value = date_node.get("datetime") or date_node.get("dateTime")
            if not date_value:
                date_value = date_node.get_text(" ", strip=True)
        published = _parse_date_value(date_value, local_tz)
        if not published:
            continue

        desc_node = _select_first_node(node, desc_selector) if desc_selector else None
        summary = None
        if desc_node is not None:
            if desc_attr:
                summary = desc_node.get(desc_attr)
            if not summary:
                summary = desc_node.get_text(" ", strip=True)
        summary = _strip_html(summary) if summary else None

        results.append(
            Item(
                source=source.name,
                title=title,
                link=link,
                published=published,
                summary=summary,
            )
        )
    return results


def _get_json_path(data: dict, path: str | None):
    if not path:
        return None
    current = data
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _parse_rsshub_json(
    source: Source, local_tz: tz.tzfile | tz.tzlocal | None, target_url: str, params: dict[str, str]
) -> list[Item]:
    resp = requests.get(target_url, headers={"User-Agent": "llm-vendor-daily/0.1"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    items = _get_json_path(data, params.get("item"))
    if not isinstance(items, list):
        return []

    title_key = params.get("itemTitle")
    link_key = params.get("itemLink")
    link_prefix = params.get("itemLinkPrefix")
    date_key = params.get("itemPubDate")
    desc_key = params.get("itemDesc")

    results: list[Item] = []
    for entry in items:
        if not isinstance(entry, dict):
            continue
        title = entry.get(title_key) if title_key else None
        link = entry.get(link_key) if link_key else None
        if not title or not link:
            continue
        if link_prefix and not str(link).startswith("http"):
            link = urljoin(link_prefix, str(link))
        date_value = entry.get(date_key) if date_key else None
        published = _parse_date_value(date_value, local_tz)
        if not published:
            continue
        summary = entry.get(desc_key) if desc_key else None
        summary = _strip_html(summary) if summary else None
        results.append(
            Item(
                source=source.name,
                title=str(title).strip(),
                link=str(link).strip(),
                published=published,
                summary=summary,
            )
        )
    return results


def _fetch_rsshub_fallback(source: Source, local_tz: tz.tzfile | tz.tzlocal | None) -> list[Item]:
    target_url, params = _rsshub_params(source.rss)
    if not target_url:
        return []
    if "/transform/html" in source.rss:
        return _parse_rsshub_html(source, local_tz, target_url, params)
    if "/transform/json" in source.rss:
        return _parse_rsshub_json(source, local_tz, target_url, params)
    return []


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
    if items:
        return items
    if _is_rsshub_transform(source.rss):
        try:
            return _fetch_rsshub_fallback(source, local_tz)
        except requests.RequestException:
            return []
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
