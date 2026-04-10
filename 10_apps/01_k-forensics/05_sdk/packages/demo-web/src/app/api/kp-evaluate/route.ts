/**
 * kprotect evaluate proxy.
 *
 * Forwards evaluation requests to kprotect backend at localhost:18100.
 * Called by the demo site after each kbio ingest to get policy decisions.
 */

import { NextRequest, NextResponse } from 'next/server'

const KPROTECT_URL = (process.env.KPROTECT_BACKEND_URL ?? 'http://localhost:8200') + '/v1/evaluate'
const API_KEY = process.env.KPROTECT_API_KEY ?? 'kprotect_demo_dev_key_2026'

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.text()

    const res = await fetch(KPROTECT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body,
      signal: AbortSignal.timeout(8000),
    })

    if (!res.ok) {
      const errText = await res.text().catch(() => 'unknown')
      return NextResponse.json(
        { ok: false, error: { code: 'KPROTECT_ERROR', message: `kprotect returned ${res.status}: ${errText.slice(0, 200)}` } },
        { status: res.status },
      )
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    if (err instanceof Error && err.name === 'TimeoutError') {
      return NextResponse.json(
        { ok: false, error: { code: 'KPROTECT_TIMEOUT', message: 'kprotect backend timed out' } },
        { status: 504 },
      )
    }
    return NextResponse.json(
      { ok: false, error: { code: 'KPROTECT_UNAVAILABLE', message: 'kprotect backend is not running' } },
      { status: 503 },
    )
  }
}
