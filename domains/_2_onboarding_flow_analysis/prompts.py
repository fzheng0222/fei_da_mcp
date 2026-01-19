"""
Onboarding Flow Analysis Domain - MCP Prompts
==============================================
Keyword triggers for onboarding analysis tasks.
"""

from mcp.types import Prompt

PROMPTS = {
    "onboarding_report": {
        "name": "onboarding_report",
        "description": "Full onboarding flow analysis report",
        "prompt": """Analyze our onboarding flow and tell me:
1. Current funnel metrics (conversion at each step)
2. Biggest drop-off points
3. Trends vs previous period
4. Recommendations to improve conversion"""
    },
    "onboarding_dropoff": {
        "name": "onboarding_dropoff",
        "description": "Where users drop off in onboarding",
        "prompt": """Where are users dropping off in onboarding?
1. Which steps have the worst conversion
2. How many users we're losing at each step
3. Potential reasons for drop-off
4. Quick wins to improve"""
    },
    "onboarding_compare": {
        "name": "onboarding_compare",
        "description": "Compare onboarding across cohorts",
        "prompt": """Compare onboarding performance:
1. This month vs last month
2. Conversion rate changes
3. Time to activate changes
4. What's working better/worse"""
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
