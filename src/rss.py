from __future__ import annotations

from datetime import datetime
from email.utils import format_datetime
from html import escape
from typing import Iterable
import xml.etree.ElementTree as ET

from dateutil import tz

from .fetch import Item


def _rfc822(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz.UTC)
    return format_datetime(dt.astimezone(tz.UTC))


def build_rss(
    items: Iterable[Item],
    *,
    channel_title: str,
    channel_link: str,
    channel_description: str,
    feed_link: str | None = None,
) -> str:
    rss = ET.Element("rss", version="2.0", attrib={"xmlns:atom": "http://www.w3.org/2005/Atom"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = channel_title
    ET.SubElement(channel, "link").text = channel_link
    ET.SubElement(channel, "description").text = channel_description

    if feed_link:
        atom_link = ET.SubElement(channel, "atom:link")
        atom_link.set("href", feed_link)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")

    for item in items:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item.title
        ET.SubElement(node, "link").text = item.link
        ET.SubElement(node, "guid").text = item.link
        ET.SubElement(node, "pubDate").text = _rfc822(item.published)
        if item.summary:
            ET.SubElement(node, "description").text = escape(item.summary)

    xml = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return xml.decode("utf-8") + "\n"
