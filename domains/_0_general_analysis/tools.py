"""
General Analysis Domain - MCP Tools
=====================================
Generic data exploration tools for day-to-day analysis.
"""

import json
import pandas as pd
from typing import Any, List
from mcp.types import Tool, TextContent
from core.bq_client import get_client


def get_tools():
    """Return list of analysis tools."""
    return [
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
        )
    ]


async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle analysis tool calls."""
    client = get_client()
    
    if name == "list_tables":
        return await _list_tables(client, arguments)
    elif name == "describe_table":
        return await _describe_table(client, arguments)
    elif name == "sample_table":
        return await _sample_table(client, arguments)
    elif name == "query_bigquery":
        return await _query_bigquery(client, arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


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
