# Soma Delights — Generic ERP Platform Technical Reference

> A configurable entity framework that runs any small-business operation end-to-end.
> Define entity types, relationships, workflows, and automation rules through the admin UI — no code deploys.
> Soma Delights juice operations are the first tenant; the platform is domain-agnostic by design.

---

## 1. Architecture Overview

### Design Philosophy

The platform is a **truly generic ERP/CRM/Relationship Management system**. Instead of hardcoding domain-specific tables for every new concept, the core architecture provides:

1. **Configurable Entity Framework** — define any entity type (Customer, Vehicle, Campaign, Contract) and its custom fields through Settings UI
2. **Relationship Graph** — connect any two entities bidirectionally with typed relationships (Customer employs Rider, Vehicle assigned-to Route)
3. **Universal Activity Feed** — every entity gets a timeline of events, notes, and state changes
4. **Workflow Engine** — define multi-step approval/production/onboarding workflows per entity type
5. **Automation Rules** — event-driven triggers with condition/action pairs, configured through UI

### Hybrid Architecture: Hardcoded + Generic

The system uses a **hybrid approach** for pragmatic reasons:

| Layer | Purpose | Example |
|-------|---------|---------|
| **Hardcoded domain tables** | Performance-critical entities with complex constraints, FKs, and indexes | `products`, `ingredients`, `recipes`, `invoices` |
| **EAV / JSONB properties** | Extensibility on every domain table + central cross-entity queries | `properties JSONB` column on every table + `entity_attributes` EAV store |
| **Generic entity framework** | Net-new entity types added through UI without migrations | Vehicle, Campaign, Contract, Equipment |

Every hardcoded domain table carries a `properties JSONB NOT NULL DEFAULT '{}'` column. This means even "typed" entities are extensible without schema changes.

### Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js 15 (App Router) + shadcn/ui + next-intl | Server components, accessible UI primitives, multi-lingual (EN/HI/TE) from day one |
| Backend | FastAPI (Python 3.12) | Feature-driven structure, async-native, auto-generated OpenAPI docs |
| Database | PostgreSQL (shared `soma` DB) | Sub-schemas for domain isolation, JSONB for flexibility, GIN indexes for fast property queries |
| DB Access | Raw asyncpg (no ORM) | Full control over queries, connection pooling, prepared statements |
| Auth | s-auth service (JWT) | Separate microservice handling authentication, MFA, OAuth2/OIDC |
| Secrets | s-vault | API key-based secrets management, SOC2/NIST compliant |
| Notifications | s-notify | Event-driven — subscribes to ERP domain events, handles WhatsApp/email/push |

### PostgreSQL Sub-Schema Layout

All tables live in the shared `soma` database under numbered schemas:

| Schema | Domain | Purpose |
|--------|--------|---------|
| `03_erp_system` | System infrastructure | Entity framework, EAV, audit log, automation rules, workflows, tags, documents, webhooks |
| `03_erp_catalog` | Product catalog | Product lines, SKUs, ingredients, recipes, workflow templates, locations, wellness profiles, subscription plan templates |
| `03_erp_crm` | Customer relationships | Customer lifecycle (8-state machine), health scores, wellness profiles, partner program, communications |
| `03_erp_ops` | Operations | Procurement, production batches, inventory, capacity planning, zones, suppliers, equipment |
| `03_erp_billing` | Billing & payments | Razorpay subscriptions, invoices, dunning, partner payouts, cash flow forecasting |
| `03_erp_growth` | Growth & GTM | Kiosk ROI, trial conversion, ambassador performance, booklet tracking, onboarding drip sequences |
| `03_erp_hrm` | Human resources | Team members, roles, shifts, attendance, payroll, performance reviews |

Schemas `01_*` belong to s-vault, `02_*` to s-auth. The ERP claims the `03_*` prefix.

---

## 2. Core Generic Tables (`03_erp_system` Schema)

These tables form the **configurable entity framework** — the backbone that makes the platform generic.

### 2.1 Entity Type Definitions

```sql
"03_erp_system"."entity_type_definitions"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    code            TEXT NOT NULL        -- 'vehicle', 'campaign', 'contract'
    name            TEXT NOT NULL        -- 'Vehicle', 'Campaign', 'Contract'
    name_plural     TEXT NOT NULL        -- 'Vehicles', 'Campaigns', 'Contracts'
    icon            TEXT                 -- Lucide icon name: 'truck', 'megaphone', 'file-text'
    color           TEXT                 -- Hex color for UI badges
    description     TEXT
    schema          TEXT                 -- JSON Schema for validation of entity data
    is_system       BOOLEAN DEFAULT FALSE -- TRUE for built-in types (customer, product); prevents deletion
    is_active       BOOLEAN DEFAULT TRUE
    properties      JSONB DEFAULT '{}'
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ
    UNIQUE (tenant_id, code)
```

Pre-seeded system types: `customer`, `product`, `ingredient`, `supplier`, `location`, `production_batch`, `invoice`, `subscription`.

### 2.2 Entity Field Definitions

```sql
"03_erp_system"."entity_field_definitions"
    id                  UUID PRIMARY KEY
    entity_type_code    TEXT NOT NULL      -- FK to entity_type_definitions.code
    tenant_id           UUID NOT NULL
    field_name          TEXT NOT NULL      -- 'license_plate', 'campaign_budget'
    field_label         TEXT NOT NULL      -- 'License Plate', 'Campaign Budget'
    field_type          TEXT NOT NULL      -- 'text', 'number', 'date', 'select', 'multi_select',
                                           -- 'boolean', 'url', 'email', 'phone', 'currency',
                                           -- 'file', 'entity_reference', 'json'
    is_required         BOOLEAN DEFAULT FALSE
    is_filterable       BOOLEAN DEFAULT TRUE
    is_shown_in_list    BOOLEAN DEFAULT TRUE
    display_order       INTEGER DEFAULT 0
    default_value       JSONB              -- default value for new entities
    options             JSONB              -- for select/multi_select: [{value, label, color}]
    validation_rules    JSONB              -- {min, max, pattern, min_length, max_length}
    properties          JSONB DEFAULT '{}'
    created_at          TIMESTAMPTZ
    updated_at          TIMESTAMPTZ
    UNIQUE (tenant_id, entity_type_code, field_name)
```

### 2.3 Relationships

```sql
"03_erp_system"."relationship_type_definitions"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    code            TEXT NOT NULL          -- 'employs', 'assigned_to', 'supplies'
    a_entity_type   TEXT NOT NULL          -- 'customer'
    b_entity_type   TEXT NOT NULL          -- 'vehicle'
    label_a_to_b    TEXT NOT NULL          -- 'owns vehicle'
    label_b_to_a    TEXT NOT NULL          -- 'owned by customer'
    cardinality     TEXT DEFAULT 'many_to_many'  -- 'one_to_one', 'one_to_many', 'many_to_many'
    properties      JSONB DEFAULT '{}'
    created_at      TIMESTAMPTZ
    UNIQUE (tenant_id, code)

"03_erp_system"."relationships"
    id                  UUID PRIMARY KEY
    tenant_id           UUID NOT NULL
    relationship_type   TEXT NOT NULL      -- FK to relationship_type_definitions.code
    entity_a_type       TEXT NOT NULL
    entity_a_id         UUID NOT NULL
    entity_b_type       TEXT NOT NULL
    entity_b_id         UUID NOT NULL
    properties          JSONB DEFAULT '{}' -- relationship-specific data: start_date, role, notes
    created_at          TIMESTAMPTZ
    UNIQUE (tenant_id, relationship_type, entity_a_id, entity_b_id)
```

Indexes: GIN on properties, composite on `(entity_a_type, entity_a_id)` and `(entity_b_type, entity_b_id)` for bidirectional lookups.

### 2.4 Universal Activity Feed

```sql
"03_erp_system"."activities"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    entity_type     TEXT NOT NULL
    entity_id       UUID NOT NULL
    activity_type   TEXT NOT NULL      -- 'note', 'status_change', 'email_sent', 'call_logged',
                                       -- 'document_uploaded', 'payment_received', 'task_completed'
    actor_id        UUID NOT NULL      -- s-auth user ID
    title           TEXT
    data            JSONB DEFAULT '{}' -- activity-specific payload
    is_internal     BOOLEAN DEFAULT FALSE -- internal notes hidden from customer-facing views
    created_at      TIMESTAMPTZ
```

Index: `(entity_type, entity_id, created_at DESC)` for timeline queries.

### 2.5 Tags

```sql
"03_erp_system"."tags"
    id          UUID PRIMARY KEY
    tenant_id   UUID NOT NULL
    group_name  TEXT NOT NULL          -- 'priority', 'category', 'source', 'dietary'
    name        TEXT NOT NULL          -- 'VIP', 'Organic', 'Walk-in', 'Diabetic-friendly'
    color       TEXT                   -- hex color for UI
    UNIQUE (tenant_id, group_name, name)

"03_erp_system"."entity_tags"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    entity_type     TEXT NOT NULL
    entity_id       UUID NOT NULL
    tag_id          UUID NOT NULL REFERENCES tags(id)
    created_at      TIMESTAMPTZ
    UNIQUE (tenant_id, entity_type, entity_id, tag_id)
```

### 2.6 Tasks

```sql
"03_erp_system"."tasks"
    id                  UUID PRIMARY KEY
    tenant_id           UUID NOT NULL
    title               TEXT NOT NULL
    description         TEXT
    assignee_id         UUID               -- s-auth user ID
    priority            TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent'))
    status              TEXT DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'done', 'cancelled'))
    due_at              TIMESTAMPTZ
    sla_minutes         INTEGER            -- SLA deadline in minutes from creation; NULL = no SLA
    source_entity_type  TEXT               -- entity that spawned this task
    source_entity_id    UUID
    completed_at        TIMESTAMPTZ
    properties          JSONB DEFAULT '{}'
    created_at          TIMESTAMPTZ
    updated_at          TIMESTAMPTZ
```

### 2.7 Workflow Engine

```sql
"03_erp_system"."workflow_definitions"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    name            TEXT NOT NULL          -- 'Customer Onboarding', 'Vehicle Maintenance'
    entity_type     TEXT NOT NULL          -- which entity type triggers this workflow
    trigger_on      TEXT DEFAULT 'manual'  -- 'manual', 'on_create', 'on_status_change'
    steps           JSONB NOT NULL         -- [{order, name, type, assignee_role, sla_minutes, actions}]
    is_active       BOOLEAN DEFAULT TRUE
    properties      JSONB DEFAULT '{}'
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ

"03_erp_system"."workflow_instances"
    id                  UUID PRIMARY KEY
    tenant_id           UUID NOT NULL
    definition_id       UUID NOT NULL REFERENCES workflow_definitions(id)
    entity_type         TEXT NOT NULL
    entity_id           UUID NOT NULL
    current_step        INTEGER NOT NULL DEFAULT 1
    status              TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled', 'paused'))
    history             JSONB DEFAULT '[]'  -- [{step, action, actor_id, timestamp, notes}]
    started_at          TIMESTAMPTZ
    completed_at        TIMESTAMPTZ
    properties          JSONB DEFAULT '{}'
    created_at          TIMESTAMPTZ
    updated_at          TIMESTAMPTZ
```

### 2.8 Automation Rules

```sql
"03_erp_system"."automation_rules"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    name            TEXT NOT NULL          -- 'Auto-assign VIP tag on 5th order'
    trigger_event   TEXT NOT NULL          -- 'entity.created', 'entity.updated', 'field.changed',
                                           -- 'workflow.step_completed', 'schedule.daily'
    trigger_entity  TEXT                   -- entity type filter, NULL = all
    condition       JSONB NOT NULL         -- {field, operator, value} tree with AND/OR
    action          JSONB NOT NULL         -- {type: 'create_task'|'send_webhook'|'add_tag'|
                                           --        'update_field'|'start_workflow'|'send_notification',
                                           --  params: {...}}
    is_active       BOOLEAN DEFAULT TRUE
    run_count       INTEGER DEFAULT 0
    last_run_at     TIMESTAMPTZ
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ

"03_erp_system"."automation_log"
    id              UUID PRIMARY KEY
    rule_id         UUID NOT NULL REFERENCES automation_rules(id)
    trigger_event   TEXT NOT NULL
    entity_type     TEXT
    entity_id       UUID
    condition_met   BOOLEAN NOT NULL
    action_result   JSONB                  -- {success, error, duration_ms}
    created_at      TIMESTAMPTZ
```

### 2.9 Documents

```sql
"03_erp_system"."documents"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    name            TEXT NOT NULL
    file_url        TEXT NOT NULL
    mime_type       TEXT
    size_bytes      BIGINT
    entity_type     TEXT NOT NULL
    entity_id       UUID NOT NULL
    version         INTEGER DEFAULT 1
    uploaded_by     UUID NOT NULL          -- s-auth user ID
    expires_at      TIMESTAMPTZ            -- NULL = never expires
    properties      JSONB DEFAULT '{}'
    created_at      TIMESTAMPTZ
```

### 2.10 Webhooks

```sql
"03_erp_system"."webhooks"
    id              UUID PRIMARY KEY
    tenant_id       UUID NOT NULL
    event_type      TEXT NOT NULL          -- 'entity.created', 'entity.updated', 'invoice.paid'
    entity_filter   TEXT                   -- optional entity type filter
    url             TEXT NOT NULL
    headers         JSONB DEFAULT '{}'     -- custom headers (e.g., Authorization)
    is_active       BOOLEAN DEFAULT TRUE
    secret          TEXT                   -- HMAC signing secret for payload verification
    created_at      TIMESTAMPTZ
    updated_at      TIMESTAMPTZ

"03_erp_system"."webhook_deliveries"
    id              UUID PRIMARY KEY
    webhook_id      UUID NOT NULL REFERENCES webhooks(id)
    event_type      TEXT NOT NULL
    payload         JSONB NOT NULL
    response_code   INTEGER
    response_body   TEXT
    attempts        INTEGER DEFAULT 1
    delivered_at    TIMESTAMPTZ
    created_at      TIMESTAMPTZ
```

### 2.11 Existing Tables (Already Migrated)

These tables already exist in the `03_erp_system` schema:

- **`entity_attributes`** — Central EAV store for cross-entity attribute queries. Per-row fast reads use the `properties` JSONB column on each domain table instead. See migration `20260324_007`.
- **`audit_log`** — Append-only audit log for FSSAI traceability. Application role `erp_app_user` has INSERT only. Captures `actor_id`, `actor_email`, `entity_type`, `entity_id`, `action`, `before_state`, `after_state`, `ip_address`. See migration `20260324_008`.

---

## 3. Domain-Specific Schemas

Each domain schema contains performance-optimized tables with typed columns, foreign keys, and constraints. Every table includes a `properties JSONB DEFAULT '{}'` column for extensibility.

### 3.1 `03_erp_catalog` — Product Catalog

The foundation layer. All other schemas reference catalog entities.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `product_lines` | Product categories (Juice Cleanses, Wellness Shots) | name, slug, is_active, properties |
| `products` | Individual SKUs within a product line | product_line_id, volume_ml, price_paise, is_seasonal, season_months |
| `ingredients` | Ingredient registry for recipe costing | unit (grams/ml/pieces), yield_percent, waste_percent, pulp_reusable |
| `recipes` | Ingredient-to-product mapping with gram ratios | product_id, ingredient_id, quantity_per_unit |
| `subscription_plan_templates` | Reusable subscription plan definitions | frequency, duration, discount rules |
| `workflow_templates` | Production workflow templates per product line | product_line_id, ordered steps with QC gates |
| `workflow_steps` | Ordered steps within a workflow template | step_order, is_qc_gate, qc_checks JSONB |
| `locations` | Location hierarchy (city > zone > kitchen > cluster) | parent_id (self-referential), level, properties |
| `wellness_profiles` | Customer wellness goal templates | dietary preferences, health conditions, recommended SKUs |

All prices stored in **paise** (integer, INR x 100) to avoid floating-point errors. Display divides by 100.

### 3.2 `03_erp_crm` — Customer Relationships

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `customers` | Customer master with 8-state lifecycle | status (lead/trial/active/paused/churned/win_back/reactivated/archived), location_id |
| `customer_health_scores` | Computed engagement/retention scores | score, factors JSONB, computed_at |
| `customer_wellness_profiles` | Per-customer wellness preferences | wellness_profile_id, custom overrides |
| `partner_wallets` | Partner Program earning tracking | customer_id, balance_paise, lifetime_earned_paise |
| `partner_transactions` | Partner earning/payout ledger | wallet_id, amount_paise, type (earn/payout/adjustment) |
| `communications` | All outbound messages (WhatsApp, email, SMS) | customer_id, channel, template, status, sent_at |

### 3.3 `03_erp_ops` — Operations

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `suppliers` | Supplier registry | name, contact, location, rating, payment_terms |
| `purchase_orders` | Procurement orders | supplier_id, ingredient_id, qty, unit_price_paise, status |
| `price_history` | Market price tracking across sources | ingredient_id, source, price_paise, zone, recorded_at |
| `inventory` | Current stock levels | ingredient_id, location_id, quantity, unit, updated_at |
| `production_batches` | Daily batch log (FSSAI traceability) | sku_id, planned_qty, actual_yield, ingredient_cost_paise, qc_pass, spoilage_qty |
| `capacity_config` | Per-zone production/delivery limits | location_id, max_daily_units, buffer_percent |
| `equipment` | Equipment registry | name, type, location_id, status, maintenance_due_at |
| `delivery_routes` | Route planning and optimization | location_id, rider_id, sequence, status |

### 3.4 `03_erp_billing` — Billing & Payments

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `subscriptions` | Active customer subscriptions | customer_id, plan_template_id, status, razorpay_subscription_id |
| `invoices` | Monthly/weekly invoices | subscription_id, amount_paise, status (draft/sent/paid/overdue/void) |
| `invoice_line_items` | Individual line items per invoice | invoice_id, product_id, qty, unit_price_paise |
| `payments` | Payment records from Razorpay | invoice_id, razorpay_payment_id, amount_paise, method, status |
| `dunning_events` | Failed payment retry tracking | subscription_id, attempt, next_retry_at, status |
| `partner_payouts` | Bulk payout runs to partners | total_amount_paise, status, utr_number |
| `cash_flow_forecasts` | Projected revenue and expense | period, projected_revenue_paise, projected_expense_paise |

### 3.5 `03_erp_growth` — Growth & GTM

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `kiosks` | Physical kiosk locations with ROI tracking | location_id, setup_cost_paise, monthly_cost_paise |
| `kiosk_sessions` | Daily kiosk traffic and conversion | kiosk_id, date, footfall, samples, signups |
| `trials` | Free trial tracking | customer_id, start_date, end_date, converted |
| `ambassadors` | Brand ambassador registry | customer_id, tier, active_referrals, lifetime_referrals |
| `booklet_batches` | Print booklet production runs | qty, unit_cost_paise, distribution_zone |
| `qr_scans` | QR code scan tracking | source, campaign, scanned_at, converted |
| `onboarding_sequences` | Drip sequence definitions and delivery | customer_id, step, channel, sent_at, opened |

### 3.6 `03_erp_hrm` — Human Resources (Future)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `team_members` | Employee/contractor registry | user_id (s-auth), role, employment_type, location_id |
| `shifts` | Shift scheduling | team_member_id, date, start_time, end_time, location_id |
| `attendance` | Clock-in/clock-out records | team_member_id, shift_id, actual_start, actual_end |
| `payroll_runs` | Monthly payroll processing | period, total_paise, status |
| `performance_reviews` | Periodic reviews | team_member_id, reviewer_id, period, score, notes |

---

## 4. Generic UI Pattern

All entity list pages follow the same rendering pattern, driven by `entity_type_definitions` and `entity_field_definitions`.

### 4.1 List View

```text
┌──────────────────────────────────────────────────────────────────┐
│  Vehicles                                        [+ Add Vehicle] │
│  ─────────────────────────────────────────────────────────────── │
│  [Search...]  [Filter: Status ▼] [Filter: Zone ▼]  [Tags ▼]    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ License Plate  │ Make/Model    │ Zone      │ Status │ Tags  │ │
│  │────────────────│───────────────│───────────│────────│───────│ │
│  │ TS 09 AB 1234  │ Bajaj RE      │ Miyapur   │ Active │ EV    │ │
│  │ TS 09 CD 5678  │ Piaggio Ape   │ KPHB      │ Maint. │       │ │
│  │ TS 09 EF 9012  │ Bajaj RE      │ Chandangr │ Active │ EV    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  Showing 1-3 of 3                        [< Prev]  [Next >]     │
└──────────────────────────────────────────────────────────────────┘
```

**How it works:**

1. Fetch `entity_type_definitions` where `code = 'vehicle'` to get display name, icon, color
2. Fetch `entity_field_definitions` where `entity_type_code = 'vehicle'` and `is_shown_in_list = true`, ordered by `display_order`
3. Render TanStack Table column headers from field definitions
4. Server-side sort, filter, and paginate using field metadata
5. Tag badges rendered from `entity_tags` join

### 4.2 Create / Edit Form

Forms are **auto-generated** from `entity_field_definitions`:

| `field_type` | Renders As |
|--------------|------------|
| `text` | Input field |
| `number` / `currency` | Numeric input (currency shows Rs prefix) |
| `date` | Date picker |
| `select` | Dropdown from `options` JSONB |
| `multi_select` | Multi-select chips |
| `boolean` | Toggle switch |
| `url` / `email` / `phone` | Input with format validation |
| `file` | File upload dropzone |
| `entity_reference` | Searchable entity picker (combobox) |
| `json` | JSON editor (for power users) |

Validation rules from `validation_rules` JSONB are applied client-side (zod schema generated dynamically) and server-side (FastAPI pydantic).

### 4.3 Detail View

Every entity detail page has the same layout:

```text
┌──────────────────────────────────────────────────────────────────┐
│  ← Back to Vehicles                               [Edit] [...]  │
│                                                                  │
│  🚛 Bajaj RE — TS 09 AB 1234                                    │
│  Tags: [EV] [Zone: Miyapur]                                     │
│                                                                  │
│  ┌─────────────────────────────┬────────────────────────────────┐│
│  │  DETAILS                    │  RELATIONSHIPS                 ││
│  │  License Plate: TS 09 AB..  │  👤 Assigned to: Ravi Kumar    ││
│  │  Make: Bajaj                │  📍 Zone: Miyapur              ││
│  │  Model: RE                  │  🏭 Kitchen: Cloud Kitchen 1   ││
│  │  Year: 2024                 │  [+ Add Relationship]          ││
│  │  Status: Active             │                                ││
│  │  Odometer: 12,450 km        │  DOCUMENTS                    ││
│  │  Insurance exp: 15 Oct 2026 │  📄 RC Book (v1) — 2.1 MB     ││
│  │  Last service: 10 Mar 2026  │  📄 Insurance — 890 KB        ││
│  │                             │  [+ Upload Document]           ││
│  └─────────────────────────────┴────────────────────────────────┘│
│                                                                  │
│  ACTIVITY TIMELINE                                               │
│  ─────────────────                                               │
│  24 Mar 10:15  Sri created this vehicle                          │
│  24 Mar 10:20  Sri uploaded RC Book                              │
│  24 Mar 11:00  Automation: assigned to Ravi (nearest rider)      │
│  25 Mar 06:00  Workflow: maintenance check due (SLA: 48h)        │
│                                                                  │
│  [Add Note]  [Log Call]  [Create Task]                           │
└──────────────────────────────────────────────────────────────────┘
```

### 4.4 Frontend Component Architecture

```text
src/
  features/
    entities/
      components/
        EntityListPage.tsx        -- generic list (fetches type def, renders table)
        EntityDetailPage.tsx      -- generic detail (data + relationships + timeline)
        EntityForm.tsx            -- generic create/edit (generated from field defs)
        RelationshipPanel.tsx     -- bidirectional relationship cards
        ActivityTimeline.tsx      -- universal activity feed
        DocumentPanel.tsx         -- file upload + version history
        TagSelector.tsx           -- tag picker grouped by group_name
      hooks/
        useEntityType.ts          -- fetches entity_type_definition + field_definitions
        useEntityList.ts          -- paginated list with sort/filter
        useEntityDetail.ts        -- single entity with relationships, activities, docs
        useEntityMutation.ts      -- create/update with optimistic updates
```

Domain-specific pages (e.g., `/procurement`, `/capacity`) use **custom layouts** that still compose from the generic components where applicable.

---

## 5. Automation Rules — Practical Examples

### Example 1: Auto-Tag VIP Customers

```json
{
  "name": "Tag customer as VIP after 5th order",
  "trigger_event": "entity.updated",
  "trigger_entity": "customer",
  "condition": {
    "field": "properties.total_orders",
    "operator": "gte",
    "value": 5
  },
  "action": {
    "type": "add_tag",
    "params": { "tag_group": "priority", "tag_name": "VIP" }
  }
}
```

### Example 2: Create Task on Overdue Vehicle Maintenance

```json
{
  "name": "Create maintenance task when vehicle service overdue",
  "trigger_event": "schedule.daily",
  "trigger_entity": "vehicle",
  "condition": {
    "field": "properties.next_service_date",
    "operator": "lt",
    "value": "$TODAY"
  },
  "action": {
    "type": "create_task",
    "params": {
      "title": "Vehicle {{entity.properties.license_plate}} — overdue maintenance",
      "priority": "high",
      "sla_minutes": 2880,
      "assignee_role": "ops_manager"
    }
  }
}
```

### Example 3: Send Webhook on Invoice Payment

```json
{
  "name": "Notify accounting system when invoice paid",
  "trigger_event": "field.changed",
  "trigger_entity": "invoice",
  "condition": {
    "field": "status",
    "operator": "eq",
    "value": "paid"
  },
  "action": {
    "type": "send_webhook",
    "params": { "webhook_code": "accounting_sync" }
  }
}
```

### Example 4: Start Onboarding Workflow on New Customer

```json
{
  "name": "Auto-start onboarding when customer created",
  "trigger_event": "entity.created",
  "trigger_entity": "customer",
  "condition": { "always": true },
  "action": {
    "type": "start_workflow",
    "params": { "workflow_name": "Customer Onboarding" }
  }
}
```

### Example 5: Capacity Alert When Zone Hits 85%

```json
{
  "name": "Alert ops when zone capacity exceeds 85%",
  "trigger_event": "entity.updated",
  "trigger_entity": "capacity_config",
  "condition": {
    "field": "properties.current_utilization_percent",
    "operator": "gte",
    "value": 85
  },
  "action": {
    "type": "send_notification",
    "params": {
      "channel": "whatsapp",
      "template": "capacity_warning",
      "recipient_role": "ops_manager"
    }
  }
}
```

### Example 6: Auto-Pause Subscription on 3 Failed Payments

```json
{
  "name": "Pause subscription after 3 dunning failures",
  "trigger_event": "entity.updated",
  "trigger_entity": "dunning_events",
  "condition": {
    "field": "attempt",
    "operator": "gte",
    "value": 3
  },
  "action": {
    "type": "update_field",
    "params": {
      "target_entity": "subscription",
      "target_id_field": "subscription_id",
      "field": "status",
      "value": "paused"
    }
  }
}
```

---

## 6. What This Architecture Enables

### No-Code Entity Creation

Through **Settings > Entity Types**, an admin can:

1. **Add a new entity type** (e.g., "Vehicle", "Campaign", "Contract", "Equipment")
   - Set name, icon, color
   - Define custom fields with types, validation, and display order
   - Entity immediately gets: list page, detail page, create/edit forms, search, filters

2. **Define relationships** between any entities
   - Vehicle ↔ Rider ("assigned to" / "drives")
   - Campaign ↔ Customer ("targets" / "enrolled in")
   - Contract ↔ Supplier ("signed with" / "has contract")
   - Relationships appear automatically on detail pages

3. **Create workflows** for any entity type
   - Vehicle Maintenance: Inspection > Repair > QC Check > Return to Service
   - Campaign Approval: Draft > Manager Review > Finance Approval > Launch
   - Customer Onboarding: Welcome Call > First Delivery > 7-Day Check-in > 30-Day Review

4. **Set automation rules** for event-driven behavior
   - When vehicle maintenance is overdue, create a high-priority task
   - When a campaign budget exceeds Rs 50,000, require manager approval workflow
   - When a contract expires in 30 days, send renewal notification

### What Still Requires Code

| Change | Requires Code? | Why |
|--------|---------------|-----|
| Add entity type with custom fields | No | Entity framework handles it |
| Add relationship between entities | No | Relationship type definitions |
| Create workflow for entity | No | Workflow definitions |
| Add automation rule | No | Automation rules engine |
| Complex domain logic (recipe costing, capacity planning) | Yes | Performance-critical calculations need typed tables and optimized queries |
| New payment gateway integration | Yes | External API integration |
| Custom report with complex aggregation | Yes | Domain-specific SQL queries |
| New notification channel | Yes | s-notify integration work |

### Scale Characteristics

| Metric | Supported Range |
|--------|----------------|
| Entity types | Unlimited (practical limit ~50 before UI becomes unwieldy) |
| Custom fields per entity | Unlimited (practical limit ~30 before forms become long) |
| Relationships | Unlimited bidirectional connections |
| Automation rules | Unlimited (evaluated async, background worker) |
| Concurrent workflows | Unlimited (each is an independent state machine) |
| Tenants | Multi-tenant ready (dormant `tenant_id` on every table) |

---

## 7. Hosting & Cost

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Hetzner VPS (CPX21) | 3 vCPU, 4 GB RAM, 80 GB SSD | ~Rs 700 |
| PostgreSQL | Self-hosted on same VPS (initial) | Rs 0 |
| S3-compatible storage | Hetzner Object Storage (1 TB) | ~Rs 400 |
| Domain | somadelights.in | ~Rs 70 (Rs 800/year) |
| Claude API | ~500 queries/month at Haiku rates | ~Rs 200 |
| WhatsApp Business API | Meta Cloud API free tier (1000 conversations/month) | Rs 0 |

**Total: Under Rs 1,500/month** until traffic or storage demands scaling.

---

## 8. References

| Document | Path |
|----------|------|
| Executive Summary | `docs/01-foundation/executive-summary.md` |
| Subscription Plans | `docs/03-product/subscription-plans.md` |
| Pricing Strategy | `docs/04-pricing-economics/pricing-strategy.md` |
| Unit Economics | `docs/04-pricing-economics/unit-economics.md` |
| Operations Model | `docs/05-operations/operations-model.md` |
| Partner Program | `docs/06-growth/partner-program.md` |
| Execution Roadmap | `docs/09-execution/execution-roadmap.md` |
| Tech Stack | `docs/09-execution/tech-stack.md` |
| Multi-lingual Strategy | `docs/09-execution/multi-lingual-strategy.md` |
| Design System | `docs/08-brand-content/design-system.md` |
