-- UP ====

-- Relax updated_by NOT NULL on solsocial fct_* tables. The audit/update
-- plumbing isn't threaded through every code path yet; until it is, UPDATE
-- statements can leave updated_by unchanged, and INSERTs should default to
-- the same actor as created_by rather than the repo needing to pass both.
-- A later migration will tighten this once every service sets updated_by
-- explicitly.

ALTER TABLE "10_solsocial"."10_fct_channels" ALTER COLUMN updated_by DROP NOT NULL;
ALTER TABLE "10_solsocial"."11_fct_posts"    ALTER COLUMN updated_by DROP NOT NULL;
ALTER TABLE "10_solsocial"."12_fct_queues"   ALTER COLUMN updated_by DROP NOT NULL;
ALTER TABLE "10_solsocial"."13_fct_ideas"    ALTER COLUMN updated_by DROP NOT NULL;

-- DOWN ====

ALTER TABLE "10_solsocial"."13_fct_ideas"    ALTER COLUMN updated_by SET NOT NULL;
ALTER TABLE "10_solsocial"."12_fct_queues"   ALTER COLUMN updated_by SET NOT NULL;
ALTER TABLE "10_solsocial"."11_fct_posts"    ALTER COLUMN updated_by SET NOT NULL;
ALTER TABLE "10_solsocial"."10_fct_channels" ALTER COLUMN updated_by SET NOT NULL;
