#!/usr/bin/env python3
"""
MRR Forecast Script (3-Lever Model)
====================================
1. XGBoost: Learn which levers predict MRR changes
2. Simple Forecast: Predict next 1-4 weeks (trend-based)

3 LEVERS:
  1. Pipeline Growth   → pipeline_growth, pipeline_growth_pct
  2. At Risk Reduction → at_risk_change, at_risk_pct  
  3. Deal Close Rate   → new_wins, velocity_change, win_rate_pct

BQ Objects:
  - INPUT:  dev-im-platform.temp_fei_ai.v_model_3_levers
  - OUTPUT: dev-im-platform.temp_fei_ai.t_forecast_feature_importance
  - OUTPUT: dev-im-platform.temp_fei_ai.t_forecast_predictions
"""

import pandas as pd
from datetime import datetime
from google.cloud import bigquery

try:
    import xgboost as xgb
    from sklearn.model_selection import cross_val_score
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'xgboost', 'scikit-learn', '-q'])
    import xgboost as xgb
    from sklearn.model_selection import cross_val_score

# Config
PROJECT = "dev-im-platform"
DATASET = "temp_fei_ai"
INPUT_VIEW = f"{PROJECT}.{DATASET}.v_model_3_levers"
OUTPUT_IMPORTANCE = f"{PROJECT}.{DATASET}.t_forecast_feature_importance"
OUTPUT_PREDICTIONS = f"{PROJECT}.{DATASET}.t_forecast_predictions"

def main():
    print("=" * 60)
    print("MRR FORECAST (3-Lever Model)")
    print("=" * 60)
    
    # 1. Load data
    print("\n📥 Loading data from BQ...")
    client = bigquery.Client()
    df = client.query(f"SELECT * FROM `{INPUT_VIEW}`").to_dataframe()
    df = df.sort_values('week').reset_index(drop=True)
    
    # Fill NaN in numeric columns only
    numeric_cols = df.select_dtypes(include=['float64', 'int64', 'Int64']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Drop first row (no lag data)
    df = df.dropna(subset=['mrr_lag1'])
    print(f"   Loaded {len(df)} weeks of data")
    
    # 2. Define 3-lever features
    feature_cols = [
        # Lever 1: Pipeline Growth
        'pipeline_growth', 'pipeline_growth_pct',
        # Lever 2: At Risk Reduction  
        'at_risk_change', 'at_risk_pct',
        # Lever 3: Deal Close Rate
        'new_wins', 'velocity_change', 'win_rate_pct',
        # Trend
        'mrr_lag1'
    ]
    
    X = df[feature_cols]
    y = df['total_mrr']
    
    # 3. Train XGBoost (for feature importance)
    print("\n🤖 Learning which levers matter (XGBoost)...")
    model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    model.fit(X, y)
    
    # 4. Feature Importance
    importance = dict(zip(feature_cols, model.feature_importances_))
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    importance_df = pd.DataFrame([
        {
            'run_date': datetime.now(),
            'feature': feat,
            'importance': float(imp),
            'importance_pct': round(float(imp) * 100, 1),
            'rank': i + 1,
            'lever': 'Pipeline Growth' if feat in ['pipeline_growth', 'pipeline_growth_pct'] 
                     else 'At Risk' if feat in ['at_risk_change', 'at_risk_pct']
                     else 'Deal Close' if feat in ['new_wins', 'velocity_change', 'win_rate_pct']
                     else 'Trend'
        }
        for i, (feat, imp) in enumerate(importance_sorted)
    ])
    
    print("\n📊 Feature Importance (3 Levers):")
    print("-" * 50)
    for _, row in importance_df.iterrows():
        bar = "█" * int(row['importance'] * 40)
        print(f"   {row['rank']:2d}. [{row['lever']:15s}] {row['feature']:20s} {row['importance_pct']:5.1f}%  {bar}")
    
    # 5. Simple Forecast (trend-based)
    print("\n📈 Forecasting next 4 weeks (simple trend)...")
    
    last_mrr = float(df['total_mrr'].iloc[-1])
    last_week = df['week'].iloc[-1]
    
    # Calculate recent trend (last 4 weeks average change)
    recent_changes = df['mrr_change'].tail(4)
    avg_change = float(recent_changes.mean())
    
    predictions = []
    forecast_mrr = last_mrr
    
    for i in range(4):
        forecast_mrr = forecast_mrr + avg_change
        week_date = last_week + pd.Timedelta(weeks=i+1)
        change_pct = ((forecast_mrr - last_mrr) / last_mrr) * 100
        
        predictions.append({
            'run_date': datetime.now(),
            'forecast_week': week_date,
            'weeks_ahead': i + 1,
            'predicted_mrr': round(forecast_mrr, 0),
            'baseline_mrr': round(last_mrr, 0),
            'weekly_trend': round(avg_change, 0),
            'change_pct': round(change_pct, 1)
        })
        
        print(f"   Week {i+1} ({week_date.strftime('%Y-%m-%d')}): ${forecast_mrr:>10,.0f}  ({change_pct:+.1f}%)")
    
    predictions_df = pd.DataFrame(predictions)
    
    # 6. Save to BQ
    print("\n💾 Saving to BigQuery...")
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    
    client.load_table_from_dataframe(importance_df, OUTPUT_IMPORTANCE, job_config=job_config).result()
    print(f"   ✓ {OUTPUT_IMPORTANCE}")
    
    client.load_table_from_dataframe(predictions_df, OUTPUT_PREDICTIONS, job_config=job_config).result()
    print(f"   ✓ {OUTPUT_PREDICTIONS}")
    
    # 7. Summary
    print("\n" + "=" * 60)
    top_lever = importance_df.iloc[0]
    print(f"TOP PREDICTOR: {top_lever['feature']} ({top_lever['lever']}) - {top_lever['importance_pct']}%")
    print(f"TREND: ${avg_change:+,.0f}/week")
    print(f"FORECAST (4 weeks): ${predictions[-1]['predicted_mrr']:,.0f} ({predictions[-1]['change_pct']:+.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    main()
