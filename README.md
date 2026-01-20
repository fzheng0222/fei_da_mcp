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

---

## MCP Components

MCP servers have 3 components: **Tools** (actions), **Resources** (read-only data), **Prompts** (templates).

**0. General Analysis** - Daily data exploration

| Tool | What it does |
|------|--------------|
| `list_tables` | List tables in a dataset |
| `describe_table` | Get table schema |
| `sample_table` | Quick row preview |
| `query_bigquery` | Run SQL query |

**1. Forecast MMR** - Weekly MRR predictions

| Tool | What it does |
|------|--------------|
| `forecast_mmr` | Generate weekly report |

---

## Domains

| # | Domain | Status |
|---|--------|--------|
| 0 | general_analysis | Ready |
| 1 | forecast_mmr | Ready |

---

## Structure

```
da-mcp/
├── main.py           # MCP server
├── core/             # BigQuery client
└── domains/
    ├── _0_general_analysis/
    └── _1_forecast_mmr/
```

---

## How to Add a Domain

1. Create folder: `domains/_X_name/`
2. Add files: `tools.py`, `resources.py`, `prompts.py`, `README.md`
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
