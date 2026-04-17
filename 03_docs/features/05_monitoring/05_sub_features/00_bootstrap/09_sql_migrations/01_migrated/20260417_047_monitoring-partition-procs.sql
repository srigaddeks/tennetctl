-- UP ====
-- 13-07 Task 3 — Partition manager procs (create-ahead + drop-behind).

-- Ensure daily partitions exist from today to today + days_ahead for a partitioned parent.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_ensure_partitions(
    parent_name TEXT,
    days_ahead  INT
)
RETURNS INT AS $$
DECLARE
    d          DATE := CURRENT_DATE;
    end_d      DATE := CURRENT_DATE + days_ahead;
    p_name     TEXT;
    p_exists   BOOLEAN;
    created    INT  := 0;
    schema_nm  TEXT := '05_monitoring';
BEGIN
    WHILE d <= end_d LOOP
        p_name := parent_name || '_p' || to_char(d, 'YYYYMMDD');
        SELECT EXISTS (
            SELECT 1 FROM pg_class c
              JOIN pg_namespace n ON n.oid = c.relnamespace
             WHERE n.nspname = schema_nm
               AND c.relname = p_name
        ) INTO p_exists;
        IF NOT p_exists THEN
            EXECUTE format(
                'CREATE TABLE %I.%I PARTITION OF %I.%I FOR VALUES FROM (%L) TO (%L)',
                schema_nm, p_name, schema_nm, parent_name,
                d::text || ' 00:00:00',
                (d + 1)::text || ' 00:00:00'
            );
            created := created + 1;
        END IF;
        d := d + 1;
    END LOOP;
    RETURN created;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_ensure_partitions(TEXT, INT) IS 'Ensure daily partitions exist today through today+days_ahead for the given parent table.';

-- Drop partitions older than CURRENT_DATE - days_to_keep.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_drop_old_partitions(
    parent_name  TEXT,
    days_to_keep INT
)
RETURNS INT AS $$
DECLARE
    cutoff     DATE := CURRENT_DATE - days_to_keep;
    r          RECORD;
    dropped    INT  := 0;
    schema_nm  TEXT := '05_monitoring';
    suffix     TEXT;
    part_date  DATE;
BEGIN
    FOR r IN
        SELECT c.relname
          FROM pg_class c
          JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = schema_nm
           AND c.relkind = 'r'
           AND c.relname LIKE parent_name || '\_p%' ESCAPE '\'
    LOOP
        suffix := substring(r.relname FROM length(parent_name || '_p') + 1);
        IF suffix ~ '^[0-9]{8}$' THEN
            part_date := to_date(suffix, 'YYYYMMDD');
            IF part_date < cutoff THEN
                EXECUTE format('DROP TABLE %I.%I', schema_nm, r.relname);
                dropped := dropped + 1;
            END IF;
        END IF;
    END LOOP;
    RETURN dropped;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_drop_old_partitions(TEXT, INT) IS 'Drop daily partitions older than CURRENT_DATE - days_to_keep for the given parent table.';

-- Drive ensure + drop across every active retention policy; skips tables that don't exist yet.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_partition_manager()
RETURNS TABLE(table_name TEXT, created INT, dropped INT, days_to_keep SMALLINT) AS $$
DECLARE
    r       RECORD;
    c       INT;
    d       INT;
    exists_ BOOLEAN;
BEGIN
    FOR r IN
        SELECT rp.table_name AS t, rp.days_to_keep AS k
          FROM "05_monitoring"."10_fct_monitoring_retention_policies" rp
         WHERE rp.is_active = TRUE
           AND rp.deleted_at IS NULL
    LOOP
        SELECT EXISTS (
            SELECT 1 FROM pg_class pc
              JOIN pg_namespace pn ON pn.oid = pc.relnamespace
             WHERE pn.nspname = '05_monitoring'
               AND pc.relname = r.t
        ) INTO exists_;
        IF NOT exists_ THEN
            table_name   := r.t;
            created      := 0;
            dropped      := 0;
            days_to_keep := r.k;
            RETURN NEXT;
            CONTINUE;
        END IF;
        c := "05_monitoring".monitoring_ensure_partitions(r.t, 7);
        d := "05_monitoring".monitoring_drop_old_partitions(r.t, r.k);
        table_name   := r.t;
        created      := c;
        dropped      := d;
        days_to_keep := r.k;
        RETURN NEXT;
    END LOOP;
    RETURN;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_partition_manager() IS 'Drive create-ahead + drop-behind for every active retention policy. Returns per-table summary.';

-- DOWN ====
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_partition_manager();
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_drop_old_partitions(TEXT, INT);
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_ensure_partitions(TEXT, INT);
