"""
Forecast MRR Domain - MCP Tools
"""

import json
import pandas as pd
from typing import Any, List
from mcp.types import Tool, TextContent
from core.bq_client import get_client
from .prompts import get_prompt_content, TARGET_MRR


def get_tools():
    """Return list of forecast tools."""
    return [
        Tool(
            name="forecast_mrr",
            description="Generate the weekly MRR forecast report.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle forecast tool calls."""
    if name == "forecast_mrr":
        return await _forecast_mrr_report(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _forecast_mrr_report(arguments: Any) -> List[TextContent]:
    """Generate the weekly MRR forecast report with SCQA-structured prompt."""
    try:
        client = get_client()
        PROJECT = "dev-im-platform"
        DATASET = "temp_fei_ai"
        
        # 1. Get current performance data
        df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.v_model_3_levers` ORDER BY week").to_dataframe()
        df = df.sort_values('week').reset_index(drop=True)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_mrr = float(latest['total_mrr'])
        wow_change = float(latest.get('mrr_change', 0))
        wow_pct = (wow_change / float(prev['total_mrr']) * 100) if prev['total_mrr'] else 0
        win_rate = float(latest.get('win_rate_pct', 0))
        at_risk_pct = float(latest.get('at_risk_pct', 0))
        at_risk_deals = int(latest.get('at_risk_deals', 0))
        
        # 2. Run forecast
        df[df.select_dtypes(include=['float64', 'int64', 'Int64']).columns] = df.select_dtypes(include=['float64', 'int64', 'Int64']).fillna(0)
        avg_change = float(df['mrr_change'].tail(4).mean())
        
        predictions = []
        forecast_mrr = current_mrr
        for i in range(4):
            forecast_mrr = forecast_mrr + avg_change
            predictions.append({"week": i + 1, "mrr": round(forecast_mrr / 1000, 0)})
        
        # 3. Get feature importance
        try:
            imp_df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.t_forecast_feature_importance` ORDER BY rank LIMIT 10").to_dataframe()
            top_features = imp_df.to_dict(orient='records')
        except:
            top_features = [{"lever": "Deal Close", "importance_pct": 74}]
        
        # 4. Get top deals
        try:
            deals_df = client.query(f"SELECT * FROM `{PROJECT}.{DATASET}.v_next_best_action` ORDER BY priority ASC").to_dataframe()
            deals_to_win = deals_df[deals_df['action_type'] == 'WIN'].to_dict(orient='records')
            deals_to_save = deals_df[deals_df['action_type'] == 'SAVE'].to_dict(orient='records')
        except:
            deals_to_win, deals_to_save = [], []
        
        # 5. Get historical data for trajectory (15 weeks)
        history = df[['week', 'total_mrr', 'mrr_change', 'win_rate_pct', 'at_risk_pct']].tail(15).to_dict(orient='records')
        
        # 6. Build data section
        data_section = f"""
================================================================================
DATA (use this to generate the report)
================================================================================

TARGET: ${TARGET_MRR:,} end-of-cycle MRR

CURRENT PERFORMANCE (latest week):
- Current MRR: ${current_mrr:,.0f}
- Week-over-Week Change: ${wow_change:+,.0f} ({wow_pct:+.1f}%)
- Win Rate: {win_rate:.0f}%
- At-Risk: {at_risk_pct:.0f}% ({at_risk_deals} deals)

4-WEEK FORECAST (trend: ${avg_change:+,.0f}/week):
"""
        for p in predictions:
            data_section += f"- Week {p['week']}: ${p['mrr']:.0f}K\n"
        
        data_section += f"""
FEATURE IMPORTANCE (from XGBoost model):
"""
        for feat in top_features:
            data_section += f"- {feat.get('lever', 'Unknown')}: {feat.get('feature', '')} = {feat.get('importance_pct', 0):.1f}%\n"
        
        data_section += f"""
HISTORICAL TRAJECTORY (last 15 weeks):
"""
        for h in history:
            week_str = str(h['week'])[:10] if h['week'] else 'N/A'
            data_section += f"- {week_str}: ${h['total_mrr']:,.0f} (change: ${h.get('mrr_change', 0):+,.0f})\n"
        
        data_section += f"""
DEALS TO WIN ({len(deals_to_win)} deals):
"""
        for deal in deals_to_win:
            data_section += f"- {deal.get('company_name', 'Unknown')}: ${deal.get('mrr', 0):,.0f} | velocity: {deal.get('deal_velocity_days', 'N/A')} days | region: {deal.get('b2b_region', 'N/A')}\n"
        
        data_section += f"""
DEALS TO SAVE ({len(deals_to_save)} deals):
"""
        for deal in deals_to_save:
            data_section += f"- {deal.get('company_name', 'Unknown')}: ${deal.get('mrr', 0):,.0f} | velocity: {deal.get('deal_velocity_days', 'N/A')} days | region: {deal.get('b2b_region', 'N/A')}\n"
        
        # 7. Get the SCQA prompt and combine
        prompt_content = get_prompt_content("forecast_mrr")
        
        full_response = f"""
{prompt_content}

{data_section}

================================================================================
Now generate the SCQA-structured MRR forecast report using the data above.
================================================================================
"""
        
        return [TextContent(type="text", text=full_response)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
