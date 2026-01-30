# LLM Vendor Daily Digest

[English](#english) | [中文](#中文)

---

## English

Collect vendor blog/news feeds and generate a daily markdown digest. Designed for a personal, GitHub Actions-based workflow.

### Quick start

1. Edit `config/sources.yaml` and add RSS/Atom feeds.
2. Create a virtualenv and install requirements:

```bash
pip install -r requirements.txt
```

3. Run locally (defaults to yesterday in local time):

```bash
python -m src.run_daily
```

Or specify a date:

```bash
python -m src.run_daily --date 2026-01-29
```

Output goes to `data/daily/YYYY-MM-DD.md`.

### Optional AI summaries

If `ZHIPU_API_KEY` is set, the digest is summarized by Zhipu (GLM-4.7-Flash by default). Otherwise if `OPENAI_API_KEY` is set, it uses an OpenAI-compatible API. If neither is set, it falls back to a simple extractive list.

Environment variables:
- `ZHIPU_API_KEY` (required to enable Zhipu summaries)
- `ZHIPU_API_BASE` (default: `https://open.bigmodel.cn/api/paas/v4`)
- `ZHIPU_MODEL` (default: `glm-4.7-flash`)
- `OPENAI_API_KEY` (required to enable OpenAI summaries if ZHIPU is not set)
- `OPENAI_API_BASE` (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

### GitHub Actions

The workflow runs daily and commits new digests back to the repo.

- File: `.github/workflows/daily.yml`
- Schedule: `0 1 * * *` (UTC)

To enable AI summaries on GitHub Actions, add repository secrets:
- `ZHIPU_API_KEY` (recommended)
- `ZHIPU_API_BASE` (optional)
- `ZHIPU_MODEL` (optional)
- `OPENAI_API_KEY` (optional, used only if ZHIPU is not set)
- `OPENAI_API_BASE` (optional)
- `OPENAI_MODEL` (optional)

### Sources format

`config/sources.yaml` example:

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```

---

## 中文

收集厂商博客/新闻 RSS 并生成每日 Markdown 摘要，适合个人使用 GitHub Actions 自动化。

### 快速开始

1. 编辑 `config/sources.yaml`，添加 RSS/Atom 源。
2. 创建虚拟环境并安装依赖：

```bash
pip install -r requirements.txt
```

3. 本地运行（默认使用本地时间的昨天）：

```bash
python -m src.run_daily
```

或指定日期：

```bash
python -m src.run_daily --date 2026-01-29
```

输出文件位于 `data/daily/YYYY-MM-DD.md`。

### 可选 AI 摘要

若设置 `ZHIPU_API_KEY`，则使用智谱（默认 GLM-4.7-Flash）生成摘要；否则如设置 `OPENAI_API_KEY`，则使用 OpenAI 兼容接口；两者都未设置时回退为简单摘录列表。

环境变量：
- `ZHIPU_API_KEY`（启用智谱摘要必需）
- `ZHIPU_API_BASE`（默认：`https://open.bigmodel.cn/api/paas/v4`）
- `ZHIPU_MODEL`（默认：`glm-4.7-flash`）
- `OPENAI_API_KEY`（未设置智谱时启用 OpenAI 摘要必需）
- `OPENAI_API_BASE`（默认：`https://api.openai.com/v1`）
- `OPENAI_MODEL`（默认：`gpt-4o-mini`）

### GitHub 自动化

工作流每日运行并将新摘要提交回仓库。

- 文件：`.github/workflows/daily.yml`
- 计划任务：`0 1 * * *`（UTC）

要在 GitHub Actions 上启用 AI 摘要，请添加仓库 Secrets：
- `ZHIPU_API_KEY`（推荐）
- `ZHIPU_API_BASE`（可选）
- `ZHIPU_MODEL`（可选）
- `OPENAI_API_KEY`（可选，仅在未设置智谱时使用）
- `OPENAI_API_BASE`（可选）
- `OPENAI_MODEL`（可选）

### 来源格式

`config/sources.yaml` 示例：

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```
