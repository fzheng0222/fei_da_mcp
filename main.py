#!/usr/bin/env python3
"""
DS-MRR: Data Science MRR Forecast Server
=========================================
MRR forecasting and BigQuery exploration via MCP.

DATA SOURCE: BigQuery
"""

import asyncio
from typing import Any, List
import warnings
warnings.filterwarnings('ignore')

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, Prompt, GetPromptResult, PromptMessage

import tools
import resources
import prompts


# =============================================================================
# INITIALIZE MCP SERVER
# =============================================================================

app = Server("ds-mrr")


# =============================================================================
# MCP RESOURCES
# =============================================================================

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List all available resources."""
    return resources.get_resources()


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    return await resources.read_resource(uri)


# =============================================================================
# MCP TOOLS
# =============================================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools."""
    return tools.get_tools()


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    return await tools.call_tool(name, arguments)


# =============================================================================
# MCP PROMPTS
# =============================================================================

@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List all available prompts."""
    return prompts.get_prompts()


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Get a prompt by name."""
    content = prompts.get_prompt_content(name)
    return GetPromptResult(
        description=name,
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))]
    )


# =============================================================================
# START THE SERVER
# =============================================================================

async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    print("=" * 60)
    print("DS-MRR Server")
    print("=" * 60)
    print("Tools: list_tables, describe_table, sample_table, query_bigquery, forecast_mrr")
    print("=" * 60)
    asyncio.run(main())
