from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import os
from typing import Iterable

import requests

from .fetch import Item


def _truncate(text: str, limit: int = 240) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _group_items(items: Iterable[Item]):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.source].append(item)
    return grouped


def _format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def _fallback_digest(items: list[Item]) -> str:
    grouped = _group_items(items)
    lines: list[str] = []
    lines.append("## English")
    for source in sorted(grouped.keys()):
        lines.append(f"### {source}")
        for item in grouped[source]:
            summary = f" - {_truncate(item.summary)}" if item.summary else ""
            entry = f"[{item.title}]({item.link}) ({_format_date(item.published)}){summary}"
            lines.append(f"- {entry}")
        lines.append("")
    lines.append("## 中文")
    for source in sorted(grouped.keys()):
        lines.append(f"### {source}")
        for item in grouped[source]:
            summary = f" - {_truncate(item.summary)}" if item.summary else ""
            entry = f"[{item.title}]({item.link}) ({_format_date(item.published)}){summary}"
            lines.append(f"- {entry}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _openai_chat(messages: list[dict], model: str, api_base: str, api_key: str) -> str:
    url = api_base.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _resolve_chat_config() -> tuple[str | None, str, str]:
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    if zhipu_key:
        api_base = os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
        model = os.getenv("ZHIPU_MODEL", "glm-4.7-flash")
        return zhipu_key, api_base, model

    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return api_key, api_base, model


def summarize_items(items: list[Item], report_date: str) -> str:
    api_key, api_base, model = _resolve_chat_config()

    if not api_key:
        return _fallback_digest(items)

    grouped = _group_items(items)
    bullets: list[str] = []
    for source in sorted(grouped.keys()):
        for item in grouped[source]:
            bullets.append(
                f"[{source}] {item.title} | {item.link} | {item.summary or ''}"
            )

    system = (
        "You are an assistant that writes concise daily vendor digests. "
        "Return markdown with two top-level sections: '## English' and '## 中文'. "
        "Within each section, group by vendor using '### Vendor'. "
        "Each item should be a single bullet with 1-2 sentences, always include the source link."
    )
    user = (
        f"Write a bilingual daily digest for {report_date}.\n"
        "Items:\n" + "\n".join(bullets)
    )

    content = _openai_chat(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=model,
        api_base=api_base,
        api_key=api_key,
    )
    return content.rstrip() + "\n"
