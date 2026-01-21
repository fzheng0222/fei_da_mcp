"""
DS-MRR Resources
=================
Read-only data AI can access.
"""

import json
from mcp.types import Resource
from bq_client import get_client

PROJECT = "dev-im-platform"
DATASET = "temp_fei_ai"


def get_resources():
    """Return list of all resources."""
    return [
        # BigQuery schema resources
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
        ),
        # Forecast resources
        Resource(
            uri="forecast://latest",
            name="Latest Forecast",
            mimeType="application/json",
            description="Most recent MRR forecast predictions (4-week)"
        ),
        Resource(
            uri="forecast://feature_importance",
            name="Feature Importance",
            mimeType="application/json",
            description="XGBoost feature importance - what drives MRR"
        )
    ]


async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    client = get_client()
    
    # Schema resources
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
    
    # Forecast resources
    elif uri == "forecast://latest":
        sql = f"SELECT * FROM `{PROJECT}.{DATASET}.t_forecast_predictions` ORDER BY forecast_week"
        df = client.query(sql).to_dataframe()
        return json.dumps({
            "source": f"{PROJECT}.{DATASET}.t_forecast_predictions",
            "predictions": df.to_dict(orient="records")
        }, indent=2, default=str)
    
    elif uri == "forecast://feature_importance":
        sql = f"SELECT * FROM `{PROJECT}.{DATASET}.t_forecast_feature_importance` ORDER BY rank"
        df = client.query(sql).to_dataframe()
        return json.dumps({
            "source": f"{PROJECT}.{DATASET}.t_forecast_feature_importance",
            "features": df.to_dict(orient="records")
        }, indent=2, default=str)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")
