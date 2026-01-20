# Forecast MMR - DS Pipeline

## Objective

Predict weekly MRR and identify which levers drive it.

**Question:** "What's our MRR outlook and what should we focus on?"

---

## Pipeline

```
                            🤖 AI-ASSISTED PIPELINE
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 1. GET   │ → │ 2. CLEAN │ → │ 3. FEAT  │ → │ 4. MODEL │ → │ 5. EVAL  │ → │ 6. SCQA  │
│   DATA   │   │   DATA   │   │   SELECT │   │ FORECAST │   │ PERFORM  │   │  REPORT  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                                          Consultant-style
                                                                             output
```

---

## Step 1: Get Data (Raw)

**Source:** `dev-im-platform.temp_fei_ai.v_cleaned_deals`

Deal-level data with cleaning applied:

```sql
SELECT * FROM `dev-im-platform.temp_fei_ai.v_cleaned_deals`
```

**Raw Deal Features:**
| Column | Type | Description |
|--------|------|-------------|
| `deal_id` | STRING | Unique deal identifier |
| `company_name` | STRING | Account name |
| `mrr` | FLOAT | Monthly recurring revenue |
| `stage` | STRING | Deal stage |
| `close_date` | DATE | Expected close date |
| `created_date` | DATE | Deal created |
| `region` | STRING | Sales region |
| `is_at_risk` | BOOL | At-risk flag |
| `days_in_pipeline` | INT | Days since created |

---

## Step 2: Clean & Feature Generation

**Output:** `dev-im-platform.temp_fei_ai.v_model_3_levers`

Aggregate deal-level → weekly timeseries with engineered features:

```sql
SELECT * FROM `dev-im-platform.temp_fei_ai.v_model_3_levers` ORDER BY week
```

**Generated Features (PK: week):**
| Column | Type | Description |
|--------|------|-------------|
| `week` | DATE | Week ending (PK) |
| `total_mrr` | FLOAT | Target variable |
| `pipeline_deals` | INT | Active deals in pipeline |
| `pipeline_growth` | INT | New deals added (WoW) |
| `pipeline_growth_pct` | FLOAT | % pipeline change |
| `at_risk_deals` | INT | Deals flagged at-risk |
| `at_risk_change` | INT | Change in at-risk (WoW) |
| `at_risk_pct` | FLOAT | % of pipeline at risk |
| `new_wins` | INT | Deals closed won |
| `win_rate_pct` | FLOAT | Close rate |
| `pipeline_velocity` | FLOAT | Avg days to close |
| `velocity_change` | FLOAT | Change in velocity (WoW) |
| `mrr_lag1` | FLOAT | Previous week MRR |
| `mrr_change` | FLOAT | WoW MRR change |

**Transformations:**
- Deal-level → Weekly aggregation
- Lag features (`mrr_lag1`)
- WoW change features (`*_change`)
- Percentage features (`*_pct`)

```python
# Additional cleaning in Python
numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
df[numeric_cols] = df[numeric_cols].fillna(0)
df = df.dropna(subset=['mrr_lag1'])  # Drop first week (no lag)
```

**Result:** ~14 weeks of training data

---

## Step 3: Feature Selection (3-Lever Model)

Reduce raw features into 3 controllable business levers:

| Lever | Features | Business Meaning |
|-------|----------|------------------|
| **Pipeline Growth** | `pipeline_growth`, `pipeline_growth_pct` | Are we adding new opportunities? |
| **At Risk** | `at_risk_change`, `at_risk_pct` | Are we losing existing deals? |
| **Deal Close** | `new_wins`, `velocity_change`, `win_rate_pct` | Are we converting pipeline? |
| **Trend** | `mrr_lag1` | Momentum from last week |

```python
feature_cols = [
    'pipeline_growth', 'pipeline_growth_pct',  # Lever 1
    'at_risk_change', 'at_risk_pct',            # Lever 2
    'new_wins', 'velocity_change', 'win_rate_pct',  # Lever 3
    'mrr_lag1'                                  # Trend
]
X = df[feature_cols]
y = df['total_mrr']
```

---

## Step 4: Model & Forecast

### 4a. XGBoost (Feature Importance)

Learn which levers actually predict MRR:

```python
model = xgb.XGBRegressor(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.1,
    random_state=42
)
model.fit(X, y)
importance = dict(zip(feature_cols, model.feature_importances_))
```

### 4b. Trend Forecast (Simple)

Project next 4 weeks using rolling average:

```python
avg_change = df['mrr_change'].tail(4).mean()  # Last 4 weeks trend

for i in range(4):
    forecast_mrr = forecast_mrr + avg_change
```

**Why simple trend?** 
- Small dataset (~14 weeks) → complex models overfit
- Business wants directional guidance, not precision
- Easy to explain and debug

---

## Step 5: Evaluate Performance

### Feature Importance Results

| Lever | Features | Importance | Interpretation |
|-------|----------|------------|----------------|
| **Deal Close** | new_wins, velocity, win_rate | **74%** | Closing drives MRR |
| **At Risk** | at_risk_change, at_risk_pct | **14%** | Retention secondary |
| **Pipeline** | pipeline_growth, growth_pct | **12%** | Prospecting barely matters |

**Key Insight:** 74% Deal Close means we have enough pipeline — the problem is conversion, not prospecting. Focus on closing and saving, not adding more top-of-funnel.

### Model Limitations

- No confidence intervals (yet)
- Assumes trend continues linearly
- No seasonality adjustment
- Small training window

---

## Step 6: SCQA Report (Consultant-Style Output)

### Save to BQ

| Table | Purpose |
|-------|---------|
| `t_forecast_feature_importance` | XGBoost weights by feature |
| `t_forecast_predictions` | 4-week forecast |

### Generate Report (SCQA Structure)

```
📊 WEEKLY MRR FORECAST REPORT
=============================
1. SITUATION     → MRR, target progress, confidence + trajectory graph
2. COMPLICATION  → What's blocking us (connects situation to analysis)
3. ANALYSIS      → Feature importance (what levers drive MRR)
4. ACTIONS       → Urgent (close/save), Nurture, Metric to fix
```

**Report Flow:**
- SITUATION: Where we are (MRR + trajectory visual)
- COMPLICATION: The problem in one sentence
- ANALYSIS: Feature importance explains WHY (74% Deal Close = focus on closing, not prospecting)
- ACTIONS: Prioritized by urgency (closeable vs at-risk vs nurture)

---

## Data Layer

**Dataset:** `dev-im-platform.temp_fei_ai`

| Object | Type | Stage | Purpose |
|--------|------|-------|---------|
| `v_cleaned_deals` | View | Raw | Deal-level cleaned data |
| `v_model_3_levers` | View | Features | Weekly timeseries (PK: week) |
| `v_next_best_action` | View | Input | Prioritized deal list |
| `t_forecast_feature_importance` | Table | Output | Feature weights |
| `t_forecast_predictions` | Table | Output | 4-week forecast |

```
v_cleaned_deals → v_model_3_levers → Model → t_forecast_*
    (raw)           (features)              (output)
```

---

## Run

```bash
# Full pipeline (XGBoost + Forecast + Save)
python -m domains._1_forecast_mmr.run

# Via MCP (report only)
"forecast mmr"
```

---

## TODO

**Model Improvements:**
- [ ] Add seasonality (month-end spikes)
- [ ] Add competitor score

**Output & Delivery:**
- [ ] Beautify insights (charts, 1-pagers, visual summaries)
- [ ] Slack integration (weekly auto-post)

**New:**
- [ ] Identify deals that are likely to be closed as NBA