"""
Forecast MMR Domain - MCP Tools
================================
Actions AI can execute for MRR forecasting.
"""

import json
import pandas as pd
from typing import Any, List
from mcp.types import Tool, TextContent
from core.bq_client import get_client


def get_tools():
    """Return list of forecast tools."""
    return [
        Tool(
            name="forecast_mmr",
            description=(
                "Generate the weekly MRR forecast report. "
                "Auto-executes: queries BQ, runs forecast, returns formatted report."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="forecast_trend",
            description="Simple trend-based forecast using recent average change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "weeks": {
                        "type": "number",
                        "description": "Number of weeks to forecast (default: 4)",
                        "default": 4
                    }
                },
                "required": []
            }
        )
    ]


async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle forecast tool calls."""
    
    if name == "forecast_mmr":
        return await _forecast_mmr_report(arguments)
    elif name == "forecast_trend":
        return await _forecast_trend(arguments)
    else:
        raise ValueError(f"Unknown forecast tool: {name}")


async def _forecast_mmr_report(arguments: Any) -> List[TextContent]:
    """Generate the full weekly MRR forecast report."""
    try:
        client = get_client()
        PROJECT = "dev-im-platform"
        DATASET = "temp_fei_ai"
        
        # 1. Get current performance data
        model_sql = f"SELECT * FROM `{PROJECT}.{DATASET}.v_model_3_levers` ORDER BY week"
        df = client.query(model_sql).to_dataframe()
        df = df.sort_values('week').reset_index(drop=True)
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        current_mrr = float(latest['total_mrr'])
        wow_change = float(latest.get('mrr_change', 0))
        wow_pct = (wow_change / float(prev['total_mrr']) * 100) if prev['total_mrr'] else 0
        win_rate = float(latest.get('win_rate_pct', 0))
        at_risk_pct = float(latest.get('at_risk_pct', 0))
        pipeline_growth_pct = float(latest.get('pipeline_growth_pct', 0))
        
        # 2. Run forecast
        numeric_cols = df.select_dtypes(include=['float64', 'int64', 'Int64']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        recent_changes = df['mrr_change'].tail(4)
        avg_change = float(recent_changes.mean())
        
        last_week = df['week'].iloc[-1]
        predictions = []
        forecast_mrr = current_mrr
        
        for i in range(4):
            forecast_mrr = forecast_mrr + avg_change
            week_date = last_week + pd.Timedelta(weeks=i+1)
            predictions.append({"week": i + 1, "mrr": round(forecast_mrr / 1000, 0)})
        
        # 3. Get feature importance
        try:
            imp_sql = f"SELECT * FROM `{PROJECT}.{DATASET}.t_forecast_feature_importance` ORDER BY rank LIMIT 3"
            imp_df = client.query(imp_sql).to_dataframe()
            top_features = imp_df.to_dict(orient='records')
        except:
            top_features = [{"lever": "Deal Close", "importance_pct": 74}]
        
        # 4. Get top deals
        try:
            deals_sql = f"SELECT * FROM `{PROJECT}.{DATASET}.v_next_best_action` ORDER BY priority ASC"
            deals_df = client.query(deals_sql).to_dataframe()
            
            if 'action_type' in deals_df.columns:
                deals_to_win = deals_df[deals_df['action_type'] == 'WIN'].head(3).to_dict(orient='records')
                deals_to_save = deals_df[deals_df['action_type'] == 'SAVE'].head(3).to_dict(orient='records')
                win_total = deals_df[deals_df['action_type'] == 'WIN']['mrr'].sum()
                save_total = deals_df[deals_df['action_type'] == 'SAVE']['mrr'].sum()
            else:
                deals_to_win, deals_to_save = [], []
                win_total, save_total = 0, 0
        except:
            deals_to_win, deals_to_save = [], []
            win_total, save_total = 0, 0
        
        # 5. Format report
        at_risk_deals = int(latest.get('at_risk_deals', 0))
        pipeline_velocity = float(latest.get('pipeline_velocity', 0))
        
        report = f"""
📊 WEEKLY MRR REPORT
====================

1. CURRENT PERFORMANCE
   MRR: ${current_mrr/1000:.0f}K | WoW: ${wow_change/1000:+.1f}K ({wow_pct:+.1f}%)
   Win Rate: {win_rate:.0f}% | At-Risk: {at_risk_pct:.0f}% | Pipeline: {pipeline_growth_pct:+.0f}%

2. FORECAST
   Week 1: ${predictions[0]['mrr']:.0f}K  Week 2: ${predictions[1]['mrr']:.0f}K  Week 3: ${predictions[2]['mrr']:.0f}K  Week 4: ${predictions[3]['mrr']:.0f}K
   Trend: ${avg_change/1000:+.1f}K/week

3. DRIVERS"""
        
        for feat in top_features[:3]:
            report += f"\n   {feat.get('importance_pct', 0):.0f}% {feat.get('lever', 'Unknown')}"
        
        report += f"""

4. FOCUS AREAS
   #1 Fix Win Rate ({win_rate:.0f}% → 13%) → +${win_total/1000:.0f}K potential
   #2 Save At-Risk Deals ({at_risk_deals} deals) → ${save_total/1000:.0f}K at stake
   #3 Speed Up Velocity ({pipeline_velocity:.0f} → 158 days) → faster wins

5. TOP DEALS TO ACTION
   
   🎯 DEALS TO WIN"""
        
        for i, deal in enumerate(deals_to_win[:3], 1):
            report += f"\n   #{i} {deal.get('company_name', 'Unknown')[:25]:<25} ${deal.get('mrr', 0):,.0f}/mo   {deal.get('region', 'N/A')}"
        
        report += "\n   \n   🛡️ DEALS TO SAVE"
        
        for i, deal in enumerate(deals_to_save[:3], 1):
            report += f"\n   #{i} {deal.get('company_name', 'Unknown')[:25]:<25} ${deal.get('mrr', 0):,.0f}/mo   {deal.get('region', 'N/A')}"
        
        return [TextContent(type="text", text=report)]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Error generating report: {str(e)}")]


async def _forecast_trend(arguments: Any) -> List[TextContent]:
    """Simple trend-based forecast."""
    weeks = arguments.get("weeks", 4)
    
    try:
        client = get_client()
        sql = "SELECT * FROM `dev-im-platform.temp_fei_ai.v_model_3_levers` ORDER BY week"
        df = client.query(sql).to_dataframe()
        
        last_mrr = float(df['total_mrr'].iloc[-1])
        last_week = df['week'].iloc[-1]
        avg_change = float(df['mrr_change'].tail(4).mean())
        
        predictions = []
        forecast_mrr = last_mrr
        
        for i in range(weeks):
            forecast_mrr = forecast_mrr + avg_change
            week_date = last_week + pd.Timedelta(weeks=i+1)
            change_pct = ((forecast_mrr - last_mrr) / last_mrr) * 100
            predictions.append({
                "week": week_date.strftime('%Y-%m-%d'),
                "predicted_mrr": round(forecast_mrr, 0),
                "change_pct": round(change_pct, 1)
            })
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "model": "Trend",
                "baseline_mrr": round(last_mrr, 0),
                "weekly_trend": round(avg_change, 0),
                "predictions": predictions
            }, indent=2, default=str)
        )]
        
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]
