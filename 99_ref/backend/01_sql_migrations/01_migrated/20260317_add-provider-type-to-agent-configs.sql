-- Add provider_type to agent configs table
-- Supports: openai, anthropic, azure_openai, openai_compatible (default)
-- openai_compatible covers any base URL (Ollama, Together, Groq, custom endpoints)

ALTER TABLE "20_ai"."32_fct_agent_configs"
    ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50) NOT NULL DEFAULT 'openai_compatible'
    CHECK (provider_type IN ('openai', 'anthropic', 'azure_openai', 'openai_compatible'));

-- Seed a global default config for grc_assistant pointing to kreesalis LLM gateway
-- Uses INSERT ... ON CONFLICT DO NOTHING so it's safe to re-run
-- api_key_encrypted is NULL here — set via the admin UI after deploy
INSERT INTO "20_ai"."32_fct_agent_configs"
    (tenant_key, agent_type_code, org_id, provider_type, provider_base_url,
     api_key_encrypted, model_id, temperature, max_tokens, is_active)
VALUES
    ('system', 'grc_assistant', NULL, 'openai_compatible',
     'https://llm.kreesalis.com/v1',
     NULL, 'gpt-5.3-chat', 0.30, 4096, TRUE)
ON CONFLICT (agent_type_code, COALESCE(org_id::text, ''))
DO NOTHING;

-- Seed a global default config for copilot (session naming + general chat)
INSERT INTO "20_ai"."32_fct_agent_configs"
    (tenant_key, agent_type_code, org_id, provider_type, provider_base_url,
     api_key_encrypted, model_id, temperature, max_tokens, is_active)
VALUES
    ('system', 'copilot', NULL, 'openai_compatible',
     'https://llm.kreesalis.com/v1',
     NULL, 'gpt-5.3-chat', 0.30, 1024, TRUE)
ON CONFLICT (agent_type_code, COALESCE(org_id::text, ''))
DO NOTHING;
