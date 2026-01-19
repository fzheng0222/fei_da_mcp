# Onboarding Flow Analysis - DS Pipeline

## Objective

Analyze user onboarding funnel by campaign variant:
1. How many users land on the game page?
2. How many start onboarding?
3. How many attempt login?
4. How many succeed?

---

## Pipeline

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ 1. GET   │ → │ 2. FILTER│ → │ 3. MAP   │ → │ 4. AGG   │
│  EVENTS  │   │  & JOIN  │   │ VARIANTS │   │  FUNNEL  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

---

## Query Template

```sql
WITH 
  -- 1. Centralized Visitor Logic
  visitors AS (
    SELECT * FROM `prod-im-data.app_immutable_play.visitor` 
    WHERE is_front_end_cohort OR FALSE
  ),

  -- 2. Base Event Data with Initial Filtering
  base_events AS (
    SELECT 
      e.visitor_id,
      e.event_name,
      e.control_name,
      e.page_section,
      v.first_campaign_source,
      v.first_campaign_content,
      v.first_campaign_name,
      v.is_immutable_employee
    FROM `prod-im-data.app_immutable_play.event` AS e
    INNER JOIN visitors AS v ON e.visitor_id = v.visitor_id
    WHERE 
      e.event_name IN ('GamePage_Pressed', 'GamePage_Succeeded', 'GamePage_Viewed') 
      AND (e.event_type <> 'backend' OR e.event_type IS NULL) 
      AND e.page_path LIKE '%/games/8-ball%'
      AND v.first_event_ts >= TIMESTAMP('2026-01-16 09:00:00')
      AND v.first_campaign_source IS NOT NULL
  ),

  -- 3. Map to Variants
  mapped_events AS (
    SELECT 
      visitor_id,
      event_name,
      control_name,
      page_section,
      is_immutable_employee,
      CASE
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%Conversion-Sign-Up%' AND first_campaign_name LIKE '%Desktop%' THEN 'Var0:D'
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%Conversion-Sign-Up%' AND first_campaign_name LIKE '%Mobile%' THEN 'Var0:M'
        WHEN first_campaign_source = 'fb' AND first_campaign_content LIKE '%Lead%' AND first_campaign_content LIKE '%Desktop%' THEN 'VarA:D'
        WHEN first_campaign_source = 'fb' AND first_campaign_content LIKE '%Lead%' AND first_campaign_content LIKE '%Mobile%' THEN 'VarA:M'
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%link-steam%' AND first_campaign_name LIKE '%Desktop%' THEN 'VarB:D'
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%link-steam%' AND first_campaign_name LIKE '%Mobile%' THEN 'VarB:M'
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%steam-sign-in%' AND first_campaign_name LIKE '%Desktop%' THEN 'VarC:D'
        WHEN first_campaign_source = 'youtube' AND first_campaign_content LIKE '%steam-sign-in%' AND first_campaign_name LIKE '%Mobile%' THEN 'VarC:M'
        ELSE 'others'
      END AS variant
    FROM base_events
    WHERE NOT COALESCE(is_immutable_employee, FALSE)
  )

-- 4. Final Aggregation (Funnel Metrics)
SELECT 
  variant,
  COUNT(DISTINCT CASE WHEN event_name = 'GamePage_Viewed' AND (control_name IS NULL OR control_name = 'game-page') THEN visitor_id END) AS page_land,
  COUNT(DISTINCT CASE WHEN event_name = 'GamePage_Pressed' AND control_name IN ('get-started', 'get-started-no-steam') AND page_section = 'onboarding-modal' THEN visitor_id END) AS first_event,
  COUNT(DISTINCT CASE WHEN event_name = 'GamePage_Pressed' AND control_name IN ('social-login-google', 'social-login-apple', 'social-login-facebook', 'email-login') THEN visitor_id END) AS auth_login_attempt,
  COUNT(DISTINCT CASE WHEN event_name = 'GamePage_Succeeded' AND control_name IN ('social-login-google', 'social-login-apple', 'social-login-facebook', 'email-login') THEN visitor_id END) AS auth_login_success
FROM mapped_events
WHERE variant <> 'others'
GROUP BY variant
ORDER BY variant
```

---

## Customization Points

| Parameter | Where | Example |
|-----------|-------|---------|
| `page_path` | Step 2 | `%/games/8-ball%`, `%/games/guild-of-guardians%` |
| `first_event_ts` | Step 2 | `TIMESTAMP('2026-01-16 09:00:00')` |
| `variant mapping` | Step 3 | Adjust CASE logic for campaign attribution |
| `funnel steps` | Step 4 | Add/remove COUNT(DISTINCT CASE...) |

---

## Data Layer

| Table | Purpose |
|-------|---------|
| `prod-im-data.app_immutable_play.visitor` | Visitor attributes, campaign attribution |
| `prod-im-data.app_immutable_play.event` | Event stream (page views, clicks, successes) |

---

## Funnel Steps

| Step | Event | Control Name |
|------|-------|--------------|
| **page_land** | `GamePage_Viewed` | `game-page` or NULL |
| **first_event** | `GamePage_Pressed` | `get-started`, `get-started-no-steam` |
| **auth_login_attempt** | `GamePage_Pressed` | `social-login-*`, `email-login` |
| **auth_login_success** | `GamePage_Succeeded` | `social-login-*`, `email-login` |

---

## TODO

**Analysis Improvements:**
- [ ] Add conversion rates between steps
- [ ] Add time-to-convert metrics
- [ ] Break down by device type

**Output & Delivery:**
- [ ] Automated daily report
- [ ] Visual funnel chart
- [ ] Slack integration
