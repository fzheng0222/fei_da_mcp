#!/usr/bin/env python3
"""
DA-MCP: Data Analysis MCP Server
=================================
Modular MCP server with domain-based organization.

Domains:
  0_general_analysis        - Daily data exploration (most used)
  1_forecast_mmr            - Weekly MRR forecasting
  2_onboarding_flow_analysis - User onboarding funnel analysis
  3_farming_topic_insight   - Farming/airdrop behavior (placeholder)
  4_user_segmentation       - User grouping (placeholder)
  5_sybil                   - Fraud detection (placeholder)

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

# Domains (0, 1, 2 are populated; 3, 4, 5 are placeholders)
from domains._0_general_analysis import resources as analysis_resources
from domains._0_general_analysis import tools as analysis_tools
from domains._0_general_analysis import prompts as analysis_prompts

from domains._1_forecast_mmr import resources as forecast_resources
from domains._1_forecast_mmr import tools as forecast_tools
from domains._1_forecast_mmr import prompts as forecast_prompts

from domains._2_onboarding_flow_analysis import resources as onboarding_resources
from domains._2_onboarding_flow_analysis import tools as onboarding_tools
from domains._2_onboarding_flow_analysis import prompts as onboarding_prompts

from domains._3_farming_topic_insight import resources as farming_resources
from domains._3_farming_topic_insight import tools as farming_tools
from domains._3_farming_topic_insight import prompts as farming_prompts

from domains._4_user_segmentation import resources as segment_resources
from domains._4_user_segmentation import tools as segment_tools
from domains._4_user_segmentation import prompts as segment_prompts

from domains._5_sybil import resources as sybil_resources
from domains._5_sybil import tools as sybil_tools
from domains._5_sybil import prompts as sybil_prompts


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
    resources.extend(onboarding_resources.get_resources())
    resources.extend(farming_resources.get_resources())
    resources.extend(segment_resources.get_resources())
    resources.extend(sybil_resources.get_resources())
    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri.startswith("schema://"):
        return await analysis_resources.read_resource(uri)
    if uri.startswith("forecast://"):
        return await forecast_resources.read_resource(uri)
    if uri.startswith("onboarding://"):
        return await onboarding_resources.read_resource(uri)
    raise ValueError(f"Unknown resource: {uri}")


# ============================================================================
# MCP TOOLS
# ============================================================================

# Tool to domain mapping
TOOL_DOMAINS = {
    # 0_general_analysis
    "list_tables": "analysis", "describe_table": "analysis",
    "sample_table": "analysis", "query_bigquery": "analysis", "profile_table": "analysis",
    # 1_forecast_mmr
    "forecast_mmr": "forecast", "forecast_trend": "forecast",
    # 2_onboarding_flow_analysis
    "onboarding_funnel": "onboarding", "onboarding_dropoff": "onboarding",
    "onboarding_cohort": "onboarding", "onboarding_report": "onboarding",
}


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools."""
    tools = []
    tools.extend(analysis_tools.get_tools())
    tools.extend(forecast_tools.get_tools())
    tools.extend(onboarding_tools.get_tools())
    tools.extend(farming_tools.get_tools())
    tools.extend(segment_tools.get_tools())
    tools.extend(sybil_tools.get_tools())
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    domain = TOOL_DOMAINS.get(name)
    
    if domain == "analysis":
        return await analysis_tools.call_tool(name, arguments)
    elif domain == "forecast":
        return await forecast_tools.call_tool(name, arguments)
    elif domain == "onboarding":
        return await onboarding_tools.call_tool(name, arguments)
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
    prompts.extend(onboarding_prompts.get_prompts())
    prompts.extend(farming_prompts.get_prompts())
    prompts.extend(segment_prompts.get_prompts())
    prompts.extend(sybil_prompts.get_prompts())
    return prompts


@app.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Get a prompt by name."""
    for module in [analysis_prompts, forecast_prompts, onboarding_prompts]:
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
    print("  0_general_analysis  - list_tables, describe_table, sample_table, query_bigquery, profile_table")
    print("  1_forecast_mmr      - forecast_mmr, forecast_trend")
    print("  2_onboarding_flow   - onboarding_funnel, onboarding_dropoff, onboarding_cohort, onboarding_report")
    print("  3_farming_insight   - (placeholder)")
    print("  4_user_segmentation - (placeholder)")
    print("  5_sybil             - (placeholder)")
    print("=" * 60)
    asyncio.run(main())
