#!/usr/bin/env bash
# =============================================================================
# seed_environment.sh — Plug-and-play seed data for staging/prod
#
# Extracts all seed data from dev, generates an idempotent SQL migration,
# and optionally applies it to a target environment.
#
# Usage:
#   # Step 1: Extract seeds from dev → generate migration file
#   ./seed_environment.sh extract
#
#   # Step 2: Apply to staging
#   ./seed_environment.sh apply staging
#
#   # Step 3: Apply to prod
#   ./seed_environment.sh apply prod
#
#   # Verify seed data in an environment
#   ./seed_environment.sh verify staging
#   ./seed_environment.sh verify prod
#
#   # One-shot: extract + apply to staging
#   ./seed_environment.sh sync staging
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MIGRATIONS_DIR="$BACKEND_DIR/01_sql_migrations/01_migrated"
SEED_OUTPUT="$BACKEND_DIR/01_sql_migrations/02_inprogress/$(date +%Y%m%d)_seed-full-environment.sql"
PYTHON="${PYTHON:-python3}"

# ── Load env files ───────────────────────────────────────────────────────────

load_env() {
    local env_file="$1"
    if [[ -f "$env_file" ]]; then
        set -a
        # shellcheck source=/dev/null
        source "$env_file"
        set +a
    fi
}

# ── DB connection helpers ────────────────────────────────────────────────────

get_dev_connection() {
    load_env "$BACKEND_DIR/.env"
    echo "host=$DB_HOST port=$DB_PORT dbname=$DATABASE_NAME user=$ADMIN_USER"
    export PGPASSWORD="$ADMIN_PASSWORD"
}

get_staging_connection() {
    load_env "$BACKEND_DIR/.env.staging"
    echo "host=${STAGING_DB_HOST:?Set STAGING_DB_HOST} port=${STAGING_DB_PORT:-5432} dbname=${STAGING_DATABASE_NAME:?Set STAGING_DATABASE_NAME} user=${STAGING_ADMIN_USER:?Set STAGING_ADMIN_USER}"
    export PGPASSWORD="${STAGING_ADMIN_PASSWORD:?Set STAGING_ADMIN_PASSWORD}"
}

get_prod_connection() {
    load_env "$BACKEND_DIR/.env.prod"
    echo "host=${PROD_DB_HOST:?Set PROD_DB_HOST} port=${PROD_DB_PORT:-5432} dbname=${PROD_DATABASE_NAME:?Set PROD_DATABASE_NAME} user=${PROD_ADMIN_USER:?Set PROD_ADMIN_USER}"
    export PGPASSWORD="${PROD_ADMIN_PASSWORD:?Set PROD_ADMIN_PASSWORD}"
}

run_psql() {
    local conn_string="$1"
    shift
    psql "$conn_string" "$@"
}

# ── Commands ─────────────────────────────────────────────────────────────────

cmd_extract() {
    echo "=== Extracting seed data from dev ==="
    cd "$BACKEND_DIR"

    # Use extract_seeds.py to dump all categories
    $PYTHON 91_scripts/extract_seeds.py --all --output "$SEED_OUTPUT"

    echo ""
    echo "Seed SQL written to: $SEED_OUTPUT"
    echo "Lines: $(wc -l < "$SEED_OUTPUT")"
    echo ""
    echo "Next steps:"
    echo "  1. Review the file: less $SEED_OUTPUT"
    echo "  2. Apply to staging: $0 apply staging"
    echo "  3. Apply to prod:    $0 apply prod"
}

cmd_apply() {
    local target="${1:?Usage: $0 apply <staging|prod>}"
    local conn

    case "$target" in
        staging) conn=$(get_staging_connection) ;;
        prod)    conn=$(get_prod_connection) ;;
        dev)     conn=$(get_dev_connection) ;;
        *)       echo "Unknown target: $target (use staging or prod)"; exit 1 ;;
    esac

    # Determine what to apply
    if [[ -f "$SEED_OUTPUT" ]]; then
        local sql_file="$SEED_OUTPUT"
    else
        echo "No seed file found at $SEED_OUTPUT"
        echo "Run '$0 extract' first, or the migration system will handle it."
        exit 1
    fi

    echo "=== Applying seeds to $target ==="
    echo "File: $sql_file"
    echo "Target: $conn"
    echo ""
    read -rp "Continue? [y/N] " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

    psql "$conn" -f "$sql_file" 2>&1
    echo ""
    echo "=== Done. Run '$0 verify $target' to check. ==="
}

cmd_verify() {
    local target="${1:?Usage: $0 verify <staging|prod|dev>}"
    local conn

    case "$target" in
        staging) conn=$(get_staging_connection) ;;
        prod)    conn=$(get_prod_connection) ;;
        dev)     conn=$(get_dev_connection) ;;
        *)       echo "Unknown target: $target"; exit 1 ;;
    esac

    echo "=== Seed data verification: $target ==="
    echo ""

    psql "$conn" -c "
    -- Feature flags
    SELECT 'feature_flags' AS entity, COUNT(*) AS count
    FROM \"03_auth_manage\".\"14_dim_feature_flags\"
    UNION ALL
    -- Feature permissions
    SELECT 'feature_permissions', COUNT(*)
    FROM \"03_auth_manage\".\"15_dim_feature_permissions\"
    UNION ALL
    -- System roles
    SELECT 'system_roles', COUNT(*)
    FROM \"03_auth_manage\".\"16_fct_roles\" WHERE is_system = TRUE
    UNION ALL
    -- System groups
    SELECT 'system_groups', COUNT(*)
    FROM \"03_auth_manage\".\"17_fct_user_groups\" WHERE is_system = TRUE
    UNION ALL
    -- Role-permission links
    SELECT 'role_permissions', COUNT(*)
    FROM \"03_auth_manage\".\"20_lnk_role_feature_permissions\"
    UNION ALL
    -- Portal views
    SELECT 'portal_views', COUNT(*)
    FROM \"03_auth_manage\".\"50_dim_portal_views\"
    UNION ALL
    -- Notification templates
    SELECT 'notification_templates', COUNT(*)
    FROM \"03_notifications\".\"10_fct_templates\" WHERE is_deleted = FALSE AND is_test = FALSE
    UNION ALL
    -- Template versions
    SELECT 'template_versions', COUNT(*)
    FROM \"03_notifications\".\"14_dtl_template_versions\"
    UNION ALL
    -- Notification rules
    SELECT 'notification_rules', COUNT(*)
    FROM \"03_notifications\".\"11_fct_notification_rules\" WHERE is_deleted = FALSE
    UNION ALL
    -- Notification types
    SELECT 'notification_types', COUNT(*)
    FROM \"03_notifications\".\"04_dim_notification_types\"
    UNION ALL
    -- License profiles
    SELECT 'license_profiles', COUNT(*)
    FROM \"03_auth_manage\".\"37_fct_license_profiles\"
    UNION ALL
    -- GRC dims
    SELECT 'grc_framework_types', COUNT(*)
    FROM \"05_grc_library\".\"02_dim_framework_types\"
    UNION ALL
    -- Variable queries
    SELECT 'variable_queries', COUNT(*)
    FROM \"03_notifications\".\"31_fct_variable_queries\"
    ORDER BY entity;
    "
}

cmd_sync() {
    local target="${1:?Usage: $0 sync <staging|prod>}"
    cmd_extract
    cmd_apply "$target"
}

cmd_migrate() {
    local target="${1:?Usage: $0 migrate <staging|prod>}"
    local conn

    case "$target" in
        staging) conn=$(get_staging_connection) ;;
        prod)    conn=$(get_prod_connection) ;;
        *)       echo "Unknown target: $target"; exit 1 ;;
    esac

    echo "=== Running migrations on $target ==="
    cd "$BACKEND_DIR"

    case "$target" in
        staging)
            export DB_HOST="$STAGING_DB_HOST" DB_PORT="${STAGING_DB_PORT:-5432}"
            export DATABASE_NAME="$STAGING_DATABASE_NAME"
            export ADMIN_USER="$STAGING_ADMIN_USER" ADMIN_PASSWORD="$STAGING_ADMIN_PASSWORD"
            ;;
        prod)
            export DB_HOST="$PROD_DB_HOST" DB_PORT="${PROD_DB_PORT:-5432}"
            export DATABASE_NAME="$PROD_DATABASE_NAME"
            export ADMIN_USER="$PROD_ADMIN_USER" ADMIN_PASSWORD="$PROD_ADMIN_PASSWORD"
            ;;
    esac

    $PYTHON -m backend.91_scripts.apply_migrations "$@"
}

# ── Main ─────────────────────────────────────────────────────────────────────

cmd="${1:-help}"
shift || true

case "$cmd" in
    extract)   cmd_extract ;;
    apply)     cmd_apply "$@" ;;
    verify)    cmd_verify "$@" ;;
    sync)      cmd_sync "$@" ;;
    migrate)   cmd_migrate "$@" ;;
    help|--help|-h)
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  extract          Extract seed data from dev into a migration file"
        echo "  apply <env>      Apply seed migration to staging or prod"
        echo "  verify <env>     Verify seed data counts in an environment"
        echo "  sync <env>       Extract + apply in one step"
        echo "  migrate <env>    Run migration system against staging or prod"
        echo ""
        echo "Environments: dev, staging, prod"
        echo ""
        echo "Setup:"
        echo "  Create .env.staging and .env.prod in backend/ with:"
        echo "    STAGING_DB_HOST, STAGING_DB_PORT, STAGING_DATABASE_NAME"
        echo "    STAGING_ADMIN_USER, STAGING_ADMIN_PASSWORD"
        echo "    (same pattern for PROD_*)"
        ;;
    *)
        echo "Unknown command: $cmd"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac
