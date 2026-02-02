# LLM Vendor Daily Digest

[English](#english) | [中文](#中文)

---

## English

Daily digest generator for LLM vendors. It collects RSS/Atom feeds and produces:
- a **daily markdown report** under `data/daily/YYYY-MM-DD.md`
- an **aggregated RSS feed** at `feed.xml` (subscribe once, get all updates)

### Subscribe (one-click)

After the workflow runs, subscribe to:

```
https://raw.githubusercontent.com/cyclez2000/llm-vendor-daily-digest/master/feed.xml
```

This feed aggregates the latest items from all sources (latest first).

### Quick start (local)

1. Edit `config/sources.yaml` to add or remove sources.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run locally (defaults to **yesterday** in local time):

```bash
python -m src.run_daily
```

Or specify a date:

```bash
python -m src.run_daily --date 2026-01-29
```

### GitHub Actions

Workflow: `.github/workflows/daily.yml`  
Schedule: `0 1 * * *` (UTC)

Outputs:
- `data/daily/YYYY-MM-DD.md`
- `feed.xml`

### Optional AI summaries

If `ZHIPU_API_KEY` is set, the digest is summarized by Zhipu (GLM-4.7-Flash by default).
Otherwise, if `OPENAI_API_KEY` is set, it uses an OpenAI-compatible API.
If neither is set, it falls back to an extractive list.

Environment variables:
- `ZHIPU_API_KEY` (required to enable Zhipu summaries)
- `ZHIPU_API_BASE` (default: `https://open.bigmodel.cn/api/paas/v4`)
- `ZHIPU_MODEL` (default: `glm-4.7-flash`)
- `OPENAI_API_KEY` (required if ZHIPU is not set)
- `OPENAI_API_BASE` (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

### Sources format

`config/sources.yaml` example:

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```

### Notes & troubleshooting

- Only items **published on the target date** are included in the daily report.
- Some sources use RSSHub. If RSSHub is blocked, the code falls back to direct HTML/JSON parsing.
- If a date looks empty, check whether the vendor posted on that date.

---

## 中文

这是一个大模型厂商的日报生成器，会抓取 RSS/Atom 源并生成：
- **每日 Markdown 摘要**：`data/daily/YYYY-MM-DD.md`
- **聚合 RSS 订阅**：`feed.xml`（一次订阅即可获取所有更新）

### 一键订阅

工作流跑完后，订阅：

```
https://raw.githubusercontent.com/cyclez2000/llm-vendor-daily-digest/master/feed.xml
```

该订阅会汇总所有来源的最新更新（按时间倒序）。

### 本地快速开始

1. 编辑 `config/sources.yaml` 添加/删除来源。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 本地运行（默认使用本地时间“昨天”）：

```bash
python -m src.run_daily
```

或指定日期：

```bash
python -m src.run_daily --date 2026-01-29
```

### GitHub Actions

工作流：`.github/workflows/daily.yml`  
计划任务：`0 1 * * *`（UTC）

输出：
- `data/daily/YYYY-MM-DD.md`
- `feed.xml`

### 可选 AI 摘要

设置 `ZHIPU_API_KEY` 后使用智谱（默认 GLM-4.7-Flash）生成摘要。
如果没有智谱 Key，但设置了 `OPENAI_API_KEY`，则使用 OpenAI 兼容接口。
都未设置时回退为抽取式列表。

环境变量：
- `ZHIPU_API_KEY`（启用智谱摘要必需）
- `ZHIPU_API_BASE`（默认：`https://open.bigmodel.cn/api/paas/v4`）
- `ZHIPU_MODEL`（默认：`glm-4.7-flash`）
- `OPENAI_API_KEY`（未设置智谱时必需）
- `OPENAI_API_BASE`（默认：`https://api.openai.com/v1`）
- `OPENAI_MODEL`（默认：`gpt-4o-mini`）

### 来源格式

`config/sources.yaml` 示例：

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```

### 说明与排查

- 每日日报只包含**目标日期当天**发布的内容。
- 部分来源使用 RSSHub，若被拦截会自动回退为直连解析。
- 某天为空通常是该厂商当日没有更新。
