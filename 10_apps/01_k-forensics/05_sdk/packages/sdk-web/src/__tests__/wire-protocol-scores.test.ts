/**
 * wire-protocol-scores.test.ts
 *
 * Verify DriftScoreResponse type includes all 4 scores.
 * This is a compile-time check — if the types are wrong, this won't build.
 */

import { describe, it, expect } from 'vitest';
import type { DriftScoreResponse } from '../runtime/wire-protocol.js';

describe('DriftScoreResponse type', () => {
  it('includes all score fields', () => {
    const response: DriftScoreResponse = {
      batch_id: 'test-batch-id',
      processed_at: Date.now(),
      drift_score: 0.25,
      confidence: 0.8,
      signal_scores: { keystroke: 0.2, pointer: 0.3 },
      action: 'allow',
      anomaly_score: 0.15,
      trust_score: 0.85,
      bot_score: 0.05,
      auth_state: {
        session_trust: 'trusted',
        device_known: true,
        baseline_age_days: 30,
        baseline_quality: 'strong',
      },
    };

    expect(response.drift_score).toBe(0.25);
    expect(response.anomaly_score).toBe(0.15);
    expect(response.trust_score).toBe(0.85);
    expect(response.bot_score).toBe(0.05);
    expect(response.action).toBe('allow');
  });

  it('allows optional decision_id and policy_id', () => {
    const response: DriftScoreResponse = {
      batch_id: 'test-batch-id',
      processed_at: Date.now(),
      drift_score: 0.7,
      confidence: 0.9,
      signal_scores: {},
      action: 'challenge',
      anomaly_score: 0.6,
      trust_score: 0.3,
      bot_score: 0.1,
      decision_id: 'decision-123',
      policy_id: 'POL_FRAUD_001',
      auth_state: {
        session_trust: 'suspicious',
        device_known: true,
        baseline_age_days: 5,
        baseline_quality: 'forming',
      },
    };

    expect(response.decision_id).toBe('decision-123');
    expect(response.policy_id).toBe('POL_FRAUD_001');
  });
});
