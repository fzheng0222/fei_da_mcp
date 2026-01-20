"""
Forecast MRR Domain - MCP Resources
====================================
Read-only data AI can access about forecasts.
"""

import json
from mcp.types import Resource
from core.bq_client import get_client

PROJECT = "dev-im-platform"
DATASET = "temp_fei_ai"


def get_resources():
    """Return list of forecast resources."""
    return [
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
    """Read a forecast resource by URI."""
    client = get_client()
    
    if uri == "forecast://latest":
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
        raise ValueError(f"Unknown forecast resource: {uri}")
