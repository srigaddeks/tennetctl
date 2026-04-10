/**
 * Local batch ingestion endpoint.
 *
 * Forwards batches to the real scoring backend at localhost:8100.
 * Returns error if backend is unavailable — no mock fallback.
 * Always saves batches to disk for debugging.
 */

import { NextRequest, NextResponse } from 'next/server';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';

const BATCH_DIR = join(process.cwd(), '..', '..', 'tmp', 'kp-batches');
const KBIO_BACKEND_URL = process.env.KBIO_BACKEND_URL ?? 'http://localhost:8100';
const KBIO_URL = `${KBIO_BACKEND_URL}/v1/internal/ingest`;
const API_KEY = process.env.KBIO_API_KEY ?? 'kbio_demo_site_dev_key_2026';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    // Read body — handle both gzip and plain JSON
    const contentEncoding = request.headers.get('content-encoding');
    let bodyText: string;

    if (contentEncoding === 'gzip') {
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

    // Extract security headers for logging
    const keyId = request.headers.get('x-kp-key-id');
    const authToken = request.headers.get('x-kp-auth-token');
    const unsigned = request.headers.get('x-kp-unsigned');
    const authMethod = authToken ? 'hmac' : (unsigned ? 'unsigned' : 'legacy');
    console.log(`[KP] Auth: method=${authMethod} key_id=${keyId ?? 'none'}`);

    // Save batch to disk for debugging (fire-and-forget)
    const sessionId = (batch.session_id ?? batch.header?.session_id ?? 'unknown').slice(0, 8);
    const pulse = batch.pulse ?? batch.header?.pulse_number ?? 0;
    const batchType = batch.type ?? 'unknown';
    const timestamp = Date.now();
    const filename = `${sessionId}_p${String(pulse).padStart(4, '0')}_${batchType}_${timestamp}.json`;

    mkdir(BATCH_DIR, { recursive: true })
      .then(() => writeFile(
        join(BATCH_DIR, filename),
        JSON.stringify({ ...batch, _demo_meta: { auth_method: authMethod, received_at: new Date().toISOString() } }, null, 2),
        'utf-8',
      ))
      .then(() => console.log(`[KP] Saved batch: ${filename}`))
      .catch(err => console.warn(`[KP] Failed to save batch: ${err}`));

    // Forward to real V2 scoring backend
    try {
      const backendRes = await fetch(KBIO_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: bodyText,
        signal: AbortSignal.timeout(5000),
      });

      if (!backendRes.ok) {
        const errText = await backendRes.text().catch(() => 'unknown');
        console.warn(`[KP] Backend returned ${backendRes.status}: ${errText.slice(0, 200)}`);
        return NextResponse.json(
          { ok: false, error: { code: 'BACKEND_ERROR', message: `Backend returned ${backendRes.status}` } },
          { status: backendRes.status },
        );
      }

      const v2Data = await backendRes.json();
      console.log(`[KP] V2 scores received: action=${v2Data.data?.verdict?.action ?? 'unknown'} processing=${v2Data.data?.processing_ms?.toFixed(0) ?? '?'}ms`);
      return NextResponse.json(v2Data);
    } catch (backendErr) {
      console.warn(`[KP] Backend unavailable: ${backendErr}`);
      return NextResponse.json(
        { ok: false, error: { code: 'BACKEND_UNAVAILABLE', message: 'Scoring backend is not running' } },
        { status: 503 },
      );
    }
  } catch (err) {
    console.error('[KP] Ingest error:', err);
    return NextResponse.json(
      { ok: false, error: { code: 'SERVER_ERROR', message: String(err) } },
      { status: 500 },
    );
  }
}

