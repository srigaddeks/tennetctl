/**
 * Challenge API proxy.
 * Routes generate/verify requests to the real backend challenge endpoints.
 */

import { NextRequest, NextResponse } from 'next/server';

const KBIO_BACKEND_URL = process.env.KBIO_BACKEND_URL ?? 'http://localhost:8100';
const KBIO_BASE = `${KBIO_BACKEND_URL}/v1/internal/challenge`;
const SERVICE_TOKEN = process.env.KBIO_SERVICE_TOKEN ?? 'kbio-dev-internal-token';

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { action, ...params } = body;

    if (action !== 'generate' && action !== 'verify') {
      return NextResponse.json(
        { ok: false, error: { code: 'INVALID_ACTION', message: `Unknown action: ${action}` } },
        { status: 400 },
      );
    }

    const url = `${KBIO_BASE}/${action}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Service-Token': SERVICE_TOKEN,
      },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(5000),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    console.warn(`[KP-Challenge] Error: ${err}`);
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_UNAVAILABLE', message: 'Challenge backend is not running' } },
      { status: 503 },
    );
  }
}
