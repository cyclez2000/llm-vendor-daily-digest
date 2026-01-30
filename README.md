# LLM Vendor Daily Digest

Collect vendor blog/news feeds and generate a daily markdown digest. Designed for a personal, GitHub Actions-based workflow.

## Quick start

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

## Optional AI summaries

If `ZHIPU_API_KEY` is set, the digest is summarized by Zhipu (GLM-4.7-Flash by default). Otherwise if `OPENAI_API_KEY` is set, it uses an OpenAI-compatible API. If neither is set, it falls back to a simple extractive list.

Environment variables:
- `ZHIPU_API_KEY` (required to enable Zhipu summaries)
- `ZHIPU_API_BASE` (default: `https://open.bigmodel.cn/api/paas/v4`)
- `ZHIPU_MODEL` (default: `glm-4.7-flash`)
- `OPENAI_API_KEY` (required to enable OpenAI summaries if ZHIPU is not set)
- `OPENAI_API_BASE` (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

## GitHub Actions

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

## Sources format

`config/sources.yaml` example:

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```