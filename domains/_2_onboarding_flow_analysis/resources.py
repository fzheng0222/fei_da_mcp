"""
Onboarding Flow Analysis Domain - MCP Resources
================================================
Read-only data about onboarding funnels and user flows.
"""

import json
from mcp.types import Resource
from core.bq_client import get_client


def get_resources():
    """Return list of onboarding resources."""
    return [
        Resource(
            uri="onboarding://funnel",
            name="Onboarding Funnel",
            mimeType="application/json",
            description="Current onboarding funnel metrics and conversion rates"
        ),
        Resource(
            uri="onboarding://dropoff",
            name="Drop-off Analysis",
            mimeType="application/json",
            description="Where users drop off in the onboarding flow"
        )
    ]


async def read_resource(uri: str) -> str:
    """Read an onboarding resource by URI."""
    # TODO: Implement when BQ views are ready
    if uri == "onboarding://funnel":
        return json.dumps({
            "status": "placeholder",
            "message": "Create BQ view for onboarding funnel data",
            "expected_columns": ["step", "users", "conversion_rate", "drop_off_rate"]
        }, indent=2)
    
    elif uri == "onboarding://dropoff":
        return json.dumps({
            "status": "placeholder",
            "message": "Create BQ view for drop-off analysis",
            "expected_columns": ["step", "drop_off_count", "drop_off_pct", "common_reasons"]
        }, indent=2)
    
    else:
        raise ValueError(f"Unknown onboarding resource: {uri}")
