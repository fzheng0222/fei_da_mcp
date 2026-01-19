"""
General Analysis Domain - MCP Prompts
======================================
Keyword triggers for common analysis tasks.
"""

from mcp.types import Prompt

PROMPTS = {
    "explore": {
        "name": "explore",
        "description": "Explore a dataset - list tables and show key schemas",
        "prompt": """Explore the dataset and tell me:
1. What tables are available
2. Key tables and their schemas
3. Relationships between tables (if visible)
4. Suggested queries to start with"""
    },
    "profile": {
        "name": "profile",
        "description": "Profile a table - data quality summary",
        "prompt": """Profile this table and tell me:
1. Row count and column count
2. Data types for each column
3. Null percentages
4. Unique value counts
5. Any data quality issues spotted"""
    },
    "quick_stats": {
        "name": "quick_stats",
        "description": "Quick statistics on a table or query result",
        "prompt": """Give me quick stats:
1. Total rows
2. Key aggregations (sum, avg, min, max for numeric columns)
3. Date range (if date columns exist)
4. Top categories (if categorical columns exist)"""
    }
}


def get_prompts():
    """Return list of MCP Prompt objects."""
    prompts = []
    for key, config in PROMPTS.items():
        prompts.append(
            Prompt(
                name=config["name"],
                description=config["description"],
                arguments=[]
            )
        )
    return prompts


def get_prompt_content(name: str) -> str:
    """Get the full prompt text for a given prompt name."""
    if name in PROMPTS:
        return PROMPTS[name]["prompt"]
    raise ValueError(f"Unknown prompt: {name}")
