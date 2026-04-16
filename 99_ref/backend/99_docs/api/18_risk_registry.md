# Risk Registry API

Base path: `/api/v1/rr`
Auth: Bearer JWT required on all endpoints

---

## Dimensions

### GET /api/v1/rr/risk-categories
Returns all risk category dimension records.

**Response** `200 OK`
```json
[
  { "code": "operational", "name": "Operational", "description": "...", "sort_order": 1 },
  { "code": "strategic",   "name": "Strategic",   "description": "...", "sort_order": 2 }
]
```

**All codes:** `operational`, `strategic`, `financial`, `compliance`, `reputational`, `technology`, `third_party`, `environmental`

### GET /api/v1/rr/risk-levels
Returns risk level dimension records with scoring ranges and colors.

**Response** `200 OK` — `RiskLevelResponse[]`
```json
[
  { "code": "critical", "name": "Critical", "score_min": 20, "score_max": 25, "color_hex": "#ef4444", "sort_order": 1 },
  { "code": "high",     "name": "High",     "score_min": 12, "score_max": 19, "color_hex": "#f97316", "sort_order": 2 },
  { "code": "medium",   "name": "Medium",   "score_min": 6,  "score_max": 11, "color_hex": "#eab308", "sort_order": 3 },
  { "code": "low",      "name": "Low",      "score_min": 1,  "score_max": 5,  "color_hex": "#3b82f6", "sort_order": 4 }
]
```

### GET /api/v1/rr/treatment-types
Returns risk treatment type dimension records.

**All codes:** `mitigate`, `accept`, `transfer`, `avoid`

---

## Risks

### GET /api/v1/rr/risks
List risks for the authenticated tenant.

**Query params**
| Param | Type | Description |
|-------|------|-------------|
| org_id | UUID | Filter to an organisation |
| workspace_id | UUID | Filter to a workspace |
| risk_category_code | string | operational, strategic, ... |
| risk_level_code | string | critical, high, medium, low |
| treatment_type_code | string | mitigate, accept, transfer, avoid |
| risk_status | string | identified, assessed, treating, accepted, closed |
| search | string | Full-text search on title/description |
| sort_by | string | created_at, risk_level_code, risk_status, updated_at |
| sort_dir | string | asc, desc (default: desc) |
| limit | int | 1–500 (default: 100) |
| offset | int | ≥0 (default: 0) |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...", "risk_code": "RISK-001",
      "org_id": "...", "workspace_id": "...",
      "risk_category_code": "operational", "risk_level_code": "high",
      "treatment_type_code": "mitigate", "risk_status": "assessed",
      "title": "Insufficient access controls",
      "description": "...",
      "is_active": true, "created_at": "2026-03-01T00:00:00Z"
    }
  ],
  "total": 12
}
```

**Risk status flow:** `identified` → `assessed` → `treating` → `accepted` | `closed`

### GET /api/v1/rr/risks/{risk_id}
Get single risk with all EAV properties.

**Response** `200 OK` — `RiskResponse`
```json
{
  "id": "...", "risk_code": "RISK-001",
  "risk_category_code": "operational", "risk_level_code": "high",
  "treatment_type_code": "mitigate", "risk_status": "assessed",
  "title": "Insufficient access controls",
  "description": "Users have excessive database permissions",
  "notes": "Flagged during Q1 audit",
  "owner_user_id": "...",
  "business_impact": "Data breach risk, potential regulatory fines",
  "likelihood_rationale": "Multiple failed access reviews",
  "impact_rationale": "Sensitive PII stored in affected systems",
  "source_reference": "Audit finding AF-2026-003"
}
```

### POST /api/v1/rr/risks
Create a new risk.

**Request body**
```json
{
  "org_id": "...",
  "workspace_id": "...",
  "risk_code": "RISK-001",
  "risk_category_code": "operational",
  "risk_level_code": "high",
  "treatment_type_code": "mitigate",
  "source_type": "manual",
  "title": "Insufficient access controls",
  "description": "...",
  "notes": "Optional notes",
  "owner_user_id": "...",
  "business_impact": "...",
  "source_reference": "AF-2026-003"
}
```

### PATCH /api/v1/rr/risks/{risk_id}
Update a risk.

### DELETE /api/v1/rr/risks/{risk_id}
Soft-delete. Returns `204 No Content`.

---

## Risk Assessments

Assessments are **immutable** — each assessment is a point-in-time 5×5 scoring record.

### GET /api/v1/rr/risks/{risk_id}/assessments
List all assessments for a risk, newest first.

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...", "risk_id": "...",
      "likelihood_score": 4, "impact_score": 5,
      "risk_score": 20,
      "assessment_type": "initial",
      "assessment_notes": "Based on Q1 audit findings",
      "created_at": "2026-03-15T10:30:00Z"
    }
  ],
  "total": 3
}
```

**risk_score** = `likelihood_score × impact_score` (1–25)

**Score colour thresholds:**
- ≥20 → Critical (red)
- ≥12 → High (orange)
- ≥6 → Medium (yellow)
- <6 → Low (blue)

### POST /api/v1/rr/risks/{risk_id}/assessments
Create a new assessment.

**Request body**
```json
{
  "likelihood_score": 4,
  "impact_score": 5,
  "assessment_type": "initial",
  "assessment_notes": "Based on Q1 audit findings"
}
```

**assessment_type values:** `initial`, `periodic`, `triggered`, `post_treatment`

---

## Treatment Plans

Each risk has at most one active treatment plan.

### GET /api/v1/rr/risks/{risk_id}/treatment-plan
Get the active treatment plan for a risk (404 if none exists).

**Response** `200 OK` — `TreatmentPlanResponse`
```json
{
  "id": "...", "risk_id": "...",
  "plan_status": "in_progress",
  "target_date": "2026-06-30T00:00:00Z",
  "is_active": true, "completed_at": null,
  "properties": {
    "plan_description": "Implement RBAC across all database systems",
    "action_items": "1. Audit current permissions\n2. Define RBAC schema\n3. Migrate",
    "approver_user_id": "...",
    "review_frequency": "monthly"
  }
}
```

**plan_status values:** `draft`, `approved`, `in_progress`, `completed`, `overdue`

### POST /api/v1/rr/risks/{risk_id}/treatment-plans
Create a treatment plan.

**Request body**
```json
{
  "plan_status": "draft",
  "target_date": "2026-06-30",
  "plan_description": "...",
  "action_items": "...",
  "approver_user_id": "...",
  "review_frequency": "monthly"
}
```

### PATCH /api/v1/rr/risks/{risk_id}/treatment-plans/{plan_id}
Update a treatment plan.

**Request body** (all optional)
```json
{
  "plan_status": "approved",
  "target_date": "2026-09-30",
  "plan_description": "Updated plan description"
}
```

---

## Risk Control Mappings

Link risks to GRC library controls that are intended to mitigate them.

### GET /api/v1/rr/risks/{risk_id}/control-mappings
List control mappings for a risk.

### POST /api/v1/rr/risks/{risk_id}/control-mappings
Create a control mapping.

**Request body**
```json
{ "control_id": "..." }
```

### DELETE /api/v1/rr/risks/{risk_id}/control-mappings/{mapping_id}
Remove a control mapping. Returns `204 No Content`.

---

## Risk Review Events

Immutable audit trail of lifecycle events.

### GET /api/v1/rr/risks/{risk_id}/reviews
List review events, newest first.

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...", "risk_id": "...",
      "event_type": "status_changed",
      "old_value": "identified", "new_value": "assessed",
      "comment": "Completed initial 5×5 assessment",
      "actor_id": "...", "occurred_at": "2026-03-15T10:30:00Z"
    }
  ],
  "total": 5
}
```

### POST /api/v1/rr/risks/{risk_id}/reviews
Add a review event (comment or status change).

**Request body**
```json
{
  "event_type": "comment",
  "comment": "Reviewed with compliance team — on track"
}
```

---

## Risk Summary (KPI)

### GET /api/v1/rr/risks/summary

Get KPI summary counts for risks in an org — used by dashboard stat cards.

**Query params:** `org_id` (UUID, optional)

**Response** `200 OK`
```json
{
  "total": 24,
  "by_status": {
    "identified": 8,
    "assessed": 6,
    "treating": 7,
    "accepted": 2,
    "closed": 1
  },
  "by_level": {
    "critical": 3,
    "high": 7,
    "medium": 10,
    "low": 4
  },
  "overdue_count": 2,
  "avg_risk_score": 11.4
}
```

---

## Risk Heat Map

### GET /api/v1/rr/risks/heat-map

Get a 5×5 likelihood × impact heat map showing risk density.

**Query params:** `org_id` (UUID, optional), `workspace_id` (UUID, optional)

**Response** `200 OK`
```json
{
  "cells": [
    {
      "likelihood_score": 4,
      "impact_score": 5,
      "risk_score": 20,
      "count": 3,
      "risk_ids": ["...", "...", "..."]
    },
    {
      "likelihood_score": 3,
      "impact_score": 4,
      "risk_score": 12,
      "count": 5,
      "risk_ids": ["..."]
    }
  ],
  "max_count": 5
}
```

**Color coding** (from `risk_score`):

- ≥20 → Critical (`#ef4444`)
- ≥12 → High (`#f97316`)
- ≥6 → Medium (`#eab308`)
- <6 → Low (`#3b82f6`)

---

## Export Risks

### GET /api/v1/rr/risks/export

Export risks as CSV. Returns streaming `text/csv` response.

**Query params:** `org_id` (UUID, optional), `workspace_id` (UUID, optional)

**Response** `200 OK` — `Content-Type: text/csv; charset=utf-8`

CSV columns: `risk_code`, `title`, `risk_category_code`, `risk_level_code`, `risk_status`, `treatment_type_code`, `owner_display_name`, `current_risk_score`, `created_at`

---

## Group Assignments (RACI)

### GET /api/v1/rr/risks/{risk_id}/groups

List RACI group assignments for a risk.

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "risk_id": "...",
      "group_id": "...",
      "role": "accountable",
      "notes": "Security team owns this risk",
      "assigned_at": "2026-03-20T10:00:00Z",
      "assigned_by": "..."
    }
  ],
  "total": 2
}
```

**RACI role values:** `responsible`, `accountable`, `consulted`, `informed`

### POST /api/v1/rr/risks/{risk_id}/groups

Assign a group to a risk with a RACI role.

**Request body**
```json
{
  "group_id": "...",
  "role": "accountable",
  "notes": "Primary responsible team"
}
```

**Response** `201 Created` — `RiskGroupAssignmentResponse`

### DELETE /api/v1/rr/risks/{risk_id}/groups/{assignment_id}

Remove a group assignment. Returns `204 No Content`.

---

## Risk Appetite

### GET /api/v1/rr/risks/appetite

List risk appetite thresholds for an org.

**Query params:** `org_id` (UUID, required)

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "org_id": "...",
      "category_code": "technology",
      "max_tolerance_score": 12,
      "appetite_description": "Moderate tolerance for technology risks",
      "created_at": "2026-03-20T10:00:00Z"
    }
  ],
  "total": 3
}
```

### PUT /api/v1/rr/risks/appetite

Create or update an appetite threshold for an org + category combination.

**Request body**
```json
{
  "org_id": "...",
  "category_code": "technology",
  "max_tolerance_score": 12,
  "appetite_description": "Moderate tolerance for technology risks"
}
```

**Response** `200 OK` — `RiskAppetiteResponse`

---

## Scheduled Reviews

### GET /api/v1/rr/risks/{risk_id}/review-schedule

Get the review schedule for a risk.

**Response** `200 OK`
```json
{
  "id": "...",
  "risk_id": "...",
  "frequency": "quarterly",
  "next_review_date": "2026-06-30T00:00:00Z",
  "last_reviewed_at": "2026-03-20T10:00:00Z",
  "is_overdue": false,
  "notes": "Quarterly board-level review",
  "created_at": "2026-03-01T00:00:00Z"
}
```

**`frequency` values:** `weekly`, `monthly`, `quarterly`, `semi_annual`, `annual`

**`is_overdue`** is computed: `next_review_date < NOW() AND last_reviewed_at IS NULL OR last_reviewed_at < next_review_date`

### PUT /api/v1/rr/risks/{risk_id}/review-schedule

Create or update the review schedule.

**Request body**
```json
{
  "frequency": "quarterly",
  "next_review_date": "2026-06-30",
  "notes": "Quarterly board-level review"
}
```

### POST /api/v1/rr/risks/{risk_id}/review-schedule/complete

Mark a review as complete. Advances `next_review_date` based on frequency.

**Request body**
```json
{
  "notes": "Q1 review completed — risk level unchanged",
  "outcome": "no_change"
}
```

**`outcome` values:** `no_change`, `risk_reduced`, `risk_increased`, `risk_closed`

---

## Overdue Reviews

### GET /api/v1/rr/risks/overdue-reviews

List risks with overdue scheduled reviews.

**Query params:** `org_id` (UUID, optional)

**Response** `200 OK`
```json
{
  "items": [
    {
      "risk_id": "...",
      "risk_code": "RISK-007",
      "title": "Third-party vendor access",
      "risk_status": "treating",
      "next_review_date": "2026-01-15T00:00:00Z",
      "days_overdue": 64,
      "frequency": "quarterly"
    }
  ],
  "total": 4
}
```

---

## Auto-Task Creation

When a risk is created with `risk_level_code` of `high` or `critical`, a `risk_mitigation` task is **automatically created** and linked to the risk:

- `entity_type = "risk"`, `entity_id = <risk_id>`
- `task_type_code = "risk_mitigation"`
- `priority_code` matches the risk level (`high` or `critical`)
- `title` = `"Mitigate risk: <risk title>"`

The task is created within the same database transaction as the risk. No opt-in required.

## Version Tracking

All risks include a `version` field (integer, starts at 1) that increments automatically on each update. Use this to detect stale reads or track change history.
