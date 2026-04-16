
import asyncio
import asyncpg
import sys

DB_CONFIG = {
    "user": "kcontrol_dev_admin",
    "password": "6f6eda3fa4f1a3f02d2156f572b6d053cb790cbecfca41a0",
    "database": "kcontrol_dev",
    "host": "ks-prod-cin-psql-02.postgres.database.azure.com",
    "port": 5432,
    "ssl": "require"
}

TABLES = [
    "37_fct_risk_questionnaires",
    "38_vrs_risk_questionnaire_versions",
    "39_lnk_risk_questionnaire_assignments",
    "41_fct_risk_questionnaire_responses"
]

EXPECTED_COLUMNS = {
    "37_fct_risk_questionnaires": [
        "id", "tenant_key", "questionnaire_code", "name", "description",
        "intended_scope", "current_status", "latest_version_number",
        "active_version_id", "is_active", "is_disabled", "is_deleted",
        "is_test", "is_system", "is_locked", "created_at", "updated_at",
        "created_by", "updated_by", "deleted_at", "deleted_by"
    ],
    "38_vrs_risk_questionnaire_versions": [
        "id", "questionnaire_id", "version_number", "version_status",
        "content_jsonb", "version_label", "change_notes", "published_at", 
        "published_by", "created_at", "updated_at", "created_by", "updated_by"
    ],
    "39_lnk_risk_questionnaire_assignments": [
        "id", "tenant_key", "assignment_scope", "org_id", "workspace_id",
        "questionnaire_version_id", "is_active", "created_at", "updated_at",
        "created_by", "updated_by"
    ],
    "41_fct_risk_questionnaire_responses": [
        "id", "tenant_key", "org_id", "workspace_id", "questionnaire_version_id",
        "response_status", "answers_jsonb", "completed_at", "completed_by",
        "created_at", "updated_at", "created_by", "updated_by"
    ]
}

async def verify():
    conn = None
    try:
        conn = await asyncio.wait_for(asyncpg.connect(**DB_CONFIG), timeout=10.0)
        
        all_match = True
        for table in TABLES:
            query = f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = '14_risk_registry' 
                  AND table_name = '{table}'
            """
            rows = await conn.fetch(query)
            actual_columns = [r['column_name'] for r in rows]
            
            expected = set(EXPECTED_COLUMNS[table])
            actual = set(actual_columns)

            missing_in_db = expected - actual
            extra_in_db = actual - expected

            if not missing_in_db and not extra_in_db:
                print(f"MATCH: {table}")
            else:
                all_match = False
                print(f"MISMATCH: {table}")
                if missing_in_db:
                    print(f"  Missing in DB: {sorted(list(missing_in_db))}")
                if extra_in_db:
                    print(f"  Extra in DB: {sorted(list(extra_in_db))}")

        if all_match:
            print("\nSUCCESS: All scripts match DB exactly.")
        else:
            print("\nFAILURE: Mismatches remain.")

    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
