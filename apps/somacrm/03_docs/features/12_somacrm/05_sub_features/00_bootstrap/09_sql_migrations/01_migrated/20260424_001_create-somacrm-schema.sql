-- UP ====
CREATE SCHEMA IF NOT EXISTS "12_somacrm";
SET search_path TO "12_somacrm";

-- Dim tables (lookup enums)
CREATE TABLE "12_somacrm".dim_contact_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP
);

CREATE TABLE "12_somacrm".dim_lead_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP
);

CREATE TABLE "12_somacrm".dim_deal_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP
);

CREATE TABLE "12_somacrm".dim_activity_types (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    deprecated_at TIMESTAMP
);

CREATE TABLE "12_somacrm".dim_activity_statuses (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP
);

CREATE TABLE "12_somacrm".dim_address_types (
    id SMALLINT PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    label VARCHAR(100) NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP
);

-- Entity tables
-- Contacts (people)
CREATE TABLE "12_somacrm".fct_contacts (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36),
    first_name VARCHAR(200) NOT NULL,
    last_name VARCHAR(200),
    email VARCHAR(500),
    phone VARCHAR(100),
    mobile VARCHAR(100),
    job_title VARCHAR(200),
    company_name VARCHAR(200),
    website VARCHAR(500),
    linkedin_url VARCHAR(500),
    twitter_handle VARCHAR(200),
    lead_source VARCHAR(200),
    status_id SMALLINT NOT NULL DEFAULT 1 REFERENCES "12_somacrm".dim_contact_statuses(id),
    notes_count INT NOT NULL DEFAULT 0,
    activities_count INT NOT NULL DEFAULT 0,
    deals_count INT NOT NULL DEFAULT 0,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_contacts_tenant_email UNIQUE (tenant_id, email)
);

-- Organizations (companies/accounts)
CREATE TABLE "12_somacrm".fct_organizations (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(500) NOT NULL,
    slug VARCHAR(200) NOT NULL,
    industry VARCHAR(200),
    website VARCHAR(500),
    phone VARCHAR(100),
    email VARCHAR(500),
    employee_count INT,
    annual_revenue DECIMAL(20,4),
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_organizations_tenant_slug UNIQUE (tenant_id, slug)
);

-- Addresses (polymorphic — contact or organization)
CREATE TABLE "12_somacrm".fct_addresses (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('contact', 'organization')),
    entity_id VARCHAR(36) NOT NULL,
    address_type_id SMALLINT NOT NULL REFERENCES "12_somacrm".dim_address_types(id),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    street VARCHAR(500),
    city VARCHAR(200),
    state VARCHAR(200),
    country VARCHAR(200),
    postal_code VARCHAR(50),
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Leads (prospects)
CREATE TABLE "12_somacrm".fct_leads (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    title VARCHAR(500) NOT NULL,
    contact_id VARCHAR(36),
    organization_id VARCHAR(36),
    first_name VARCHAR(200),
    last_name VARCHAR(200),
    email VARCHAR(500),
    phone VARCHAR(100),
    company VARCHAR(200),
    lead_source VARCHAR(200),
    status_id SMALLINT NOT NULL DEFAULT 1 REFERENCES "12_somacrm".dim_lead_statuses(id),
    score INT NOT NULL DEFAULT 0 CHECK (score >= 0 AND score <= 100),
    assigned_to VARCHAR(36),
    converted_deal_id VARCHAR(36),
    converted_at TIMESTAMP,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline stages
CREATE TABLE "12_somacrm".fct_pipeline_stages (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(200) NOT NULL,
    order_position INT NOT NULL DEFAULT 0,
    probability_pct INT NOT NULL DEFAULT 0 CHECK (probability_pct >= 0 AND probability_pct <= 100),
    color VARCHAR(20) NOT NULL DEFAULT '#6366f1',
    is_won BOOLEAN NOT NULL DEFAULT FALSE,
    is_lost BOOLEAN NOT NULL DEFAULT FALSE,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_pipeline_stages_tenant_name UNIQUE (tenant_id, name)
);

-- Deals (opportunities)
CREATE TABLE "12_somacrm".fct_deals (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    title VARCHAR(500) NOT NULL,
    contact_id VARCHAR(36),
    organization_id VARCHAR(36),
    stage_id VARCHAR(36) REFERENCES "12_somacrm".fct_pipeline_stages(id),
    status_id SMALLINT NOT NULL DEFAULT 1 REFERENCES "12_somacrm".dim_deal_statuses(id),
    value DECIMAL(20,4),
    currency VARCHAR(10) NOT NULL DEFAULT 'INR',
    expected_close_date DATE,
    actual_close_date DATE,
    probability_pct INT CHECK (probability_pct >= 0 AND probability_pct <= 100),
    assigned_to VARCHAR(36),
    description TEXT,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Activities (tasks, calls, emails, meetings)
CREATE TABLE "12_somacrm".fct_activities (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    activity_type_id SMALLINT NOT NULL REFERENCES "12_somacrm".dim_activity_types(id),
    status_id SMALLINT NOT NULL DEFAULT 1 REFERENCES "12_somacrm".dim_activity_statuses(id),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_minutes INT,
    entity_type VARCHAR(50) CHECK (entity_type IN ('contact', 'organization', 'lead', 'deal')),
    entity_id VARCHAR(36),
    assigned_to VARCHAR(36),
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Notes (on any entity)
CREATE TABLE "12_somacrm".fct_notes (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('contact', 'organization', 'lead', 'deal')),
    entity_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
    properties JSONB NOT NULL DEFAULT '{}',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tags
CREATE TABLE "12_somacrm".fct_tags (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20) NOT NULL DEFAULT '#6366f1',
    deleted_at TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_tags_tenant_name UNIQUE (tenant_id, name)
);

-- Entity-tag links
CREATE TABLE "12_somacrm".lnk_entity_tags (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    entity_type VARCHAR(50) NOT NULL CHECK (entity_type IN ('contact', 'organization', 'lead', 'deal')),
    entity_id VARCHAR(36) NOT NULL,
    tag_id VARCHAR(36) NOT NULL REFERENCES "12_somacrm".fct_tags(id),
    created_by VARCHAR(36),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_entity_tags UNIQUE (entity_type, entity_id, tag_id)
);

-- ── Indexes ─────────────────────────────────────────────────────────────
CREATE INDEX idx_contacts_tenant ON "12_somacrm".fct_contacts(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_contacts_org ON "12_somacrm".fct_contacts(organization_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_tenant ON "12_somacrm".fct_organizations(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_addresses_entity ON "12_somacrm".fct_addresses(entity_type, entity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_tenant ON "12_somacrm".fct_leads(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_status ON "12_somacrm".fct_leads(tenant_id, status_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_pipeline_stages_tenant ON "12_somacrm".fct_pipeline_stages(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_deals_tenant ON "12_somacrm".fct_deals(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_deals_stage ON "12_somacrm".fct_deals(tenant_id, stage_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_activities_tenant ON "12_somacrm".fct_activities(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_activities_entity ON "12_somacrm".fct_activities(entity_type, entity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_notes_entity ON "12_somacrm".fct_notes(entity_type, entity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_entity_tags_entity ON "12_somacrm".lnk_entity_tags(entity_type, entity_id);

-- ── Views ──────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW "12_somacrm".v_contacts AS
SELECT
    c.id, c.tenant_id, c.organization_id,
    o.name AS organization_name,
    c.first_name, c.last_name,
    CONCAT_WS(' ', c.first_name, c.last_name) AS full_name,
    c.email, c.phone, c.mobile,
    c.job_title, c.company_name, c.website,
    c.linkedin_url, c.twitter_handle, c.lead_source,
    c.status_id, s.code AS status,
    c.notes_count, c.activities_count, c.deals_count,
    c.properties, c.deleted_at, c.created_by, c.updated_by,
    c.created_at, c.updated_at
FROM "12_somacrm".fct_contacts c
LEFT JOIN "12_somacrm".dim_contact_statuses s ON s.id = c.status_id
LEFT JOIN "12_somacrm".fct_organizations o ON o.id = c.organization_id AND o.deleted_at IS NULL;

CREATE OR REPLACE VIEW "12_somacrm".v_organizations AS
SELECT
    o.id, o.tenant_id, o.name, o.slug,
    o.industry, o.website, o.phone, o.email,
    o.employee_count, o.annual_revenue, o.description,
    o.properties, o.deleted_at, o.created_by, o.updated_by,
    o.created_at, o.updated_at,
    COUNT(DISTINCT c.id) FILTER (WHERE c.deleted_at IS NULL) AS contact_count,
    COUNT(DISTINCT d.id) FILTER (WHERE d.deleted_at IS NULL) AS deal_count
FROM "12_somacrm".fct_organizations o
LEFT JOIN "12_somacrm".fct_contacts c ON c.organization_id = o.id
LEFT JOIN "12_somacrm".fct_deals d ON d.organization_id = o.id
GROUP BY o.id, o.tenant_id, o.name, o.slug, o.industry, o.website,
         o.phone, o.email, o.employee_count, o.annual_revenue, o.description,
         o.properties, o.deleted_at, o.created_by, o.updated_by, o.created_at, o.updated_at;

CREATE OR REPLACE VIEW "12_somacrm".v_addresses AS
SELECT
    a.id, a.tenant_id, a.entity_type, a.entity_id,
    a.address_type_id, t.code AS address_type,
    a.is_primary, a.street, a.city, a.state,
    a.country, a.postal_code,
    TRIM(CONCAT_WS(', ',
        NULLIF(TRIM(COALESCE(a.street, '')), ''),
        NULLIF(TRIM(COALESCE(a.city, '')), ''),
        NULLIF(TRIM(COALESCE(a.state, '')), ''),
        NULLIF(TRIM(COALESCE(a.country, '')), ''),
        NULLIF(TRIM(COALESCE(a.postal_code, '')), '')
    )) AS full_address,
    a.properties, a.deleted_at, a.created_by, a.updated_by,
    a.created_at, a.updated_at
FROM "12_somacrm".fct_addresses a
JOIN "12_somacrm".dim_address_types t ON t.id = a.address_type_id;

CREATE OR REPLACE VIEW "12_somacrm".v_leads AS
SELECT
    l.id, l.tenant_id, l.title,
    l.contact_id, l.organization_id,
    CONCAT_WS(' ', c.first_name, c.last_name) AS contact_name,
    o.name AS organization_name,
    l.first_name, l.last_name,
    COALESCE(CONCAT_WS(' ', l.first_name, l.last_name), CONCAT_WS(' ', c.first_name, c.last_name)) AS full_name,
    l.email, l.phone, l.company,
    l.lead_source, l.status_id, s.code AS status,
    l.score, l.assigned_to, l.converted_deal_id, l.converted_at,
    l.properties, l.deleted_at, l.created_by, l.updated_by,
    l.created_at, l.updated_at
FROM "12_somacrm".fct_leads l
LEFT JOIN "12_somacrm".dim_lead_statuses s ON s.id = l.status_id
LEFT JOIN "12_somacrm".fct_contacts c ON c.id = l.contact_id AND c.deleted_at IS NULL
LEFT JOIN "12_somacrm".fct_organizations o ON o.id = l.organization_id AND o.deleted_at IS NULL;

CREATE OR REPLACE VIEW "12_somacrm".v_pipeline_stages AS
SELECT
    ps.id, ps.tenant_id, ps.name, ps.order_position,
    ps.probability_pct, ps.color, ps.is_won, ps.is_lost,
    ps.properties, ps.deleted_at, ps.created_by, ps.updated_by,
    ps.created_at, ps.updated_at,
    COUNT(d.id) FILTER (WHERE d.deleted_at IS NULL AND d.stage_id = ps.id) AS deals_count
FROM "12_somacrm".fct_pipeline_stages ps
LEFT JOIN "12_somacrm".fct_deals d ON d.stage_id = ps.id
GROUP BY ps.id, ps.tenant_id, ps.name, ps.order_position, ps.probability_pct,
         ps.color, ps.is_won, ps.is_lost, ps.properties, ps.deleted_at,
         ps.created_by, ps.updated_by, ps.created_at, ps.updated_at;

CREATE OR REPLACE VIEW "12_somacrm".v_deals AS
SELECT
    d.id, d.tenant_id, d.title,
    d.contact_id, d.organization_id,
    CONCAT_WS(' ', c.first_name, c.last_name) AS contact_name,
    o.name AS organization_name,
    d.stage_id, ps.name AS stage_name, ps.color AS stage_color, ps.order_position AS stage_order,
    d.status_id, ds.code AS status,
    d.value, d.currency, d.expected_close_date, d.actual_close_date,
    d.probability_pct, d.assigned_to, d.description,
    d.properties, d.deleted_at, d.created_by, d.updated_by,
    d.created_at, d.updated_at
FROM "12_somacrm".fct_deals d
LEFT JOIN "12_somacrm".dim_deal_statuses ds ON ds.id = d.status_id
LEFT JOIN "12_somacrm".fct_contacts c ON c.id = d.contact_id AND c.deleted_at IS NULL
LEFT JOIN "12_somacrm".fct_organizations o ON o.id = d.organization_id AND o.deleted_at IS NULL
LEFT JOIN "12_somacrm".fct_pipeline_stages ps ON ps.id = d.stage_id AND ps.deleted_at IS NULL;

CREATE OR REPLACE VIEW "12_somacrm".v_activities AS
SELECT
    a.id, a.tenant_id,
    a.activity_type_id, at2.code AS activity_type, at2.label AS activity_type_label, at2.icon AS activity_type_icon,
    a.status_id, ast.code AS status,
    a.title, a.description, a.due_at, a.completed_at, a.duration_minutes,
    a.entity_type, a.entity_id, a.assigned_to,
    a.properties, a.deleted_at, a.created_by, a.updated_by,
    a.created_at, a.updated_at
FROM "12_somacrm".fct_activities a
JOIN "12_somacrm".dim_activity_types at2 ON at2.id = a.activity_type_id
JOIN "12_somacrm".dim_activity_statuses ast ON ast.id = a.status_id;

CREATE OR REPLACE VIEW "12_somacrm".v_notes AS
SELECT
    n.id, n.tenant_id, n.entity_type, n.entity_id,
    n.content, n.is_pinned,
    n.properties, n.deleted_at, n.created_by, n.updated_by,
    n.created_at, n.updated_at
FROM "12_somacrm".fct_notes n;

CREATE OR REPLACE VIEW "12_somacrm".v_tags AS
SELECT
    t.id, t.tenant_id, t.name, t.color,
    t.deleted_at, t.created_by, t.updated_by, t.created_at, t.updated_at
FROM "12_somacrm".fct_tags t;

-- DOWN ====
DROP VIEW IF EXISTS "12_somacrm".v_tags;
DROP VIEW IF EXISTS "12_somacrm".v_notes;
DROP VIEW IF EXISTS "12_somacrm".v_activities;
DROP VIEW IF EXISTS "12_somacrm".v_deals;
DROP VIEW IF EXISTS "12_somacrm".v_pipeline_stages;
DROP VIEW IF EXISTS "12_somacrm".v_leads;
DROP VIEW IF EXISTS "12_somacrm".v_addresses;
DROP VIEW IF EXISTS "12_somacrm".v_organizations;
DROP VIEW IF EXISTS "12_somacrm".v_contacts;
DROP TABLE IF EXISTS "12_somacrm".lnk_entity_tags;
DROP TABLE IF EXISTS "12_somacrm".fct_tags;
DROP TABLE IF EXISTS "12_somacrm".fct_notes;
DROP TABLE IF EXISTS "12_somacrm".fct_activities;
DROP TABLE IF EXISTS "12_somacrm".fct_deals;
DROP TABLE IF EXISTS "12_somacrm".fct_pipeline_stages;
DROP TABLE IF EXISTS "12_somacrm".fct_leads;
DROP TABLE IF EXISTS "12_somacrm".fct_addresses;
DROP TABLE IF EXISTS "12_somacrm".fct_organizations;
DROP TABLE IF EXISTS "12_somacrm".fct_contacts;
DROP TABLE IF EXISTS "12_somacrm".dim_address_types;
DROP TABLE IF EXISTS "12_somacrm".dim_activity_statuses;
DROP TABLE IF EXISTS "12_somacrm".dim_activity_types;
DROP TABLE IF EXISTS "12_somacrm".dim_deal_statuses;
DROP TABLE IF EXISTS "12_somacrm".dim_lead_statuses;
DROP TABLE IF EXISTS "12_somacrm".dim_contact_statuses;
DROP SCHEMA IF EXISTS "12_somacrm";
