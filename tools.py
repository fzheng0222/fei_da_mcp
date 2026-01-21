"""
DS-MRR Tools
=============
BigQuery exploration tools + MRR forecast tool.
"""

import json
import pandas as pd
from typing import Any, List
from mcp.types import Tool, TextContent
from bq_client import get_client
from prompts import get_prompt_content, TARGET_MRR


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

def get_tools():
    """Return list of all tools."""
    return [
        # BigQuery exploration tools
        Tool(
            name="list_tables",
            description="List all tables in a BigQuery dataset.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "Dataset ID (e.g., 'prod-im-data.mod_imx')"
                    }
                },
                "required": ["dataset"]
            }
        ),
        Tool(
            name="describe_table",
            description="Get schema (column names and types) for a BigQuery table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Full table ID (e.g., 'prod-im-data.mod_imx.hubspot_b2b_deal')"
                    }
                },
                "required": ["table"]
            }
        ),
        Tool(
            name="sample_table",
            description="Get a quick sample of rows from a table. No SQL needed!",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "Full table ID (e.g., 'prod-im-data.mod_imx.hubspot_b2b_deal')"
                    },
                    "rows": {
                        "type": "number",
                        "description": "Number of sample rows (default: 5)",
                        "default": 5
                    }
                },
                "required": ["table"]
            }
        ),
        Tool(
            name="query_bigquery",
            description="Run a SQL query on BigQuery and return results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query to run on BigQuery"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Max rows to return (default: 100)",
                        "default": 100
                    }
                },
                "required": ["sql"]
            }
        ),
        # MRR Forecast tool
        Tool(
            name="forecast_mrr",
            description="Generate the weekly MRR forecast report.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


# =============================================================================
# TOOL HANDLERS
# =============================================================================

async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    client = get_client()
    
    if name == "list_tables":
        return await _list_tables(client, arguments)
    elif name == "describe_table":
        return await _describe_table(client, arguments)
    elif name == "sample_table":
        return await _sample_table(client, arguments)
    elif name == "query_bigquery":
        return await _query_bigquery(client, arguments)
    elif name == "forecast_mrr":
        return await _forecast_mrr_report(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


# =============================================================================
# BIGQUERY TOOLS
# =============================================================================

async def _list_tables(client, arguments: Any) -> List[TextContent]:
    """List tables in a dataset."""
    dataset = arguments.get("dataset")
    if not dataset:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": "dataset is required"}))]
    
    try:
        tables = list(client.list_tables(dataset))
        table_list = [t.table_id for t in tables]
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "dataset": dataset,
                "tables": table_list,
                "count": len(table_list)
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


async def _describe_table(client, arguments: Any) -> List[TextContent]:
    """Get table schema."""
    table = arguments.get("table")
    if not table:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": "table is required"}))]
    
    try:
        table_ref = client.get_table(table)
        schema = [{"name": f.name, "type": f.field_type, "mode": f.mode} for f in table_ref.schema]
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "table": table,
                "row_count": table_ref.num_rows,
                "columns": schema
            }, indent=2)
        )]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


async def _sample_table(client, arguments: Any) -> List[TextContent]:
    """Get sample rows from a table."""
    table = arguments.get("table")
    rows = arguments.get("rows", 5)
    if not table:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": "table is required"}))]
    
    try:
        sql = f"SELECT * FROM `{table}` LIMIT {rows}"
        df = client.query(sql).to_dataframe()
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "table": table,
                "sample_rows": rows,
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records")
            }, indent=2, default=str)
        )]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


async def _query_bigquery(client, arguments: Any) -> List[TextContent]:
    """Run a SQL query."""
    sql = arguments.get("sql")
    limit = arguments.get("limit", 100)
    
    if not sql:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": "sql query is required"}))]
    
    try:
        query_job = client.query(sql)
        df = query_job.to_dataframe()
        
        truncated = False
        if len(df) > limit:
            df = df.head(limit)
            truncated = True
        
        result = {
            "success": True,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records"),
            "truncated": truncated,
            "message": f"Query returned {len(df)} rows" + (" (truncated)" if truncated else "")
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


# =============================================================================
# MRR FORECAST TOOL
# =============================================================================

async def _forecast_mrr_report(arguments: Any) -> List[TextContent]:
    """Generate the weekly MRR forecast report with SCQA-structured prompt."""
    try:
        client = get_client()
        PROJECT = "dev-im-platform"
        DATASET = "temp_fei_ai"
        
        # 1. Get current performance data
        df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.v_model_3_levers` ORDER BY week").to_dataframe()
        df = df.sort_values('week').reset_index(drop=True)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_mrr = float(latest['total_mrr'])
        wow_change = float(latest.get('mrr_change', 0))
        wow_pct = (wow_change / float(prev['total_mrr']) * 100) if prev['total_mrr'] else 0
        win_rate = float(latest.get('win_rate_pct', 0))
        at_risk_pct = float(latest.get('at_risk_pct', 0))
        at_risk_deals = int(latest.get('at_risk_deals', 0))
        
        # 2. Run forecast
        df[df.select_dtypes(include=['float64', 'int64', 'Int64']).columns] = df.select_dtypes(include=['float64', 'int64', 'Int64']).fillna(0)
        avg_change = float(df['mrr_change'].tail(4).mean())
        
        predictions = []
        forecast_mrr = current_mrr
        for i in range(4):
            forecast_mrr = forecast_mrr + avg_change
            predictions.append({"week": i + 1, "mrr": round(forecast_mrr / 1000, 0)})
        
        # 3. Get feature importance
        try:
            imp_df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.t_forecast_feature_importance` ORDER BY rank LIMIT 10").to_dataframe()
            top_features = imp_df.to_dict(orient='records')
        except:
            top_features = [{"lever": "Deal Close", "importance_pct": 74}]
        
        # 4. Get top deals
        try:
            deals_df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.v_next_best_action` ORDER BY priority ASC").to_dataframe()
            deals_to_win = deals_df[deals_df['action_type'] == 'WIN'].to_dict(orient='records')
            deals_to_save = deals_df[deals_df['action_type'] == 'SAVE'].to_dict(orient='records')
        except:
            deals_to_win, deals_to_save = [], []
        
        # 5. Get historical data for trajectory (15 weeks)
        history = df[['week', 'total_mrr', 'mrr_change', 'win_rate_pct', 'at_risk_pct']].tail(15).to_dict(orient='records')
        
        # 6. Build data section
        data_section = f"""
================================================================================
DATA (use this to generate the report)
================================================================================

TARGET: ${TARGET_MRR:,} end-of-cycle MRR

CURRENT PERFORMANCE (latest week):
- Current MRR: ${current_mrr:,.0f}
- Week-over-Week Change: ${wow_change:+,.0f} ({wow_pct:+.1f}%)
- Win Rate: {win_rate:.0f}%
- At-Risk: {at_risk_pct:.0f}% ({at_risk_deals} deals)

4-WEEK FORECAST (trend: ${avg_change:+,.0f}/week):
"""
        for p in predictions:
            data_section += f"- Week {p['week']}: ${p['mrr']:.0f}K\n"
        
        data_section += f"""
FEATURE IMPORTANCE (from XGBoost model):
"""
        for feat in top_features:
            data_section += f"- {feat.get('lever', 'Unknown')}: {feat.get('feature', '')} = {feat.get('importance_pct', 0):.1f}%\n"
        
        data_section += f"""
HISTORICAL TRAJECTORY (last 15 weeks):
"""
        for h in history:
            week_str = str(h['week'])[:10] if h['week'] else 'N/A'
            data_section += f"- {week_str}: ${h['total_mrr']:,.0f} (change: ${h.get('mrr_change', 0):+,.0f})\n"
        
        data_section += f"""
DEALS TO WIN ({len(deals_to_win)} deals):
"""
        for deal in deals_to_win:
            data_section += f"- {deal.get('company_name', 'Unknown')}: ${deal.get('mrr', 0):,.0f} | velocity: {deal.get('deal_velocity_days', 'N/A')} days | region: {deal.get('b2b_region', 'N/A')}\n"
        
        data_section += f"""
DEALS TO SAVE ({len(deals_to_save)} deals):
"""
        for deal in deals_to_save:
            data_section += f"- {deal.get('company_name', 'Unknown')}: ${deal.get('mrr', 0):,.0f} | velocity: {deal.get('deal_velocity_days', 'N/A')} days | region: {deal.get('b2b_region', 'N/A')}\n"
        
        # 7. Get the SCQA prompt and combine
        prompt_content = get_prompt_content("forecast_mrr")
        
        full_response = f"""
{prompt_content}

{data_section}

================================================================================
Now generate the SCQA-structured MRR forecast report using the data above.
================================================================================
"""
        
        return [TextContent(type="text", text=full_response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
