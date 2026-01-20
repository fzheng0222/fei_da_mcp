#!/usr/bin/env python3
"""
DA-MCP: Data Analysis MCP Server
=================================
Modular MCP server with domain-based organization.

Domains:
  0_general_analysis - Daily data exploration (most used)
  1_forecast_mrr     - Weekly MRR forecasting

DATA SOURCE: BigQuery
"""

import asyncio
from typing import Any, List
import warnings
warnings.filterwarnings('ignore')

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, Prompt, GetPromptResult, PromptMessage

# Core
from core.bq_client import get_client

# Domains
from domains._0_general_analysis import resources as analysis_resources
from domains._0_general_analysis import tools as analysis_tools
from domains._0_general_analysis import prompts as analysis_prompts

from domains._1_forecast_mrr import resources as forecast_resources
from domains._1_forecast_mrr import tools as forecast_tools
from domains._1_forecast_mrr import prompts as forecast_prompts


# ============================================================================
# INITIALIZE MCP SERVER
# ============================================================================

app = Server("da-mcp")


# ============================================================================
# MCP RESOURCES
# ============================================================================

@app.list_resources()
async def list_resources() -> List[Resource]:
    """List all available resources."""
    resources = []
    resources.extend(analysis_resources.get_resources())
    resources.extend(forecast_resources.get_resources())
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri.startswith("schema://"):
        return await analysis_resources.read_resource(uri)
    if uri.startswith("forecast://"):
        return await forecast_resources.read_resource(uri)
    raise ValueError(f"Unknown resource: {uri}")


# ============================================================================
# MCP TOOLS
# ============================================================================

# Tool to domain mapping
TOOL_DOMAINS = {
    # 0_general_analysis
    "list_tables": "analysis", "describe_table": "analysis",
    "sample_table": "analysis", "query_bigquery": "analysis",
    # 1_forecast_mrr
    "forecast_mrr": "forecast",
}


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools."""
    tools = []
    tools.extend(analysis_tools.get_tools())
    tools.extend(forecast_tools.get_tools())
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    domain = TOOL_DOMAINS.get(name)
    
    if domain == "analysis":
        return await analysis_tools.call_tool(name, arguments)
    elif domain == "forecast":
        return await forecast_tools.call_tool(name, arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# MCP PROMPTS
# ============================================================================

@app.list_prompts()
async def list_prompts() -> List[Prompt]:
    """List all available prompts."""
    prompts = []
    prompts.extend(analysis_prompts.get_prompts())
    prompts.extend(forecast_prompts.get_prompts())
    return prompts


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Get a prompt by name."""
    for module in [analysis_prompts, forecast_prompts]:
        try:
            content = module.get_prompt_content(name)
            return GetPromptResult(
                description=name,
                messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))]
            )
        except ValueError:
            continue
    raise ValueError(f"Unknown prompt: {name}")


# ============================================================================
# START THE SERVER
# ============================================================================

async def main():
    """Main entry point."""
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    print("=" * 60)
    print("DA-MCP Server")
    print("=" * 60)
    print("Domains:")
    print("  0_general_analysis - list_tables, describe_table, sample_table, query_bigquery")
    print("  1_forecast_mrr     - forecast_mrr")
    print("=" * 60)
    asyncio.run(main())
