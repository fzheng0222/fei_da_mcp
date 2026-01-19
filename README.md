# DA-MCP

Data Analysis MCP Server - AI-powered deep dive data analysis via BigQuery.

## What is this?

An MCP server that lets you analyze data using natural language. Say "forecast mmr" and get a full report.

## Quick Start

```bash
python main.py
```

Then in Cursor, just ask:
- `"bq analysis"` → General BigQuery exploration
- `"forecast mmr"` → Weekly MRR report
- `"onboarding flow"` → User funnel analysis

---

## MCP Components

MCP servers have 3 components: **Tools** (actions), **Resources** (read-only data), **Prompts** (templates).

**0. General Analysis** - Daily data exploration

| Type | Name | What it does |
|------|------|--------------|
| Tool | `list_tables` | List tables in a dataset |
| Tool | `describe_table` | Get table schema |
| Tool | `sample_table` | Quick row preview |
| Tool | `query_bigquery` | Run SQL query |
| Tool | `profile_table` | Data quality check |
| Resource | `schema://bigquery` | Available BQ tables |
| Prompt | `explore`, `profile`, `quick_stats` | Analysis templates |

**1. Forecast MMR** - Weekly MRR predictions

| Type | Name | What it does |
|------|------|--------------|
| Tool | `forecast_mmr` | Generate weekly report |
| Tool | `forecast_trend` | Simple trend forecast |
| Resource | `forecast://latest` | 4-week predictions |
| Resource | `forecast://feature_importance` | XGBoost weights |
| Prompt | `forecast_drivers`, `forecast_actions` | Analysis templates |

**2. Onboarding Flow** - User funnel analysis

| Type | Name | What it does |
|------|------|--------------|
| - | Query template | See `README(DEV-FACING).md` |

---

## Domains

| # | Domain | Status |
|---|--------|--------|
| 0 | general_analysis | Ready |
| 1 | forecast_mmr | Ready |
| 2 | onboarding_flow | Ready |
| 3 | farming_insight | Placeholder |
| 4 | user_segmentation | Placeholder |
| 5 | sybil | Placeholder |

---

## Structure

```
da-mcp/
├── main.py           # MCP server
├── core/             # BigQuery client
└── domains/          # Each domain has: tools.py, resources.py, prompts.py
    ├── _0_general_analysis/
    ├── _1_forecast_mmr/
    ├── _2_onboarding_flow_analysis/
    └── ...
```

---

## How to Add a Domain

1. Create folder: `domains/_X_name/`
2. Add files: `tools.py`, `resources.py`, `prompts.py`, `README(USER-FACING).md`, `README(DEV-FACING).md`
3. Register in `main.py`

See `_1_forecast_mmr` for a complete example.

---

## Future Considerations

| Area | What | Why |
|------|------|-----|
| **Guardrails** | Query cost limits, row limits, table allowlists | Prevent expensive/dangerous queries |
| **Memory** | Conversation history, past queries, user preferences | Context-aware responses, learn from usage |
| **Orchestration** | Multi-step workflows, chained tools, auto-retry | Complex analysis pipelines (e.g., "weekly report → slack → email") |
| **Caching** | Query result caching, schema caching | Faster responses, lower BQ costs |
| **Auth** | User-level permissions, dataset access control | Multi-user support |
| **Observability** | Query logs, usage metrics, error tracking | Debug and optimize |
