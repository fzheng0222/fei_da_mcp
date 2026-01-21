# Cursor MCP Configuration

## Quick Setup

### 1. Add to Cursor MCP Settings

Press `Cmd + ,` → Search "mcp" → Edit settings.json:

```json
{
  "mcpServers": {
    "ds-mrr": {
      "command": "/Users/fei.zheng/Documents/Github/ds-mrr/.venv/bin/python",
      "args": ["/Users/fei.zheng/Documents/Github/ds-mrr/main.py"]
    }
  }
}
```

### 2. Restart Cursor

`Cmd + Q` then reopen.

### 3. Test

Ask: "List tables in prod-im-data.mod_imx"

---

## Prerequisites

- Python 3.10+
- gcloud authenticated: `gcloud auth application-default login`
- Virtual env: `.venv/bin/python`

---

## Available Tools

| Tool | Purpose |
|------|---------|
| `forecast_mrr` | Generate weekly MRR forecast report |
| `list_tables` | List tables in a BQ dataset |
| `describe_table` | Get table schema |
| `sample_table` | Preview rows |
| `query_bigquery` | Run SQL queries |

---

## Troubleshooting

**"MCP server not found"**
- Check paths in config
- Restart Cursor completely

**"Auth failed"**
- Run: `gcloud auth application-default login`
- Restart MCP server

**"Table not found"**
- Check dataset/table name spelling
- Use `list_tables` to discover tables
