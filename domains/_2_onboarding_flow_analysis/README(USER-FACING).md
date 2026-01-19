# 2. Onboarding Flow Analysis

User onboarding funnel and drop-off analysis.

## Objective

Answer: **"How are users converting through the onboarding funnel by variant?"**

## Keywords

```
"onboarding flow"  → Start funnel analysis with query template
```

## Output

```
| variant | page_land | first_event | auth_login_attempt | auth_login_success |
|---------|-----------|-------------|--------------------|--------------------|
| Var0:D  | 1234      | 890         | 456                | 234                |
| Var0:M  | 2345      | 1200        | 678                | 345                |
...
```

## Quick Start

Use the query template in DEV-FACING README, customize:
- `page_path` → which game
- `first_event_ts` → cohort start time
- `variant mapping` → campaign attribution
