"""Farming Topic Insight - Tools (placeholder)"""
from typing import Any, List
from mcp.types import Tool, TextContent

def get_tools():
    return []

async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    raise ValueError(f"Not implemented: {name}")
