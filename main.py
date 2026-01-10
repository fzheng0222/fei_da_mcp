#!/usr/bin/env python3
"""
DA-MCP: Data Analysis MCP Server
=================================
Connects Cursor AI to your CSV data for automated analysis

Your use case: Sales by region vs benchmark

DATA SOURCE: CSV files (simple and fast!)
"""

import asyncio
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

import pandas as pd
from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from mcp.server.stdio import stdio_server


# ============================================================================
# SECTION 1: CONFIGURATION
# ============================================================================
# This is where you set up your data source and email settings

# Path to your CSV data directory
DATA_DIR = os.getenv("DA_DATA_DIR", "./")

# CSV files to load (you can add more!)
CSV_FILES = ["sales_data.csv"]

# Email Configuration (for sending reports)
EMAIL_SENDER = os.getenv("DA_EMAIL_SENDER", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("DA_EMAIL_PASSWORD", "")  # Gmail App Password
EMAIL_RECIPIENT = os.getenv("DA_EMAIL_RECIPIENT", "your-email@gmail.com")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# ============================================================================
# SECTION 2: INITIALIZE MCP SERVER
# ============================================================================
# This creates the MCP server that Cursor will talk to

app = Server("da-mcp")

# Global variables to store our data
dataframes = {}  # Dictionary to store loaded CSV data
csv_info = {}    # Dictionary to store CSV metadata


# ============================================================================
# SECTION 3: LOAD CSV FILES
# ============================================================================

def load_csv_data():
    """
    Load CSV files into memory
    
    What this does:
    1. Finds CSV files in the data directory
    2. Loads them into pandas DataFrames
    3. Stores metadata (columns, row counts)
    
    Why pandas? It's like Excel for Python - great for data analysis!
    """
    global dataframes, csv_info
    
    data_path = Path(DATA_DIR)
    
    if not data_path.exists():
        print(f"⚠️  Data directory not found: {DATA_DIR}")
        return False
    
    loaded_count = 0
    
    for csv_file in CSV_FILES:
        csv_path = data_path / csv_file
        
        if not csv_path.exists():
            print(f"⚠️  CSV file not found: {csv_file}")
            continue
        
        try:
            # Load CSV into pandas DataFrame
            df = pd.read_csv(csv_path)
            
            # Store the DataFrame
            table_name = csv_file.replace('.csv', '')
            dataframes[table_name] = df
            
            # Store metadata
            csv_info[table_name] = {
                "file": csv_file,
                "columns": df.columns.tolist(),
                "row_count": len(df),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
            
            print(f"✅ Loaded: {csv_file} ({len(df)} rows, {len(df.columns)} columns)")
            loaded_count += 1
            
        except Exception as e:
            print(f"❌ Error loading {csv_file}: {e}")
    
    if loaded_count > 0:
        print(f"📊 Total tables loaded: {loaded_count}")
        return True
    else:
        print("❌ No CSV files loaded")
        return False


# ============================================================================
# SECTION 4: PROMPT TEMPLATES
# ============================================================================
# This is where we store AI prompts for analysis and reports

REPORT_ANALYSIS_PROMPT = """
You are analyzing sales data by region vs benchmark.

Based on the data provided, create a concise analysis with:

1. EXECUTIVE SUMMARY (2-3 sentences)
   - Overall performance status
   - Key highlight (best performing aspect)

2. PERFORMANCE BY REGION
   - List each region with:
     * Total sales
     * Benchmark target
     * Performance (Above/Below target by X%)
   - Present this as a clean table

3. KEY RECOMMENDATIONS (3-5 bullet points)
   - Specific actions for underperforming regions
   - Opportunities to leverage strong performers
   - Strategic insights

Keep it actionable and data-driven. Use percentages and concrete numbers.
"""


# ============================================================================
# SECTION 5: MCP RESOURCE - Show AI Your Data Structure
# ============================================================================
# This is the "menu" - it tells AI what data you have

@app.list_resources()
async def list_resources() -> List[Resource]:
    """
    Tell Cursor AI what resources are available
    Resource = Information about your data (schema/structure)
    """
    return [
        Resource(
            uri="schema://tables",
            name="CSV Tables Schema",
            mimeType="application/json",
            description="Shows all available CSV tables and their columns"
        )
    ]


@app.read_resource()
async def read_resource(uri: str) -> str:
    """
    When AI asks for a resource, provide the actual data
    
    For schema://tables, we return:
    - List of all CSV tables
    - Columns in each table
    - Row counts
    - Data types
    """
    if uri == "schema://tables":
        if not csv_info:
            return json.dumps({
                "error": "No CSV data loaded",
                "help": "Make sure CSV files exist in the data directory"
            })
        
        schema = {
            "data_source": "CSV files",
            "data_directory": DATA_DIR,
            "tables": csv_info
        }
        
        return json.dumps(schema, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


# ============================================================================
# SECTION 6: MCP TOOLS - Let AI Perform Actions
# ============================================================================
# This is the "action center" - it lets AI do things with your data

@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    Tell Cursor AI what tools (actions) are available
    
    We provide two tools:
    1. query_table - Read and analyze CSV data
    2. generate_report - Create and email weekly sales report
    """
    return [
        Tool(
            name="query_table",
            description=(
                "Query data from CSV tables using pandas. "
                "Can read tables, filter columns, and return data for analysis. "
                "Perfect for: sales by region, benchmarks, aggregations, summaries."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to query (e.g., 'sales_data')"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Maximum rows to return (default: 1000)",
                        "default": 1000
                    },
                    "columns": {
                        "type": "array",
                        "description": "Optional: Specific columns to return (e.g., ['region', 'sales', 'benchmark'])",
                        "items": {"type": "string"}
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="generate_report",
            description=(
                "Generate a weekly sales report with analysis. "
                "Returns: 1) Simple summary, 2) Visual table of regions vs benchmark, 3) Recommendations. "
                "Perfect for quick insights!"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to analyze (default: 'sales_data')",
                        "default": "sales_data"
                    },
                    "send_email": {
                        "type": "boolean",
                        "description": "Send email after generating report (default: false)",
                        "default": False
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """
    When AI uses a tool, this function handles it
    
    Supports two tools:
    1. query_table - Read and return data
    2. generate_report - Analyze data, create report, send email
    """
    if name == "query_table":
        table_name = arguments.get("table_name")
        limit = arguments.get("limit", 1000)
        columns = arguments.get("columns", None)
        
        # Validate inputs
        if not table_name:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "table_name is required"
                })
            )]
        
        if not dataframes:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": "No CSV data loaded"
                })
            )]
        
        if table_name not in dataframes:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Table '{table_name}' not found",
                    "available_tables": list(dataframes.keys())
                })
            )]
        
        try:
            # Get the DataFrame
            df = dataframes[table_name].copy()
            
            # Filter specific columns if requested
            if columns:
                available_cols = [col for col in columns if col in df.columns]
                if available_cols:
                    df = df[available_cols]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": False,
                            "error": "None of the requested columns exist",
                            "available_columns": dataframes[table_name].columns.tolist()
                        })
                    )]
            
            # Limit rows
            truncated = False
            if len(df) > limit:
                df = df.head(limit)
                truncated = True
            
            # Convert to JSON-friendly format
            result = {
                "success": True,
                "table_name": table_name,
                "rows": len(df),
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
                "truncated": truncated,
                "message": f"Returned {len(df)} rows" + (" (truncated)" if truncated else "")
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    elif name == "generate_report":
        # Generate sales report (simple output for testing)
        table_name = arguments.get("table_name", "sales_data")
        send_email = arguments.get("send_email", False)
        
        if table_name not in dataframes:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                })
            )]
        
        try:
            df = dataframes[table_name]
            
            # Analyze the data
            analysis = analyze_sales_data(df)
            
            # Format simple text output
            report_text = format_simple_report(analysis)
            
            # Optionally send email
            email_status = ""
            if send_email:
                html_report = generate_html_report(analysis)
                email_status = send_email_report(html_report)
            
            return [TextContent(
                type="text",
                text=report_text + (f"\n\n📧 {email_status}" if send_email else "")
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                })
            )]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


# ============================================================================
# HELPER FUNCTIONS FOR REPORT GENERATION
# ============================================================================

def analyze_sales_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze sales data and generate insights (SIMPLE VERSION)
    
    Returns:
    - summary: 2-3 sentences
    - regional_performance: Clean table
    - recommendations: 3-5 action items
    """
    # Group by region and sum sales/benchmark
    regional = df.groupby('region').agg({
        'sales': 'sum',
        'benchmark': 'sum'
    }).reset_index()
    
    # Calculate performance
    regional['performance_pct'] = ((regional['sales'] - regional['benchmark']) / regional['benchmark'] * 100).round(1)
    regional['status'] = regional['performance_pct'].apply(lambda x: '✅ Above' if x >= 0 else '⚠️ Below')
    
    # Sort by performance (best first)
    regional = regional.sort_values('performance_pct', ascending=False)
    
    # Overall metrics
    total_sales = regional['sales'].sum()
    total_benchmark = regional['benchmark'].sum()
    overall_pct = ((total_sales - total_benchmark) / total_benchmark * 100).round(1)
    
    # Best and worst
    best = regional.iloc[0]
    worst = regional.iloc[-1]
    
    # Simple 3-sentence summary
    summary = f"Overall sales are {'above' if overall_pct >= 0 else 'below'} target by {abs(overall_pct)}%. "
    summary += f"{best['region']} leads with +{best['performance_pct']}%. "
    summary += f"{worst['region']} needs attention at {worst['performance_pct']}%."
    
    # Top 3 recommendations
    recommendations = []
    
    if worst['performance_pct'] < -5:
        recommendations.append(f"🔴 Urgent: Focus on {worst['region']} - {abs(worst['performance_pct'])}% below target")
    elif worst['performance_pct'] < 0:
        recommendations.append(f"⚠️ Monitor: {worst['region']} slightly below target")
    
    if best['performance_pct'] > 10:
        recommendations.append(f"🟢 Replicate {best['region']}'s success (+{best['performance_pct']}%)")
    
    recommendations.append("📊 Review product mix in underperforming regions")
    
    return {
        "summary": summary,
        "regional_performance": regional.to_dict(orient='records'),
        "recommendations": recommendations,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def format_simple_report(analysis: Dict[str, Any]) -> str:
    """
    Format analysis as simple text (for Cursor display)
    Clean, visual, easy to read!
    """
    output = "📊 WEEKLY SALES REPORT\n"
    output += "=" * 60 + "\n\n"
    
    # 1. SUMMARY
    output += "📝 SUMMARY\n"
    output += f"{analysis['summary']}\n\n"
    
    # 2. VISUAL TABLE
    output += "📈 PERFORMANCE BY REGION\n"
    output += "-" * 60 + "\n"
    output += f"{'Region':<15} {'Sales':>12} {'Target':>12} {'Variance':>12} {'Status':>8}\n"
    output += "-" * 60 + "\n"
    
    for region in analysis['regional_performance']:
        output += f"{region['region']:<15} "
        output += f"${region['sales']:>11,.0f} "
        output += f"${region['benchmark']:>11,.0f} "
        output += f"{region['performance_pct']:>10.1f}% "
        output += f"{region['status']:>8}\n"
    
    output += "-" * 60 + "\n\n"
    
    # 3. RECOMMENDATIONS
    output += "💡 RECOMMENDATIONS\n"
    for i, rec in enumerate(analysis['recommendations'], 1):
        output += f"{i}. {rec}\n"
    
    output += "\n" + "=" * 60
    output += f"\nGenerated: {analysis['generated_at']}"
    
    return output


def generate_html_report(analysis: Dict[str, Any]) -> str:
    """Generate HTML formatted email report"""
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .recommendations {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; }}
            .recommendations li {{ margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Weekly Sales Report</h1>
        <p><strong>Generated:</strong> {analysis['generated_at']}</p>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <p>{analysis['summary']}</p>
        </div>
        
        <h2>Performance by Region</h2>
        <table>
            <tr>
                <th>Region</th>
                <th>Sales</th>
                <th>Benchmark</th>
                <th>Performance</th>
                <th>Status</th>
            </tr>
    """
    
    for region in analysis['regional_performance']:
        html += f"""
            <tr>
                <td><strong>{region['region']}</strong></td>
                <td>${region['sales']:,.0f}</td>
                <td>${region['benchmark']:,.0f}</td>
                <td>{region['performance_pct']:+.1f}%</td>
                <td>{region['status']}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <div class="recommendations">
            <h2>Key Recommendations</h2>
            <ul>
    """
    
    for rec in analysis['recommendations']:
        html += f"<li>{rec}</li>"
    
    html += """
            </ul>
        </div>
        
        <hr>
        <p><em>This report was automatically generated by DA-MCP</em></p>
    </body>
    </html>
    """
    
    return html


def send_email_report(html_content: str) -> str:
    """
    Send email report via Gmail SMTP
    
    Returns status message
    """
    # Check if email is configured
    if not EMAIL_PASSWORD or EMAIL_SENDER == "your-email@gmail.com":
        return "⚠️ Email not configured (see setup instructions)"
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"📊 Weekly Sales Report - {datetime.now().strftime('%Y-%m-%d')}"
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send via Gmail SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return f"✅ Email sent to {EMAIL_RECIPIENT}"
        
    except Exception as e:
        return f"❌ Email failed: {str(e)}"


# ============================================================================
# SECTION 7: START THE SERVER
# ============================================================================

async def main():
    """
    Main entry point - starts the MCP server
    This runs forever, waiting for Cursor to send requests
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    # Print startup info
    print("=" * 70)
    print("🚀 DA-MCP Server Starting...")
    print("=" * 70)
    print(f"📂 Data Directory: {DATA_DIR}")
    print(f"📊 CSV Files: {', '.join(CSV_FILES)}")
    print("=" * 70)
    
    # Load CSV data
    load_csv_data()
    
    print("=" * 70)
    print("✅ Server ready! Waiting for requests from Cursor...")
    print("💡 Tip: Ask Cursor 'What tables are available?'")
    print("(Press Ctrl+C to stop)")
    print("=" * 70)
    
    # Start the server
    asyncio.run(main())
