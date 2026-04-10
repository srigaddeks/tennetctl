import { NextRequest, NextResponse } from 'next/server'

const KBIO_BACKEND = 'http://localhost:8100'

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const res = await fetch(`${KBIO_BACKEND}/v1/kbio/threat-types${url.search}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(8000),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_UNAVAILABLE', message: 'KBio backend not running' } },
      { status: 503 }
    )
  }
}
