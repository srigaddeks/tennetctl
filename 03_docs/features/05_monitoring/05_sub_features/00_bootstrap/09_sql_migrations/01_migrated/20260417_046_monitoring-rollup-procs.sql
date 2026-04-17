-- UP ====
-- 13-07 Task 2 — Rollup procs + watermark tracking.
--
-- monitoring_rollup_1m: reads raw evt_monitoring_metric_points into _1m
-- monitoring_rollup_5m: rolls _1m into _5m
-- monitoring_rollup_1h: rolls _5m into _1h
-- All idempotent. Watermarks advisory.

CREATE TABLE IF NOT EXISTS "05_monitoring"."20_dtl_monitoring_rollup_watermarks" (
    table_name   TEXT        PRIMARY KEY,
    last_bucket  TIMESTAMP   NOT NULL,
    updated_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "05_monitoring"."20_dtl_monitoring_rollup_watermarks" IS 'Advisory high-water mark per rollup table — rollup procs read this and advance it.';

-- Seed watermarks far in the past so first run picks everything up.
INSERT INTO "05_monitoring"."20_dtl_monitoring_rollup_watermarks" (table_name, last_bucket)
VALUES
    ('70_evt_monitoring_metric_points_1m', TIMESTAMP '1970-01-01'),
    ('71_evt_monitoring_metric_points_5m', TIMESTAMP '1970-01-01'),
    ('72_evt_monitoring_metric_points_1h', TIMESTAMP '1970-01-01')
ON CONFLICT (table_name) DO NOTHING;

-- Element-wise SUM of BIGINT[] arrays, NULL-safe.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_histogram_array_sum(a BIGINT[], b BIGINT[])
RETURNS BIGINT[] AS $$
DECLARE
    la INT;
    lb INT;
    i INT;
    out BIGINT[];
BEGIN
    IF a IS NULL THEN RETURN b; END IF;
    IF b IS NULL THEN RETURN a; END IF;
    la := array_length(a, 1);
    lb := array_length(b, 1);
    IF la IS NULL THEN RETURN b; END IF;
    IF lb IS NULL THEN RETURN a; END IF;
    IF la <> lb THEN
        -- incompatible; return the longer one unchanged
        IF la >= lb THEN RETURN a; ELSE RETURN b; END IF;
    END IF;
    out := ARRAY[]::BIGINT[];
    FOR i IN 1..la LOOP
        out := array_append(out, COALESCE(a[i], 0) + COALESCE(b[i], 0));
    END LOOP;
    RETURN out;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 1-minute rollup from raw.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_rollup_1m(since TIMESTAMP DEFAULT NULL)
RETURNS INT AS $$
DECLARE
    start_ts TIMESTAMP;
    end_ts   TIMESTAMP := date_trunc('minute', CURRENT_TIMESTAMP - INTERVAL '10 seconds');
    rows_upserted INT;
BEGIN
    IF since IS NULL THEN
        SELECT last_bucket INTO start_ts
          FROM "05_monitoring"."20_dtl_monitoring_rollup_watermarks"
         WHERE table_name = '70_evt_monitoring_metric_points_1m';
        IF start_ts IS NULL THEN
            start_ts := TIMESTAMP '1970-01-01';
        END IF;
    ELSE
        start_ts := since;
    END IF;

    WITH src AS (
        SELECT
            metric_id,
            labels,
            resource_id,
            org_id,
            date_trunc('minute', recorded_at) AS bucket,
            value,
            histogram_counts,
            recorded_at
          FROM "05_monitoring"."61_evt_monitoring_metric_points"
         WHERE recorded_at >= start_ts
           AND recorded_at <  end_ts
    ),
    agg AS (
        SELECT
            metric_id,
            digest(labels::text, 'sha256') AS labels_hash,
            (array_agg(labels ORDER BY recorded_at DESC))[1] AS labels,
            resource_id,
            org_id,
            bucket,
            COUNT(*)::BIGINT                       AS count,
            SUM(value)::DOUBLE PRECISION           AS sum,
            MIN(value)::DOUBLE PRECISION           AS min,
            MAX(value)::DOUBLE PRECISION           AS max,
            (array_agg(value ORDER BY recorded_at DESC))[1]::DOUBLE PRECISION AS last
          FROM src cur
         GROUP BY metric_id, labels::text, resource_id, org_id, bucket
    )
    INSERT INTO "05_monitoring"."70_evt_monitoring_metric_points_1m"
        (metric_id, labels_hash, labels, resource_id, org_id, bucket,
         count, sum, min, max, last, histogram_counts)
    SELECT
        metric_id, labels_hash, labels, resource_id, org_id, bucket,
        count, sum, min, max, last,
        NULL::BIGINT[]  -- histogram aggregation done separately below
      FROM agg
    ON CONFLICT (metric_id, labels_hash, bucket) DO UPDATE SET
        count = EXCLUDED.count,
        sum   = EXCLUDED.sum,
        min   = EXCLUDED.min,
        max   = EXCLUDED.max,
        last  = EXCLUDED.last;

    GET DIAGNOSTICS rows_upserted = ROW_COUNT;

    -- Histogram rollup — element-wise sum via unnest WITH ORDINALITY + GROUP BY idx.
    WITH src AS (
        SELECT
            metric_id,
            labels,
            resource_id,
            date_trunc('minute', recorded_at) AS bucket,
            histogram_counts
          FROM "05_monitoring"."61_evt_monitoring_metric_points"
         WHERE recorded_at >= start_ts
           AND recorded_at <  end_ts
           AND histogram_counts IS NOT NULL
    ),
    unrolled AS (
        SELECT
            metric_id,
            digest(labels::text, 'sha256') AS labels_hash,
            resource_id,
            bucket,
            u.idx,
            SUM(u.val)::BIGINT AS v
          FROM src s
          CROSS JOIN LATERAL unnest(s.histogram_counts) WITH ORDINALITY AS u(val, idx)
         GROUP BY metric_id, digest(labels::text, 'sha256'), resource_id, bucket, u.idx
    ),
    hist AS (
        SELECT
            metric_id, labels_hash, resource_id, bucket,
            array_agg(v ORDER BY idx) AS histogram_counts
          FROM unrolled
         GROUP BY metric_id, labels_hash, resource_id, bucket
    )
    UPDATE "05_monitoring"."70_evt_monitoring_metric_points_1m" tgt
       SET histogram_counts = h.histogram_counts
      FROM hist h
     WHERE tgt.metric_id    = h.metric_id
       AND tgt.labels_hash  = h.labels_hash
       AND tgt.bucket       = h.bucket;

    -- Advance watermark
    INSERT INTO "05_monitoring"."20_dtl_monitoring_rollup_watermarks" (table_name, last_bucket, updated_at)
    VALUES ('70_evt_monitoring_metric_points_1m', end_ts, CURRENT_TIMESTAMP)
    ON CONFLICT (table_name) DO UPDATE SET
        last_bucket = EXCLUDED.last_bucket,
        updated_at  = EXCLUDED.updated_at;

    RETURN rows_upserted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION "05_monitoring".monitoring_rollup_1m(TIMESTAMP) IS '1-minute rollup from evt_monitoring_metric_points. Idempotent via ON CONFLICT upsert. Advances watermark.';

-- 5m rollup from 1m.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_rollup_5m(since TIMESTAMP DEFAULT NULL)
RETURNS INT AS $$
DECLARE
    start_ts TIMESTAMP;
    end_ts   TIMESTAMP := date_trunc('minute', CURRENT_TIMESTAMP) - INTERVAL '1 minute';
    rows_upserted INT;
BEGIN
    IF since IS NULL THEN
        SELECT last_bucket INTO start_ts
          FROM "05_monitoring"."20_dtl_monitoring_rollup_watermarks"
         WHERE table_name = '71_evt_monitoring_metric_points_5m';
        IF start_ts IS NULL THEN
            start_ts := TIMESTAMP '1970-01-01';
        END IF;
    ELSE
        start_ts := since;
    END IF;

    INSERT INTO "05_monitoring"."71_evt_monitoring_metric_points_5m"
        (metric_id, labels_hash, labels, resource_id, org_id, bucket,
         count, sum, min, max, last, histogram_counts)
    SELECT
        metric_id,
        labels_hash,
        (array_agg(labels ORDER BY bucket DESC))[1] AS labels,
        resource_id,
        org_id,
        date_trunc('hour', bucket) + FLOOR(EXTRACT(MINUTE FROM bucket)::INT / 5) * INTERVAL '5 minutes' AS bucket5,
        SUM(count)::BIGINT                                             AS count,
        SUM(sum)::DOUBLE PRECISION                                     AS sum,
        MIN(min)::DOUBLE PRECISION                                     AS min,
        MAX(max)::DOUBLE PRECISION                                     AS max,
        (array_agg(last ORDER BY bucket DESC))[1]::DOUBLE PRECISION    AS last,
        (array_agg(histogram_counts ORDER BY bucket DESC))[1]          AS histogram_counts
      FROM "05_monitoring"."70_evt_monitoring_metric_points_1m"
     WHERE bucket >= start_ts AND bucket < end_ts
     GROUP BY metric_id, labels_hash, resource_id, org_id,
              date_trunc('hour', bucket) + FLOOR(EXTRACT(MINUTE FROM bucket)::INT / 5) * INTERVAL '5 minutes'
    ON CONFLICT (metric_id, labels_hash, bucket) DO UPDATE SET
        count = EXCLUDED.count,
        sum   = EXCLUDED.sum,
        min   = EXCLUDED.min,
        max   = EXCLUDED.max,
        last  = EXCLUDED.last,
        histogram_counts = EXCLUDED.histogram_counts,
        labels = EXCLUDED.labels;

    GET DIAGNOSTICS rows_upserted = ROW_COUNT;

    INSERT INTO "05_monitoring"."20_dtl_monitoring_rollup_watermarks" (table_name, last_bucket, updated_at)
    VALUES ('71_evt_monitoring_metric_points_5m', end_ts, CURRENT_TIMESTAMP)
    ON CONFLICT (table_name) DO UPDATE SET
        last_bucket = EXCLUDED.last_bucket,
        updated_at  = EXCLUDED.updated_at;

    RETURN rows_upserted;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_rollup_5m(TIMESTAMP) IS '5-minute rollup from _1m. Idempotent.';

-- 1h rollup from 5m.
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_rollup_1h(since TIMESTAMP DEFAULT NULL)
RETURNS INT AS $$
DECLARE
    start_ts TIMESTAMP;
    end_ts   TIMESTAMP := date_trunc('hour', CURRENT_TIMESTAMP);
    rows_upserted INT;
BEGIN
    IF since IS NULL THEN
        SELECT last_bucket INTO start_ts
          FROM "05_monitoring"."20_dtl_monitoring_rollup_watermarks"
         WHERE table_name = '72_evt_monitoring_metric_points_1h';
        IF start_ts IS NULL THEN
            start_ts := TIMESTAMP '1970-01-01';
        END IF;
    ELSE
        start_ts := since;
    END IF;

    INSERT INTO "05_monitoring"."72_evt_monitoring_metric_points_1h"
        (metric_id, labels_hash, labels, resource_id, org_id, bucket,
         count, sum, min, max, last, histogram_counts)
    SELECT
        metric_id,
        labels_hash,
        (array_agg(labels ORDER BY bucket DESC))[1] AS labels,
        resource_id,
        org_id,
        date_trunc('hour', bucket) AS bucketh,
        SUM(count)::BIGINT,
        SUM(sum)::DOUBLE PRECISION,
        MIN(min)::DOUBLE PRECISION,
        MAX(max)::DOUBLE PRECISION,
        (array_agg(last ORDER BY bucket DESC))[1]::DOUBLE PRECISION,
        (array_agg(histogram_counts ORDER BY bucket DESC))[1]
      FROM "05_monitoring"."71_evt_monitoring_metric_points_5m"
     WHERE bucket >= start_ts AND bucket < end_ts
     GROUP BY metric_id, labels_hash, resource_id, org_id, date_trunc('hour', bucket)
    ON CONFLICT (metric_id, labels_hash, bucket) DO UPDATE SET
        count = EXCLUDED.count,
        sum   = EXCLUDED.sum,
        min   = EXCLUDED.min,
        max   = EXCLUDED.max,
        last  = EXCLUDED.last,
        histogram_counts = EXCLUDED.histogram_counts,
        labels = EXCLUDED.labels;

    GET DIAGNOSTICS rows_upserted = ROW_COUNT;

    INSERT INTO "05_monitoring"."20_dtl_monitoring_rollup_watermarks" (table_name, last_bucket, updated_at)
    VALUES ('72_evt_monitoring_metric_points_1h', end_ts, CURRENT_TIMESTAMP)
    ON CONFLICT (table_name) DO UPDATE SET
        last_bucket = EXCLUDED.last_bucket,
        updated_at  = EXCLUDED.updated_at;

    RETURN rows_upserted;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_rollup_1h(TIMESTAMP) IS '1-hour rollup from _5m. Idempotent.';

-- DOWN ====
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_rollup_1h(TIMESTAMP);
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_rollup_5m(TIMESTAMP);
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_rollup_1m(TIMESTAMP);
DROP FUNCTION IF EXISTS "05_monitoring".monitoring_histogram_array_sum(BIGINT[], BIGINT[]);
DROP TABLE    IF EXISTS "05_monitoring"."20_dtl_monitoring_rollup_watermarks";
