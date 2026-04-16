-- Add external_audit to assessment types
DO $$ 
BEGIN
  INSERT INTO "09_assessments"."02_dim_assessment_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
  VALUES
      (gen_random_uuid(), 'external_audit', 'External Audit', 'Audit performed by an external party', 6, TRUE, NOW(), NOW())
  ON CONFLICT (code) DO NOTHING;
END $$;
