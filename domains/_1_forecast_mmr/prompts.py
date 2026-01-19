"""
Forecast MMR Domain - MCP Prompts
==================================
Keyword triggers for forecast tasks.
"""

from mcp.types import Prompt

PROMPTS = {
    "forecast_mmr": {
        "name": "forecast_mmr",
        "description": "Weekly MRR forecast report - full analysis",
        "prompt": """Run my MRR forecast and generate the weekly report with:
1. Current performance (MRR, WoW change, key metrics)
2. 4-week forecast with trend
3. What's driving the trend (feature importance)
4. What to focus on (prioritized actions)
5. Top deals to action"""
    },
    "forecast_drivers": {
        "name": "forecast_drivers",
        "description": "Deep dive on what's driving MRR changes",
        "prompt": """What's causing our MRR trend? Show:
1. Feature importance breakdown
2. Which levers matter most (Deal Close, At Risk, Pipeline)
3. Recommendations based on drivers"""
    },
    "forecast_actions": {
        "name": "forecast_actions",
        "description": "Prioritized action items",
        "prompt": """Based on current MRR data, what should we focus on?
- Top deals to WIN
- Top deals to SAVE
- Key metric to improve"""
    }
}


def get_prompts():
    """Return list of MCP Prompt objects."""
    return [Prompt(name=c["name"], description=c["description"], arguments=[]) for c in PROMPTS.values()]


def get_prompt_content(name: str) -> str:
    """Get the full prompt text for a given prompt name."""
    if name in PROMPTS:
        return PROMPTS[name]["prompt"]
    raise ValueError(f"Unknown prompt: {name}")
