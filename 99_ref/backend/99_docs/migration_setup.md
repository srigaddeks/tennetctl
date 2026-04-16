# Database Migration Setup

This document explains how the SQL migration system works and how it is executed during development, CI, Docker deployments, and Kubernetes environments with Horizontal Pod Autoscaling (HPA).

The migration runner is implemented in:

backend/01_core/database.py  
backend/91_scripts/apply_migrations.py


------------------------------------------------------------
Migration Philosophy
------------------------------------------------------------

The system follows a simple deterministic migration model similar to tools like Flyway or Prisma.

Key principles:

• Migrations are immutable  
• Files run in deterministic filename order  
• Every migration runs exactly once  
• Migration execution is safe under concurrent startup conditions  
• The application never requires manual database schema updates


------------------------------------------------------------
Migration Directory Structure
------------------------------------------------------------

Migrations live in:

backend/01_sql_migrations/

Structure:

backend/01_sql_migrations/
    01_migrated/
    02_inprogress/

Example migration:

20260313_create-auth-core.yaml

Migration naming rule:

YYYYMMDD_description.sql
YYYYMMDD_description.yaml


Example:

20260313_create_users_table.sql
20260314_add_index_users_email.sql


------------------------------------------------------------
Supported Migration Formats
------------------------------------------------------------

Two formats are supported.

SQL

Example:

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT NOT NULL
);

YAML

Example:

name: create-users
sql: |
  CREATE TABLE users (
      id UUID PRIMARY KEY,
      email TEXT NOT NULL
  );


YAML is useful when migrations need metadata.


------------------------------------------------------------
Running Migrations Manually
------------------------------------------------------------

Run migrations using the CLI script:

python backend/91_scripts/apply_migrations.py


Dry run preview:

python backend/91_scripts/apply_migrations.py --dry-run


Dry run prints migrations that would be executed without modifying the database.


------------------------------------------------------------
Migration Safety Mechanisms
------------------------------------------------------------

The migration system includes several protections.


Deterministic Ordering

Migrations are sorted by filename.


Filename Validation

Files must match this format:

^\d{8}_.+\.(sql|yaml)$


SQL Lint Warnings

Potentially dangerous statements trigger warnings:

DROP TABLE  
TRUNCATE  
DROP COLUMN  


PostgreSQL Advisory Lock

Before executing migrations the system acquires a database lock:

SELECT pg_advisory_lock(918273645)

This guarantees that only one process runs migrations even if many instances start simultaneously.

After completion:

SELECT pg_advisory_unlock(918273645)


------------------------------------------------------------
Docker Deployment Model
------------------------------------------------------------

In container environments migrations run during container startup.

Typical Docker command:

CMD ["sh", "-c", "python backend/91_scripts/apply_migrations.py && python backend/main.py"]


Startup sequence:

1. Container starts
2. Migration runner executes
3. Database schema is updated if needed
4. Application server starts


Because migrations are idempotent and protected by advisory locks, multiple containers can safely attempt to run migrations simultaneously.


------------------------------------------------------------
Kubernetes Deployment
------------------------------------------------------------

Two safe deployment patterns are supported.


Option 1 — Application Startup Migration

Each container runs migrations before starting the application.

Example container command:

python backend/91_scripts/apply_migrations.py && uvicorn backend.main:app


With HPA scaling multiple pods may start at the same time.

This is safe because the advisory lock ensures:

• Only one pod executes migrations  
• Other pods wait until migrations finish


Flow:

Pod A acquires lock → runs migrations  
Pod B waits for lock  
Pod A releases lock  
Pod B continues startup


Option 2 — Init Container (Recommended)

Kubernetes init containers run before application containers.

Example:

initContainers:
  - name: migrate
    image: backend-image
    command: ["python", "backend/91_scripts/apply_migrations.py"]


Application container starts only after migrations finish.

Advantages:

• guaranteed schema consistency  
• faster pod startup  
• clearer deployment lifecycle


------------------------------------------------------------
Horizontal Pod Autoscaling (HPA)
------------------------------------------------------------

When HPA scales the deployment:

1 pod → 5 pods


Multiple pods may start simultaneously.

Without protection this could cause migration conflicts.

The advisory lock prevents this.

Behavior:

Pod A obtains advisory lock  
Pod B,C,D,E wait  
Pod A completes migration  
Lock released  
Remaining pods continue startup


This guarantees that schema updates occur exactly once.


------------------------------------------------------------
CI Workflow
------------------------------------------------------------

CI pipelines should verify migrations before deployment.

Typical steps:

1. Start temporary PostgreSQL
2. Apply migrations
3. Run test suite


Example CI command:

python backend/91_scripts/apply_migrations.py


This ensures migrations are valid before reaching production.


------------------------------------------------------------
Development Workflow
------------------------------------------------------------

Developer workflow:

1. Create new migration file

Example:

20260401_add_user_last_login.sql


2. Run migrations

python backend/91_scripts/apply_migrations.py


3. Start backend


------------------------------------------------------------
Summary
------------------------------------------------------------

This migration system provides:

• deterministic schema updates  
• safe concurrent execution  
• Docker compatible startup  
• Kubernetes HPA safety  
• CI validation  
• SQL + YAML migration support  


The PostgreSQL advisory lock is the key mechanism that guarantees migration safety in distributed environments.