/**
 * Local batch ingestion endpoint.
 *
 * Instead of sending to api.kprotect.io, the demo SDK sends to this
 * Next.js API route which saves each batch as a JSON file:
 *
 *   /tmp/kp-batches/{session_id}_{pulse}.json
 *
 * This lets Sri review the raw behavioral data locally.
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

const BATCH_DIR = join(process.cwd(), '..', '..', 'tmp', 'kp-batches');

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    // Read body — handle both gzip and plain JSON
    const contentEncoding = request.headers.get('content-encoding');
    let bodyText: string;

    if (contentEncoding === 'gzip') {
      // Decompress gzip body
      const body = await request.arrayBuffer();
      const ds = new DecompressionStream('gzip');
      const writer = ds.writable.getWriter();
      writer.write(new Uint8Array(body));
      writer.close();
      const reader = ds.readable.getReader();
      const chunks: Uint8Array[] = [];
      let done = false;
      while (!done) {
        const result = await reader.read();
        done = result.done;
        if (result.value) chunks.push(result.value);
      }
      const decoder = new TextDecoder();
      bodyText = chunks.map(c => decoder.decode(c, { stream: true })).join('') + decoder.decode();
    } else {
      bodyText = await request.text();
    }

    const batch = JSON.parse(bodyText);

    // Extract security headers
    const keyId = request.headers.get('x-kp-key-id');
    const authToken = request.headers.get('x-kp-auth-token');
    const authTimestamp = request.headers.get('x-kp-auth-timestamp');
    const nonce = request.headers.get('x-kp-nonce');
    const signature = request.headers.get('x-kp-signature');
    const unsigned = request.headers.get('x-kp-unsigned');
    const checksum = request.headers.get('x-kp-checksum');
    const originHash = request.headers.get('x-kp-origin-hash');

    // Log security context
    const authMethod = authToken ? 'hmac' : (unsigned ? 'unsigned' : 'legacy');
    console.log(`[KP] Auth: method=${authMethod} key_id=${keyId ?? 'none'} nonce=${nonce ?? 'none'}`);
    if (checksum) console.log(`[KP] Checksum: ${checksum.slice(0, 16)}...`);
    if (originHash) console.log(`[KP] Origin-Hash: ${originHash.slice(0, 16)}...`);
    if (signature) console.log(`[KP] Signature: ${signature.slice(0, 16)}...`);

    // Validate HMAC auth (soft — warn on failure, don't reject in demo mode)
    if (authToken && keyId && authTimestamp && nonce) {
      try {
        const apiKey = 'kp_test_demo'; // Known demo key
        const encoder = new TextEncoder();
        const key = await crypto.subtle.importKey(
          'raw',
          encoder.encode(apiKey),
          { name: 'HMAC', hash: 'SHA-256' },
          false,
          ['verify', 'sign'],
        );
        const expectedMessage = `${authTimestamp}.${nonce}`;
        const expectedSig = await crypto.subtle.sign('HMAC', key, encoder.encode(expectedMessage));
        const expectedHex = Array.from(new Uint8Array(expectedSig))
          .map(b => b.toString(16).padStart(2, '0'))
          .join('');

        if (expectedHex === authToken) {
          console.log(`[KP] ✓ HMAC auth verified for key_id=${keyId}`);
        } else {
          console.warn(`[KP] ✗ HMAC auth FAILED for key_id=${keyId}`);
        }
      } catch (err) {
        console.warn(`[KP] HMAC verification error:`, err);
      }
    } else if (unsigned) {
      console.warn(`[KP] ⚠ Unsigned batch received`);
    }

    // Log sendBeacon auth (can't set custom headers, key is in body)
    if (batch.api_key_id) {
      console.log(`[KP] sendBeacon auth: key_id=${batch.api_key_id}`);
    }

    // Build filename: {session_id}_{pulse}_{type}.json
    const sessionId = (batch.session_id ?? 'unknown').slice(0, 8);
    const pulse = batch.pulse ?? 0;
    const batchType = batch.type ?? 'unknown';
    const timestamp = Date.now();
    const filename = `${sessionId}_p${String(pulse).padStart(4, '0')}_${batchType}_${timestamp}.json`;

    // Ensure directory exists
    await mkdir(BATCH_DIR, { recursive: true });

    // Write pretty-printed JSON
    const filePath = join(BATCH_DIR, filename);
    const batchWithMeta = {
      ...batch,
      _demo_meta: {
        auth_method: authToken ? 'hmac' : (unsigned ? 'unsigned' : 'legacy'),
        key_id: keyId,
        nonce,
        signature: signature ?? null,
        checksum: checksum ?? null,
        origin_hash: originHash ?? null,
        received_at: new Date().toISOString(),
      },
    };
    await writeFile(filePath, JSON.stringify(batchWithMeta, null, 2), 'utf-8');

    // Log to console for dev visibility
    console.log(`[KP] Saved batch: ${filename} (${batchType}, pulse=${pulse})`);

    // Return a fake DriftScoreResponse
    const response = {
      ok: true,
      data: {
        batch_id: batch.batch_id ?? 'unknown',
        processed_at: Date.now(),
        drift_score: Math.random() * 0.3, // low drift for testing
        confidence: Math.min(0.5 + pulse * 0.02, 0.95),
        signal_scores: {
          keystroke: Math.random() * 0.2,
          pointer: Math.random() * 0.15,
          credential: Math.random() * 0.1,
        },
        action: 'allow' as const,
        auth_state: {
          session_trust: 'trusted' as const,
          device_known: true,
          baseline_age_days: 0,
          baseline_quality: 'forming' as const,
        },
        alerts: [],
      },
    };

    return NextResponse.json(response);
  } catch (err) {
    console.error('[KP] Ingest error:', err);
    return NextResponse.json(
      { ok: false, error: { code: 'SERVER_ERROR', message: String(err) } },
      { status: 500 },
    );
  }
}
