#!/usr/bin/env python3
"""
Seed LLM credentials for Evidence Checker agents.

This script MUST be run once after the migration SQL has been applied.
It encrypts the API key using the existing AES-256-GCM crypto module and
inserts/updates two agent config rows in 20_ai.32_fct_agent_configs.

Usage:
    python -m backend.20_ai.16_evidence_checker.seed_credentials

Environment variables required:
    DATABASE_URL        — asyncpg connection string
    AI_ENCRYPTION_KEY   — 32-byte base64 key (same as used by the rest of the AI module)

Credential defaults below match the Kreesalis internal LLM gateway.
Override via env vars if needed:
    EVIDENCE_LLM_BASE_URL    (default: https://llm.kreesalis.com/v1)
    EVIDENCE_LLM_API_KEY     (default: sk-3--kkIINWzkRG3tomxV5xw)
    EVIDENCE_LLM_MODEL       (default: gpt-5.3-chat)
    EVIDENCE_LLM_TENANT_KEY  (default: system)
"""

from __future__ import annotations

import asyncio
import os
import sys

# ── Credential defaults (from the Kreesalis LLM gateway) ────────────────────
_DEFAULT_BASE_URL  = "https://llm.kreesalis.com/v1"
_DEFAULT_API_KEY   = "sk-3--kkIINWzkRG3tomxV5xw"
_DEFAULT_MODEL     = "gpt-5.3-chat"
_DEFAULT_TENANT    = "system"


async def seed():
    import asyncpg
    _crypto_mod = __import__("importlib").import_module("backend.20_ai.12_agent_config.crypto")
    encrypt_value = _crypto_mod.encrypt_value
    parse_encryption_key = _crypto_mod.parse_encryption_key

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL env var not set", file=sys.stderr)
        sys.exit(1)

    enc_key_raw = os.environ.get("AI_ENCRYPTION_KEY")
    if not enc_key_raw:
        print("ERROR: AI_ENCRYPTION_KEY env var not set", file=sys.stderr)
        sys.exit(1)

    base_url   = os.environ.get("EVIDENCE_LLM_BASE_URL",   _DEFAULT_BASE_URL)
    api_key    = os.environ.get("EVIDENCE_LLM_API_KEY",    _DEFAULT_API_KEY)
    model_id   = os.environ.get("EVIDENCE_LLM_MODEL",      _DEFAULT_MODEL)
    tenant_key = os.environ.get("EVIDENCE_LLM_TENANT_KEY", _DEFAULT_TENANT)

    enc_key = parse_encryption_key(enc_key_raw)
    api_key_encrypted = encrypt_value(api_key, enc_key)

    conn = await asyncpg.connect(database_url)
    try:
        agent_types = ["evidence_lead", "evidence_checker_agent"]
        for agent_type_code in agent_types:
            # Upsert — if config exists update it, otherwise insert
            existing = await conn.fetchrow(
                """
                SELECT id FROM "20_ai"."32_fct_agent_configs"
                WHERE agent_type_code = $1 AND org_id IS NULL AND tenant_key = $2
                """,
                agent_type_code, tenant_key,
            )
            if existing:
                await conn.execute(
                    """
                    UPDATE "20_ai"."32_fct_agent_configs"
                    SET provider_type       = 'openai_compatible',
                        provider_base_url   = $1,
                        api_key_encrypted   = $2,
                        model_id            = $3,
                        temperature         = 1.0,
                        max_tokens          = 4096,
                        is_active           = TRUE,
                        updated_at          = NOW()
                    WHERE id = $4
                    """,
                    base_url, api_key_encrypted, model_id, existing["id"],
                )
                print(f"✓ Updated config for {agent_type_code} (id={existing['id']})")
            else:
                row = await conn.fetchrow(
                    """
                    INSERT INTO "20_ai"."32_fct_agent_configs"
                        (tenant_key, agent_type_code, org_id,
                         provider_type, provider_base_url, api_key_encrypted,
                         model_id, temperature, max_tokens, is_active)
                    VALUES ($1, $2, NULL, 'openai_compatible', $3, $4, $5, 1.0, 4096, TRUE)
                    RETURNING id::text
                    """,
                    tenant_key, agent_type_code, base_url, api_key_encrypted, model_id,
                )
                print(f"✓ Created config for {agent_type_code} (id={row['id']})")

        print(f"\n✓ Evidence checker LLM credentials seeded")
        print(f"  base_url  : {base_url}")
        print(f"  model     : {model_id}")
        print(f"  tenant    : {tenant_key}")
        print(f"  api_key   : {api_key[:8]}... (encrypted in DB)")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
