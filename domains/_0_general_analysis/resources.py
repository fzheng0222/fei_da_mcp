"""
General Analysis Domain - MCP Resources
========================================
Read-only data about available datasets and schemas.
"""

import json
from mcp.types import Resource
from core.bq_client import get_client


def get_resources():
    """Return list of analysis resources."""
    return [
        Resource(
            uri="schema://bigquery",
            name="BigQuery Schema",
            mimeType="application/json",
            description="Information about available BigQuery tables and datasets"
        ),
        Resource(
            uri="schema://datasets",
            name="Available Datasets",
            mimeType="application/json",
            description="List of commonly used datasets"
        )
    ]


async def read_resource(uri: str) -> str:
    """Read an analysis resource by URI."""
    
    if uri == "schema://bigquery":
        return json.dumps({
            "data_source": "BigQuery",
            "commonly_used": [
                "prod-im-data.mod_imx.hubspot_b2b_deal",
                "prod-im-data.mod_imx.hubspot_b2b_company",
                "dev-im-platform.temp_fei_ai.v_model_3_levers",
                "dev-im-platform.temp_fei_ai.v_next_best_action"
            ],
            "hint": "Use list_tables, describe_table, sample_table, or query_bigquery tools"
        }, indent=2)
    
    elif uri == "schema://datasets":
        return json.dumps({
            "datasets": [
                {"id": "prod-im-data.mod_imx", "description": "Production Hubspot and IMX data"},
                {"id": "dev-im-platform.temp_fei_ai", "description": "Analysis views and temp tables"}
            ]
        }, indent=2)
    
    else:
        raise ValueError(f"Unknown analysis resource: {uri}")
