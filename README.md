# LLM Vendor Daily Digest

[English](#english) | [中文](#中文)

---

## English

This project collects vendor RSS/Atom feeds, filters items for a target date, and generates:

- `data/daily/YYYY-MM-DD.md`: a bilingual daily markdown digest
- `feed.xml`: a subscription-ready RSS feed where each item is one daily digest

### Why the digest can look late

Freshness depends on two things:

1. The report date you generate.
2. How fresh the upstream source feeds are.

The workflow is configured for `Asia/Hong_Kong` and now runs at `23:30` local time (`30 15 * * *` UTC) so the default report targets the same local calendar day instead of implicitly lagging by UTC.

Runtime logs also print a source health table:

- latest item date per source
- item count on the report date
- stale / empty / error status

If a source is stale, the digest will still look behind even when scheduling is correct.

### Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Edit `config/sources.yaml` to add, remove, or replace sources.

3. Run for the current day in your configured timezone:

```bash
python -m src.run_daily
```

4. Run for a specific date:

```bash
python -m src.run_daily --date 2026-03-12
```

5. Run for yesterday without hardcoding a date:

```bash
python -m src.run_daily --offset-days 1
```

### Configuration

Supported CLI flags:

- `--date YYYY-MM-DD`: generate a report for one explicit date
- `--timezone Asia/Hong_Kong`: override the report timezone
- `--offset-days 1`: shift the default report date back by N days
- `--stale-days 21`: stale threshold used in source health logs
- `--feed-limit 60`: number of daily digest entries kept in `feed.xml`

Environment variables:

- `REPORT_TIMEZONE` (default: system local time)
- `REPORT_OFFSET_DAYS` (default: `0`)
- `SOURCE_STALE_DAYS` (default: `21`)
- `DAILY_FEED_LIMIT` (default: `60`)
- `ZHIPU_API_KEY`
- `ZHIPU_API_BASE` (default: `https://open.bigmodel.cn/api/paas/v4`)
- `ZHIPU_MODEL` (default: `glm-4.7-flash`)
- `OPENAI_API_KEY`
- `OPENAI_API_BASE` (default: `https://api.openai.com/v1`)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)

If no AI API key is configured, the project falls back to an extractive bilingual list.

### GitHub Actions

Workflow: `.github/workflows/daily.yml`

- Schedule: `30 15 * * *` UTC
- Local schedule in Hong Kong: `23:30`
- Output files: `data/daily/YYYY-MM-DD.md`, `feed.xml`

### Feed Subscription

Repository feed:

```text
https://raw.githubusercontent.com/cyclez2000/llm-vendor-daily-digest/master/feed.xml
```

### Sources

`config/sources.yaml` format:

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```

Current sources include official feeds plus selected RSSHub transforms for sites without stable RSS.

### Troubleshooting

- No items for a day: the vendor may not have published on that date.
- A source shows `stale`: the upstream feed or selector likely needs replacement.
- A source shows `error`: check network access, RSSHub availability, or page structure changes.
- If the digest feels late, check both the report date and the source health summary before assuming the scheduler is wrong.

---

## 中文

这个项目会抓取大模型厂商的 RSS/Atom 源，按目标日期过滤内容，并生成：

- `data/daily/YYYY-MM-DD.md`：中英双语日报
- `feed.xml`：可直接订阅的聚合 RSS，每天一条日报

### 为什么会感觉“慢两天”

日报是否及时，取决于两个因素：

1. 生成时使用的是哪一天作为目标日期。
2. 上游源本身是不是新鲜。

现在工作流已经固定按 `Asia/Hong_Kong` 时区运行，并改为在香港时间 `23:30` 执行（UTC 为 `30 15 * * *`），默认抓取“当天”而不是受 GitHub runner 的 UTC 时区影响后再隐性滞后。

运行日志还会输出 source health 表，包含：

- 每个源的最新条目日期
- 目标日期当天命中的条目数
- `stale / empty / error` 状态

如果某个源已经 stale，就算调度时间正确，日报看起来也会偏旧。

### 快速开始

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 编辑 `config/sources.yaml`，添加、删除或替换抓取源。

3. 按当前时区的“当天”生成日报：

```bash
python -m src.run_daily
```

4. 指定某一天生成：

```bash
python -m src.run_daily --date 2026-03-12
```

5. 不写死日期，直接生成“昨天”：

```bash
python -m src.run_daily --offset-days 1
```

### 配置项

支持的命令行参数：

- `--date YYYY-MM-DD`：指定日报日期
- `--timezone Asia/Hong_Kong`：覆盖默认时区
- `--offset-days 1`：默认日期向前偏移 N 天
- `--stale-days 21`：source health 中判断 stale 的阈值
- `--feed-limit 60`：`feed.xml` 中保留多少天日报

环境变量：

- `REPORT_TIMEZONE`（默认：系统本地时区）
- `REPORT_OFFSET_DAYS`（默认：`0`）
- `SOURCE_STALE_DAYS`（默认：`21`）
- `DAILY_FEED_LIMIT`（默认：`60`）
- `ZHIPU_API_KEY`
- `ZHIPU_API_BASE`（默认：`https://open.bigmodel.cn/api/paas/v4`）
- `ZHIPU_MODEL`（默认：`glm-4.7-flash`）
- `OPENAI_API_KEY`
- `OPENAI_API_BASE`（默认：`https://api.openai.com/v1`）
- `OPENAI_MODEL`（默认：`gpt-4o-mini`）

如果没有配置 AI Key，项目会回退到抽取式的中英双语列表。

### GitHub Actions

工作流：`.github/workflows/daily.yml`

- UTC cron：`30 15 * * *`
- 香港时间：`23:30`
- 输出文件：`data/daily/YYYY-MM-DD.md`、`feed.xml`

### RSS 订阅

仓库聚合订阅地址：

```text
https://raw.githubusercontent.com/cyclez2000/llm-vendor-daily-digest/master/feed.xml
```

### 源配置

`config/sources.yaml` 格式如下：

```yaml
sources:
  - name: Example Vendor
    rss: https://example.com/blog/rss.xml
    site: https://example.com/blog
    tags: [vendor, blog]
```

当前配置同时包含：

- 官方 RSS/Atom 源
- 对没有稳定 RSS 的站点使用 RSSHub transform

### 排查建议

- 某天没有内容：通常是厂商当天没有发布。
- 源状态为 `stale`：通常表示上游 feed 太旧，或者页面选择器失效，需要替换。
- 源状态为 `error`：优先检查网络、RSSHub 可用性和页面结构变更。
- 如果体感“慢”，先看目标日期和 source health，再判断是不是调度问题。
