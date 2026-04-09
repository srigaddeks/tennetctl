-- =============================================================================
-- Migration : 20260409_023_kbio_seed_policies
-- Description: Seed 50+ predefined kbio policies into fct_predefined_policies
--              and dtl_attrs via helper functions.
-- Schema     : 10_kbio
-- =============================================================================

-- ============================================================================
-- UP
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Helper: insert a text attr for a policy
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION "10_kbio"._seed_policy_text_attr(
    _entity_type_id SMALLINT,
    _policy_id      VARCHAR(36),
    _attr_code      TEXT,
    _value          TEXT
) RETURNS VOID AS $$
BEGIN
    INSERT INTO "10_kbio"."20_dtl_attrs"
        (id, entity_type_id, entity_id, attr_def_id, key_text)
    VALUES (
        gen_random_uuid()::text,
        _entity_type_id,
        _policy_id,
        (SELECT id FROM "10_kbio"."07_dim_attr_defs"
          WHERE entity_type_id = _entity_type_id AND code = _attr_code),
        _value
    );
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Helper: insert a policy row + all 7 EAV attrs
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION "10_kbio"._seed_policy(
    _category_code  TEXT,
    _action_code    TEXT,
    _severity       SMALLINT,
    _code           TEXT,
    _name           TEXT,
    _description    TEXT,
    _conditions     JSONB,
    _default_config JSONB,
    _tags           TEXT
) RETURNS VOID AS $$
DECLARE
    _policy_id      VARCHAR(36) := gen_random_uuid()::text;
    _entity_type_id SMALLINT;
BEGIN
    SELECT id INTO _entity_type_id
    FROM "10_kbio"."06_dim_entity_types"
    WHERE code = 'kbio_predefined_policy';

    INSERT INTO "10_kbio"."15_fct_predefined_policies"
        (id, category_id, action_id, severity, is_active, is_test, created_by, updated_by)
    VALUES (
        _policy_id,
        (SELECT id FROM "10_kbio"."06_dim_policy_categories" WHERE code = _category_code),
        (SELECT id FROM "10_kbio"."04_dim_drift_actions"     WHERE code = _action_code),
        _severity,
        TRUE, FALSE,
        'system', 'system'
    );

    -- Text attrs
    PERFORM "10_kbio"._seed_policy_text_attr(_entity_type_id, _policy_id, 'code',        _code);
    PERFORM "10_kbio"._seed_policy_text_attr(_entity_type_id, _policy_id, 'name',        _name);
    PERFORM "10_kbio"._seed_policy_text_attr(_entity_type_id, _policy_id, 'description', _description);
    PERFORM "10_kbio"._seed_policy_text_attr(_entity_type_id, _policy_id, 'tags',        _tags);
    PERFORM "10_kbio"._seed_policy_text_attr(_entity_type_id, _policy_id, 'version',     '1.0.0');

    -- JSONB attrs
    INSERT INTO "10_kbio"."20_dtl_attrs"
        (id, entity_type_id, entity_id, attr_def_id, key_jsonb)
    VALUES (
        gen_random_uuid()::text, _entity_type_id, _policy_id,
        (SELECT id FROM "10_kbio"."07_dim_attr_defs"
          WHERE entity_type_id = _entity_type_id AND code = 'conditions'),
        _conditions
    );
    INSERT INTO "10_kbio"."20_dtl_attrs"
        (id, entity_type_id, entity_id, attr_def_id, key_jsonb)
    VALUES (
        gen_random_uuid()::text, _entity_type_id, _policy_id,
        (SELECT id FROM "10_kbio"."07_dim_attr_defs"
          WHERE entity_type_id = _entity_type_id AND code = 'default_config'),
        _default_config
    );
END;
$$ LANGUAGE plpgsql;

-- ===========================================================================
-- FRAUD / ACCOUNT TAKEOVER (10 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 90::SMALLINT,
    'ato-high-drift-new-device',
    'Account Takeover: High Drift on New Device',
    'Blocks sessions with very high behavioral drift score on a device never seen before for this user.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.85,"config_key":"drift_threshold"},{"field":"device.is_new","op":"==","value":true}],"action":"block","reason_template":"Drift {behavioral_drift:.2f} on unknown device"}'::jsonb,
    '{"drift_threshold":0.85}'::jsonb,
    'ato,fraud,critical,new-device'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'challenge', 85::SMALLINT,
    'ato-high-drift-known-device',
    'Account Takeover: High Drift on Known Device',
    'Challenges sessions showing high behavioral drift on a previously seen device.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.80,"config_key":"drift_threshold"},{"field":"device.is_new","op":"==","value":false}],"action":"challenge","reason_template":"Drift {behavioral_drift:.2f} on known device"}'::jsonb,
    '{"drift_threshold":0.80}'::jsonb,
    'ato,fraud,high,known-device'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'challenge', 75::SMALLINT,
    'ato-drift-plus-vpn',
    'Account Takeover: Drift + VPN Detected',
    'Challenges sessions with moderate-high drift where the IP resolves to a VPN endpoint.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.65,"config_key":"drift_threshold"},{"field":"network.is_vpn","op":"==","value":true}],"action":"challenge","reason_template":"Drift {behavioral_drift:.2f} via VPN"}'::jsonb,
    '{"drift_threshold":0.65}'::jsonb,
    'ato,fraud,vpn,network'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 80::SMALLINT,
    'ato-drift-plus-tor',
    'Account Takeover: Drift + Tor Exit Node',
    'Blocks sessions with elevated drift where traffic originates from a known Tor exit node.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.55,"config_key":"drift_threshold"},{"field":"network.is_tor","op":"==","value":true}],"action":"block","reason_template":"Drift {behavioral_drift:.2f} via Tor exit node"}'::jsonb,
    '{"drift_threshold":0.55}'::jsonb,
    'ato,fraud,tor,network,critical'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 95::SMALLINT,
    'ato-session-hijack',
    'Account Takeover: Session Hijack Detected',
    'Blocks sessions where device fingerprint, IP subnet, or behavioral signature changes mid-session, indicating possible token theft.',
    '{"operator":"OR","rules":[{"field":"session.fingerprint_changed","op":"==","value":true},{"field":"session.ip_subnet_changed","op":"==","value":true},{"field":"session.behavioral_signature_drift","op":">","value":0.90,"config_key":"hijack_drift_threshold"}],"action":"block","reason_template":"Session hijack signal: {session.fingerprint_changed}"}'::jsonb,
    '{"hijack_drift_threshold":0.90}'::jsonb,
    'ato,fraud,session,hijack,critical'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 85::SMALLINT,
    'ato-credential-stuffing',
    'Account Takeover: Credential Stuffing Pattern',
    'Blocks sessions where rapid successive login attempts across accounts are detected from the same behavioral signature.',
    '{"operator":"AND","rules":[{"field":"session.login_attempts_last_hour","op":">","value":5,"config_key":"max_login_attempts"},{"field":"behavioral_drift","op":">","value":0.60,"config_key":"drift_threshold"}],"action":"block","reason_template":"Credential stuffing: {session.login_attempts_last_hour} attempts"}'::jsonb,
    '{"max_login_attempts":5,"drift_threshold":0.60}'::jsonb,
    'ato,fraud,credential-stuffing,critical'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'challenge', 70::SMALLINT,
    'ato-rapid-drift-spike',
    'Account Takeover: Rapid Drift Spike',
    'Challenges sessions where behavioral drift escalates sharply within a short window.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift_delta","op":">","value":0.30,"config_key":"drift_delta_threshold"},{"field":"session.age_seconds","op":"<","value":300,"config_key":"spike_window_seconds"}],"action":"challenge","reason_template":"Drift spiked {behavioral_drift_delta:.2f} in under 5 min"}'::jsonb,
    '{"drift_delta_threshold":0.30,"spike_window_seconds":300}'::jsonb,
    'ato,fraud,drift-spike'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 90::SMALLINT,
    'ato-multi-signal-anomaly',
    'Account Takeover: Multi-Signal Anomaly',
    'Blocks sessions where three or more independent risk signals are elevated simultaneously.',
    '{"operator":"AND","rules":[{"field":"risk.signals_elevated_count","op":">=","value":3,"config_key":"min_signals"},{"field":"risk.composite_score","op":">","value":0.80,"config_key":"composite_threshold"}],"action":"block","reason_template":"Multi-signal anomaly: {risk.signals_elevated_count} signals elevated"}'::jsonb,
    '{"min_signals":3,"composite_threshold":0.80}'::jsonb,
    'ato,fraud,multi-signal,critical'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'challenge', 65::SMALLINT,
    'ato-drift-trend-worsening',
    'Account Takeover: Worsening Drift Trend',
    'Challenges sessions where behavioral drift has been steadily increasing over multiple recent sessions.',
    '{"operator":"AND","rules":[{"field":"profile.drift_trend_slope","op":">","value":0.05,"config_key":"trend_slope_threshold"},{"field":"profile.sessions_analyzed","op":">=","value":3}],"action":"challenge","reason_template":"Drift trend slope {profile.drift_trend_slope:.3f} over recent sessions"}'::jsonb,
    '{"trend_slope_threshold":0.05}'::jsonb,
    'ato,fraud,drift-trend'
);

SELECT "10_kbio"._seed_policy(
    'fraud', 'block', 88::SMALLINT,
    'ato-credential-plus-device',
    'Account Takeover: Compromised Credential + Unrecognized Device',
    'Blocks when leaked-credential signal is active and the device has never been associated with the account.',
    '{"operator":"AND","rules":[{"field":"user.credential_leaked","op":"==","value":true},{"field":"device.is_new","op":"==","value":true}],"action":"block","reason_template":"Leaked credential + unrecognized device"}'::jsonb,
    '{}'::jsonb,
    'ato,fraud,credential,device,critical'
);

-- ===========================================================================
-- BOT DETECTION (8 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'bot', 'block', 95::SMALLINT,
    'bot-block-high',
    'Bot Detection: High Confidence Block',
    'Blocks sessions where the bot confidence score is very high.',
    '{"operator":"AND","rules":[{"field":"bot.confidence","op":">","value":0.90,"config_key":"bot_confidence_threshold"}],"action":"block","reason_template":"Bot confidence {bot.confidence:.2f}"}'::jsonb,
    '{"bot_confidence_threshold":0.90}'::jsonb,
    'bot,automation,critical'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'challenge', 70::SMALLINT,
    'bot-challenge-medium',
    'Bot Detection: Medium Confidence Challenge',
    'Challenges sessions where bot signals are elevated but not conclusive.',
    '{"operator":"AND","rules":[{"field":"bot.confidence","op":">","value":0.60,"config_key":"bot_confidence_low"},{"field":"bot.confidence","op":"<=","value":0.90,"config_key":"bot_confidence_high"}],"action":"challenge","reason_template":"Bot confidence {bot.confidence:.2f} — requires verification"}'::jsonb,
    '{"bot_confidence_low":0.60,"bot_confidence_high":0.90}'::jsonb,
    'bot,automation,medium'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'monitor', 40::SMALLINT,
    'bot-monitor-low',
    'Bot Detection: Low Signal Monitor',
    'Monitors sessions with weak bot signals for pattern accumulation without blocking.',
    '{"operator":"AND","rules":[{"field":"bot.confidence","op":">","value":0.30,"config_key":"bot_confidence_threshold"},{"field":"bot.confidence","op":"<=","value":0.60}],"action":"monitor","reason_template":"Low bot signal {bot.confidence:.2f} — monitoring"}'::jsonb,
    '{"bot_confidence_threshold":0.30}'::jsonb,
    'bot,automation,low,monitor'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'block', 95::SMALLINT,
    'bot-automation-detected',
    'Bot Detection: Automation Framework Detected',
    'Blocks sessions where browser automation framework artifacts are detected (Selenium, Puppeteer, Playwright attributes).',
    '{"operator":"OR","rules":[{"field":"device.webdriver_present","op":"==","value":true},{"field":"device.automation_artifacts","op":"==","value":true}],"action":"block","reason_template":"Automation artifacts detected"}'::jsonb,
    '{}'::jsonb,
    'bot,automation,selenium,puppeteer,critical'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'block', 90::SMALLINT,
    'bot-headless-browser',
    'Bot Detection: Headless Browser',
    'Blocks sessions running in headless browser environments without legitimate use case.',
    '{"operator":"AND","rules":[{"field":"device.is_headless","op":"==","value":true},{"field":"session.has_trusted_context","op":"==","value":false}],"action":"block","reason_template":"Headless browser without trusted context"}'::jsonb,
    '{}'::jsonb,
    'bot,headless,automation,critical'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'block', 95::SMALLINT,
    'bot-keystroke-impossible',
    'Bot Detection: Impossible Keystroke Dynamics',
    'Blocks sessions where keystroke timing is physically impossible for a human (sub-millisecond intervals, perfect uniformity).',
    '{"operator":"OR","rules":[{"field":"keystroke.min_interval_ms","op":"<","value":10,"config_key":"min_human_interval_ms"},{"field":"keystroke.variance_coefficient","op":"<","value":0.01,"config_key":"min_variance"}],"action":"block","reason_template":"Impossible keystroke pattern: interval {keystroke.min_interval_ms}ms"}'::jsonb,
    '{"min_human_interval_ms":10,"min_variance":0.01}'::jsonb,
    'bot,keystroke,impossible,critical'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'block', 90::SMALLINT,
    'bot-zero-variance',
    'Bot Detection: Zero Behavioral Variance',
    'Blocks sessions exhibiting near-zero variance across all behavioral signals — indicative of scripted replay.',
    '{"operator":"AND","rules":[{"field":"behavioral.overall_variance","op":"<","value":0.02,"config_key":"min_variance_threshold"}],"action":"block","reason_template":"Behavioral variance {behavioral.overall_variance:.4f} — scripted replay suspected"}'::jsonb,
    '{"min_variance_threshold":0.02}'::jsonb,
    'bot,variance,replay,critical'
);

SELECT "10_kbio"._seed_policy(
    'bot', 'challenge', 75::SMALLINT,
    'bot-linear-pointer',
    'Bot Detection: Linear Pointer Movement',
    'Challenges sessions where mouse/pointer trajectories are perfectly linear, lacking human micro-tremor.',
    '{"operator":"AND","rules":[{"field":"pointer.linearity_score","op":">","value":0.98,"config_key":"linearity_threshold"},{"field":"pointer.event_count","op":">","value":10}],"action":"challenge","reason_template":"Pointer linearity {pointer.linearity_score:.3f} — possible bot"}'::jsonb,
    '{"linearity_threshold":0.98}'::jsonb,
    'bot,pointer,mouse,linear'
);

-- ===========================================================================
-- AUTHENTICATION (8 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'authentication', 'challenge', 60::SMALLINT,
    'auth-new-device-stepup',
    'Authentication: New Device Step-Up',
    'Requires step-up verification when a user authenticates from a device not previously associated with their account.',
    '{"operator":"AND","rules":[{"field":"device.is_new","op":"==","value":true},{"field":"session.action","op":"==","value":"login"}],"action":"challenge","reason_template":"Login from new device — step-up required"}'::jsonb,
    '{}'::jsonb,
    'auth,device,stepup,mfa'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'challenge', 65::SMALLINT,
    'auth-elevated-drift-mfa',
    'Authentication: Elevated Drift Requires MFA',
    'Challenges authentication attempts when behavioral drift at login is elevated, even on known devices.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.55,"config_key":"drift_threshold"},{"field":"session.action","op":"==","value":"login"}],"action":"challenge","reason_template":"Elevated drift {behavioral_drift:.2f} at login"}'::jsonb,
    '{"drift_threshold":0.55}'::jsonb,
    'auth,mfa,drift'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'monitor', 30::SMALLINT,
    'auth-weak-baseline-monitor',
    'Authentication: Weak Behavioral Baseline',
    'Monitors authentication events for users who do not yet have a strong behavioral baseline established.',
    '{"operator":"AND","rules":[{"field":"profile.baseline_strength","op":"<","value":0.40,"config_key":"min_baseline_strength"},{"field":"session.action","op":"==","value":"login"}],"action":"monitor","reason_template":"Weak baseline {profile.baseline_strength:.2f} — collecting data"}'::jsonb,
    '{"min_baseline_strength":0.40}'::jsonb,
    'auth,baseline,monitor'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'challenge', 70::SMALLINT,
    'auth-login-drift-check',
    'Authentication: Login Drift Check',
    'Challenges logins where the behavioral pattern deviates significantly from the user profile average.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.65,"config_key":"drift_threshold"},{"field":"session.action","op":"==","value":"login"},{"field":"profile.baseline_strength","op":">=","value":0.60}],"action":"challenge","reason_template":"Login drift {behavioral_drift:.2f} against strong baseline"}'::jsonb,
    '{"drift_threshold":0.65}'::jsonb,
    'auth,login,drift'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'block', 80::SMALLINT,
    'auth-password-behavioral',
    'Authentication: Password-Typing Behavioral Mismatch',
    'Blocks authentication when the password entry keystroke dynamics diverge sharply from the enrolled pattern.',
    '{"operator":"AND","rules":[{"field":"keystroke.password_similarity","op":"<","value":0.40,"config_key":"min_similarity"},{"field":"profile.password_keystroke_enrolled","op":"==","value":true}],"action":"block","reason_template":"Password keystroke mismatch {keystroke.password_similarity:.2f}"}'::jsonb,
    '{"min_similarity":0.40}'::jsonb,
    'auth,keystroke,password,biometric'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'challenge', 75::SMALLINT,
    'auth-multi-factor-drift',
    'Authentication: Drift During MFA Entry',
    'Challenges or re-prompts when behavioral drift is detected during the MFA code entry phase.',
    '{"operator":"AND","rules":[{"field":"behavioral_drift","op":">","value":0.70,"config_key":"drift_threshold"},{"field":"session.phase","op":"==","value":"mfa"}],"action":"challenge","reason_template":"Drift {behavioral_drift:.2f} during MFA phase"}'::jsonb,
    '{"drift_threshold":0.70}'::jsonb,
    'auth,mfa,drift'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'monitor', 20::SMALLINT,
    'auth-first-session-monitor',
    'Authentication: First Session Monitor',
    'Monitors the user''s very first authenticated session to start building behavioral baseline without friction.',
    '{"operator":"AND","rules":[{"field":"profile.total_sessions","op":"==","value":0}],"action":"monitor","reason_template":"First session — baseline enrollment in progress"}'::jsonb,
    '{}'::jsonb,
    'auth,onboarding,first-session,monitor'
);

SELECT "10_kbio"._seed_policy(
    'authentication', 'challenge', 65::SMALLINT,
    'auth-credential-reuse-pattern',
    'Authentication: Credential Reuse Pattern',
    'Challenges sessions where behavioral analysis suggests the same credentials may be in use across multiple distinct users.',
    '{"operator":"AND","rules":[{"field":"session.credential_sharing_score","op":">","value":0.70,"config_key":"sharing_threshold"}],"action":"challenge","reason_template":"Credential sharing score {session.credential_sharing_score:.2f}"}'::jsonb,
    '{"sharing_threshold":0.70}'::jsonb,
    'auth,credential-reuse,sharing'
);

-- ===========================================================================
-- GEOGRAPHIC / TRAVEL (7 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'geo', 'block', 90::SMALLINT,
    'geo-impossible-travel',
    'Geographic: Impossible Travel',
    'Blocks sessions where successive authentications from geographically distant locations are temporally impossible.',
    '{"operator":"AND","rules":[{"field":"geo.travel_speed_kmh","op":">","value":900,"config_key":"max_travel_speed_kmh"}],"action":"block","reason_template":"Impossible travel speed {geo.travel_speed_kmh:.0f} km/h"}'::jsonb,
    '{"max_travel_speed_kmh":900}'::jsonb,
    'geo,travel,impossible,critical'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'block', 85::SMALLINT,
    'geo-high-risk-country',
    'Geographic: High-Risk Country',
    'Blocks sessions originating from countries on the configured high-risk country list.',
    '{"operator":"AND","rules":[{"field":"geo.country_code","op":"in","value":"config_list","config_key":"high_risk_countries"}],"action":"block","reason_template":"Access from high-risk country {geo.country_code}"}'::jsonb,
    '{"high_risk_countries":[]}'::jsonb,
    'geo,country,high-risk,compliance'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'challenge', 55::SMALLINT,
    'geo-new-country',
    'Geographic: New Country for User',
    'Challenges sessions from a country the user has never previously accessed from.',
    '{"operator":"AND","rules":[{"field":"geo.country_is_new_for_user","op":"==","value":true}],"action":"challenge","reason_template":"First access from {geo.country_code}"}'::jsonb,
    '{}'::jsonb,
    'geo,country,new,travel'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'challenge', 50::SMALLINT,
    'geo-datacenter-ip',
    'Geographic: Datacenter or Hosting IP',
    'Challenges sessions originating from known datacenter, cloud, or hosting provider IP ranges.',
    '{"operator":"AND","rules":[{"field":"network.ip_type","op":"==","value":"datacenter"}],"action":"challenge","reason_template":"Traffic from datacenter IP ({network.asn_org})"}'::jsonb,
    '{}'::jsonb,
    'geo,datacenter,hosting,cloud'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'challenge', 60::SMALLINT,
    'geo-location-drift',
    'Geographic: Location Drift from Profile',
    'Challenges sessions where the IP geolocation deviates significantly from the user''s typical access geography.',
    '{"operator":"AND","rules":[{"field":"geo.distance_from_profile_km","op":">","value":500,"config_key":"max_geo_drift_km"}],"action":"challenge","reason_template":"Location {geo.distance_from_profile_km:.0f} km from typical"}'::jsonb,
    '{"max_geo_drift_km":500}'::jsonb,
    'geo,location,drift'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'challenge', 65::SMALLINT,
    'geo-vpn-with-drift',
    'Geographic: VPN with Behavioral Drift',
    'Challenges sessions that combine VPN usage with behavioral drift above threshold.',
    '{"operator":"AND","rules":[{"field":"network.is_vpn","op":"==","value":true},{"field":"behavioral_drift","op":">","value":0.50,"config_key":"drift_threshold"}],"action":"challenge","reason_template":"VPN + drift {behavioral_drift:.2f}"}'::jsonb,
    '{"drift_threshold":0.50}'::jsonb,
    'geo,vpn,drift,network'
);

SELECT "10_kbio"._seed_policy(
    'geo', 'block', 90::SMALLINT,
    'geo-tor-block',
    'Geographic: Tor Exit Node Block',
    'Blocks all sessions originating from known Tor exit nodes.',
    '{"operator":"AND","rules":[{"field":"network.is_tor","op":"==","value":true}],"action":"block","reason_template":"Traffic from Tor exit node"}'::jsonb,
    '{}'::jsonb,
    'geo,tor,anonymizer,critical'
);

-- ===========================================================================
-- DEVICE TRUST (7 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'device_trust', 'allow', 10::SMALLINT,
    'trust-device-fastpass',
    'Device Trust: Fast Pass for Trusted Low-Drift Device',
    'Allows sessions early without further checks when device is fully trusted and behavioral drift is very low.',
    '{"operator":"AND","rules":[{"field":"device.trust_level","op":"==","value":"trusted"},{"field":"behavioral_drift","op":"<","value":0.15,"config_key":"drift_threshold"}],"action":"allow","reason_template":"Trusted device + low drift {behavioral_drift:.2f} — fast pass"}'::jsonb,
    '{"drift_threshold":0.15}'::jsonb,
    'trust,device,fastpass,allow'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'challenge', 70::SMALLINT,
    'trust-device-fingerprint-drift',
    'Device Trust: Device Fingerprint Drift',
    'Challenges sessions where the current device fingerprint differs from the last trusted fingerprint for this device ID.',
    '{"operator":"AND","rules":[{"field":"device.fingerprint_drift_score","op":">","value":0.60,"config_key":"fingerprint_drift_threshold"}],"action":"challenge","reason_template":"Device fingerprint drifted {device.fingerprint_drift_score:.2f}"}'::jsonb,
    '{"fingerprint_drift_threshold":0.60}'::jsonb,
    'trust,device,fingerprint,drift'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'allow', 15::SMALLINT,
    'trust-ip-known',
    'Device Trust: Known IP Fast Pass',
    'Allows sessions from IP addresses with a long positive history and no associated risk signals.',
    '{"operator":"AND","rules":[{"field":"network.ip_trust_score","op":">","value":0.90,"config_key":"ip_trust_threshold"},{"field":"behavioral_drift","op":"<","value":0.20,"config_key":"drift_threshold"}],"action":"allow","reason_template":"Trusted IP {network.ip} + low drift"}'::jsonb,
    '{"ip_trust_threshold":0.90,"drift_threshold":0.20}'::jsonb,
    'trust,ip,fastpass,allow'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'challenge', 60::SMALLINT,
    'trust-untrusted-device-strict',
    'Device Trust: Untrusted Device Strict Mode',
    'Challenges sessions on devices that are actively flagged as untrusted in the device registry.',
    '{"operator":"AND","rules":[{"field":"device.trust_level","op":"==","value":"untrusted"}],"action":"challenge","reason_template":"Device explicitly untrusted"}'::jsonb,
    '{}'::jsonb,
    'trust,device,untrusted'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'monitor', 25::SMALLINT,
    'trust-new-device-monitor',
    'Device Trust: New Device Monitor',
    'Monitors sessions from new devices that have not yet accumulated enough trust signals.',
    '{"operator":"AND","rules":[{"field":"device.is_new","op":"==","value":true},{"field":"device.trust_level","op":"==","value":"unknown"}],"action":"monitor","reason_template":"New device — accumulating trust signals"}'::jsonb,
    '{}'::jsonb,
    'trust,device,new,monitor'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'challenge', 55::SMALLINT,
    'trust-device-age-check',
    'Device Trust: Device Age Threshold',
    'Challenges sessions where the device was first seen very recently, indicating possible throwaway device.',
    '{"operator":"AND","rules":[{"field":"device.age_days","op":"<","value":3,"config_key":"min_device_age_days"},{"field":"behavioral_drift","op":">","value":0.40,"config_key":"drift_threshold"}],"action":"challenge","reason_template":"Device only {device.age_days} day(s) old + drift {behavioral_drift:.2f}"}'::jsonb,
    '{"min_device_age_days":3,"drift_threshold":0.40}'::jsonb,
    'trust,device,age'
);

SELECT "10_kbio"._seed_policy(
    'device_trust', 'challenge', 65::SMALLINT,
    'trust-multi-device-session',
    'Device Trust: Concurrent Multi-Device Session',
    'Challenges when the same session token is in use across multiple distinct devices simultaneously.',
    '{"operator":"AND","rules":[{"field":"session.concurrent_device_count","op":">","value":1,"config_key":"max_concurrent_devices"}],"action":"challenge","reason_template":"Session active on {session.concurrent_device_count} devices"}'::jsonb,
    '{"max_concurrent_devices":1}'::jsonb,
    'trust,device,multi-device,session'
);

-- ===========================================================================
-- SESSION SECURITY (8 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'session', 'flag', 50::SMALLINT,
    'session-anomaly-short',
    'Session Security: Short Anomalous Session',
    'Flags sessions that complete high-value actions in an unusually short time, indicating possible automation.',
    '{"operator":"AND","rules":[{"field":"session.age_seconds","op":"<","value":30,"config_key":"min_session_length_seconds"},{"field":"session.high_value_action_count","op":">","value":0}],"action":"flag","reason_template":"High-value action in {session.age_seconds}s session"}'::jsonb,
    '{"min_session_length_seconds":30}'::jsonb,
    'session,anomaly,short,flag'
);

SELECT "10_kbio"._seed_policy(
    'session', 'challenge', 75::SMALLINT,
    'session-critical-action-guard',
    'Session Security: Critical Action Guard',
    'Challenges before executing critical actions (fund transfer, password change, API key rotation) if session trust is below threshold.',
    '{"operator":"AND","rules":[{"field":"session.action_criticality","op":"==","value":"critical"},{"field":"session.trust_score","op":"<","value":0.80,"config_key":"min_trust_for_critical"}],"action":"challenge","reason_template":"Critical action with session trust {session.trust_score:.2f}"}'::jsonb,
    '{"min_trust_for_critical":0.80}'::jsonb,
    'session,critical-action,guard'
);

SELECT "10_kbio"._seed_policy(
    'session', 'challenge', 60::SMALLINT,
    'session-idle-resume-check',
    'Session Security: Idle Resume Behavioral Check',
    'Challenges sessions resuming after a long idle period by re-verifying behavioral consistency.',
    '{"operator":"AND","rules":[{"field":"session.idle_duration_minutes","op":">","value":30,"config_key":"idle_threshold_minutes"},{"field":"behavioral_drift","op":">","value":0.45,"config_key":"drift_threshold"}],"action":"challenge","reason_template":"Idle {session.idle_duration_minutes}min + drift {behavioral_drift:.2f}"}'::jsonb,
    '{"idle_threshold_minutes":30,"drift_threshold":0.45}'::jsonb,
    'session,idle,resume'
);

SELECT "10_kbio"._seed_policy(
    'session', 'block', 80::SMALLINT,
    'session-page-count-anomaly',
    'Session Security: Anomalous Page Visit Count',
    'Blocks sessions that visit an abnormally high number of pages in a short time, indicative of scraping.',
    '{"operator":"AND","rules":[{"field":"session.pages_per_minute","op":">","value":60,"config_key":"max_pages_per_minute"}],"action":"block","reason_template":"Page rate {session.pages_per_minute:.0f}/min — possible scraping"}'::jsonb,
    '{"max_pages_per_minute":60}'::jsonb,
    'session,scraping,page-count,bot'
);

SELECT "10_kbio"._seed_policy(
    'session', 'flag', 45::SMALLINT,
    'session-rapid-navigation',
    'Session Security: Rapid Navigation Pattern',
    'Flags sessions with rapid sequential navigation that differs from the user''s typical browsing cadence.',
    '{"operator":"AND","rules":[{"field":"session.navigation_speed_ratio","op":">","value":3.0,"config_key":"max_speed_ratio"}],"action":"flag","reason_template":"Navigation {session.navigation_speed_ratio:.1f}x faster than baseline"}'::jsonb,
    '{"max_speed_ratio":3.0}'::jsonb,
    'session,navigation,rapid,flag'
);

SELECT "10_kbio"._seed_policy(
    'session', 'monitor', 35::SMALLINT,
    'session-overnight-active',
    'Session Security: Overnight Active Session',
    'Monitors sessions that remain active during hours outside the user''s typical usage window.',
    '{"operator":"AND","rules":[{"field":"session.local_hour","op":"not_in","value":"config_list","config_key":"typical_active_hours"},{"field":"session.age_seconds","op":">","value":3600}],"action":"monitor","reason_template":"Session active at {session.local_hour}:00 (outside typical window)"}'::jsonb,
    '{"typical_active_hours":[6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22]}'::jsonb,
    'session,overnight,hours,monitor'
);

SELECT "10_kbio"._seed_policy(
    'session', 'challenge', 55::SMALLINT,
    'session-multi-tab-drift',
    'Session Security: Multi-Tab Behavioral Drift',
    'Challenges sessions where parallel activity across multiple tabs produces divergent behavioral signatures.',
    '{"operator":"AND","rules":[{"field":"session.tab_count","op":">","value":3,"config_key":"max_normal_tabs"},{"field":"session.cross_tab_drift","op":">","value":0.50,"config_key":"cross_tab_drift_threshold"}],"action":"challenge","reason_template":"Cross-tab drift {session.cross_tab_drift:.2f} across {session.tab_count} tabs"}'::jsonb,
    '{"max_normal_tabs":3,"cross_tab_drift_threshold":0.50}'::jsonb,
    'session,multi-tab,drift'
);

SELECT "10_kbio"._seed_policy(
    'session', 'challenge', 70::SMALLINT,
    'session-escalation-pattern',
    'Session Security: Privilege Escalation Pattern',
    'Challenges sessions where action sequence suggests privilege escalation probing (accessing admin endpoints in order).',
    '{"operator":"AND","rules":[{"field":"session.escalation_probe_count","op":">","value":2,"config_key":"max_escalation_probes"}],"action":"challenge","reason_template":"Escalation probes: {session.escalation_probe_count}"}'::jsonb,
    '{"max_escalation_probes":2}'::jsonb,
    'session,escalation,privilege,security'
);

-- ===========================================================================
-- COMPLIANCE (5 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'compliance', 'challenge', 65::SMALLINT,
    'compliance-require-baseline',
    'Compliance: Require Behavioral Baseline',
    'Challenges users who attempt high-value actions before a sufficient behavioral baseline has been established.',
    '{"operator":"AND","rules":[{"field":"profile.baseline_strength","op":"<","value":0.60,"config_key":"min_baseline"},{"field":"session.action_criticality","op":"in","value":["high","critical"]}],"action":"challenge","reason_template":"Insufficient baseline {profile.baseline_strength:.2f} for high-value action"}'::jsonb,
    '{"min_baseline":0.60}'::jsonb,
    'compliance,baseline,high-value'
);

SELECT "10_kbio"._seed_policy(
    'compliance', 'monitor', 40::SMALLINT,
    'compliance-audit-high-value',
    'Compliance: Audit High-Value Operations',
    'Ensures all high-value and sensitive operations are logged with full behavioral context for compliance audit trails.',
    '{"operator":"AND","rules":[{"field":"session.action_criticality","op":"in","value":["high","critical"]}],"action":"monitor","reason_template":"High-value operation — full audit capture"}'::jsonb,
    '{}'::jsonb,
    'compliance,audit,high-value,logging'
);

SELECT "10_kbio"._seed_policy(
    'compliance', 'challenge', 70::SMALLINT,
    'compliance-data-export-guard',
    'Compliance: Data Export Guard',
    'Challenges before allowing bulk data export operations, verifying behavioral consistency and intent.',
    '{"operator":"AND","rules":[{"field":"session.operation_type","op":"==","value":"data_export"},{"field":"session.trust_score","op":"<","value":0.85,"config_key":"min_trust"}],"action":"challenge","reason_template":"Data export with session trust {session.trust_score:.2f}"}'::jsonb,
    '{"min_trust":0.85}'::jsonb,
    'compliance,data-export,guard,privacy'
);

SELECT "10_kbio"._seed_policy(
    'compliance', 'challenge', 75::SMALLINT,
    'compliance-admin-action-verify',
    'Compliance: Admin Action Verification',
    'Challenges administrative actions (user deletion, permission grants, config changes) with full behavioral verification.',
    '{"operator":"AND","rules":[{"field":"session.actor_role","op":"==","value":"admin"},{"field":"session.operation_type","op":"in","value":["delete_user","grant_permission","change_config"]}],"action":"challenge","reason_template":"Admin action {session.operation_type} requires verification"}'::jsonb,
    '{}'::jsonb,
    'compliance,admin,verification,governance'
);

SELECT "10_kbio"._seed_policy(
    'compliance', 'challenge', 80::SMALLINT,
    'compliance-pci-transaction',
    'Compliance: PCI DSS Transaction Verification',
    'Challenges payment and financial transactions per PCI DSS behavioral verification requirements.',
    '{"operator":"AND","rules":[{"field":"session.operation_type","op":"==","value":"payment"},{"field":"session.trust_score","op":"<","value":0.90,"config_key":"pci_min_trust"}],"action":"challenge","reason_template":"PCI transaction with session trust {session.trust_score:.2f}"}'::jsonb,
    '{"pci_min_trust":0.90}'::jsonb,
    'compliance,pci,payment,financial'
);

-- ===========================================================================
-- RISK THRESHOLDS (5 policies)
-- ===========================================================================

SELECT "10_kbio"._seed_policy(
    'risk', 'monitor', 30::SMALLINT,
    'risk-composite-low',
    'Risk: Composite Score Low — Monitor',
    'Monitors sessions where the composite risk score is low-to-moderate without taking action.',
    '{"operator":"AND","rules":[{"field":"risk.composite_score","op":">=","value":0.20,"config_key":"low_threshold"},{"field":"risk.composite_score","op":"<","value":0.50,"config_key":"medium_threshold"}],"action":"monitor","reason_template":"Composite risk {risk.composite_score:.2f} — monitoring"}'::jsonb,
    '{"low_threshold":0.20,"medium_threshold":0.50}'::jsonb,
    'risk,composite,low,monitor'
);

SELECT "10_kbio"._seed_policy(
    'risk', 'challenge', 60::SMALLINT,
    'risk-composite-medium',
    'Risk: Composite Score Medium — Challenge',
    'Challenges sessions where the composite risk score is in the medium range.',
    '{"operator":"AND","rules":[{"field":"risk.composite_score","op":">=","value":0.50,"config_key":"medium_threshold"},{"field":"risk.composite_score","op":"<","value":0.80,"config_key":"high_threshold"}],"action":"challenge","reason_template":"Composite risk {risk.composite_score:.2f}"}'::jsonb,
    '{"medium_threshold":0.50,"high_threshold":0.80}'::jsonb,
    'risk,composite,medium,challenge'
);

SELECT "10_kbio"._seed_policy(
    'risk', 'block', 85::SMALLINT,
    'risk-composite-high',
    'Risk: Composite Score High — Block',
    'Blocks sessions where the composite risk score crosses the high-risk threshold.',
    '{"operator":"AND","rules":[{"field":"risk.composite_score","op":">=","value":0.80,"config_key":"high_threshold"}],"action":"block","reason_template":"Composite risk {risk.composite_score:.2f} — high risk"}'::jsonb,
    '{"high_threshold":0.80}'::jsonb,
    'risk,composite,high,block,critical'
);

SELECT "10_kbio"._seed_policy(
    'risk', 'monitor', 25::SMALLINT,
    'risk-confidence-low',
    'Risk: Low Model Confidence — Monitor Only',
    'Monitors sessions where the risk model confidence is too low to take decisive action; collects data.',
    '{"operator":"AND","rules":[{"field":"risk.model_confidence","op":"<","value":0.50,"config_key":"min_confidence"}],"action":"monitor","reason_template":"Model confidence {risk.model_confidence:.2f} — insufficient for action"}'::jsonb,
    '{"min_confidence":0.50}'::jsonb,
    'risk,confidence,low,monitor'
);

SELECT "10_kbio"._seed_policy(
    'risk', 'monitor', 20::SMALLINT,
    'risk-enrollment-period',
    'Risk: Enrollment Period Grace',
    'Monitors without blocking during the initial enrollment window while behavioral baseline is being built.',
    '{"operator":"AND","rules":[{"field":"profile.enrollment_period_active","op":"==","value":true}],"action":"monitor","reason_template":"Enrollment period active — grace mode"}'::jsonb,
    '{"enrollment_grace_days":14}'::jsonb,
    'risk,enrollment,onboarding,monitor'
);

-- ===========================================================================
-- Drop helper functions (UP section cleanup — they are not needed post-seed)
-- ===========================================================================

DROP FUNCTION IF EXISTS "10_kbio"._seed_policy(
    TEXT, TEXT, SMALLINT, TEXT, TEXT, TEXT, JSONB, JSONB, TEXT
);
DROP FUNCTION IF EXISTS "10_kbio"._seed_policy_text_attr(
    SMALLINT, VARCHAR(36), TEXT, TEXT
);


-- ============================================================================
-- DOWN
-- ============================================================================

-- Remove all seeded predefined policies and their EAV attrs.
-- The ON DELETE CASCADE on dtl_attrs.entity_id should handle attrs,
-- but we use explicit subselect deletion for safety.

-- Drop helper functions if somehow still present
DROP FUNCTION IF EXISTS "10_kbio"._seed_policy(
    TEXT, TEXT, SMALLINT, TEXT, TEXT, TEXT, JSONB, JSONB, TEXT
);
DROP FUNCTION IF EXISTS "10_kbio"._seed_policy_text_attr(
    SMALLINT, VARCHAR(36), TEXT, TEXT
);

-- Delete EAV attrs for all system-seeded predefined policies
DELETE FROM "10_kbio"."20_dtl_attrs"
WHERE entity_type_id = (
        SELECT id FROM "10_kbio"."06_dim_entity_types"
        WHERE code = 'kbio_predefined_policy'
    )
  AND entity_id IN (
        SELECT id FROM "10_kbio"."15_fct_predefined_policies"
        WHERE created_by = 'system'
    );

-- Delete the predefined policy rows themselves
DELETE FROM "10_kbio"."15_fct_predefined_policies"
WHERE created_by = 'system';
