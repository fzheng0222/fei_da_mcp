# DS-MRR

Data Science MRR Forecast Server - MRR forecasting and BigQuery exploration.

## Quick Start

```bash
python main.py
```

Then in Cursor, just ask:
- `"forecast mrr"` → Weekly MRR report

## Tools

| Tool | What it does |
|------|--------------|
| `forecast_mrr` | Generate weekly MRR forecast report |
| `list_tables` | List tables in a dataset |
| `describe_table` | Get table schema |
| `sample_table` | Quick row preview |
| `query_bigquery` | Run SQL query |

## Structure

```
ds-mrr/
├── main.py        # MCP server entry point
├── tools.py       # Tool definitions and handlers
├── prompts.py     # SCQA prompt for MRR forecast
├── resources.py   # Read-only data resources
├── bq_client.py   # BigQuery client
├── run.py         # Standalone XGBoost forecast script
└── requirements.txt
```

## Standalone Forecast

Run the XGBoost model directly and save results to BigQuery:

```bash
python run.py
```

This trains the model and writes to:
- `dev-im-platform.temp_fei_ai.t_forecast_feature_importance`
- `dev-im-platform.temp_fei_ai.t_forecast_predictions`
