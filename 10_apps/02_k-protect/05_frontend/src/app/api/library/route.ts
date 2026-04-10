import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://localhost:8200'

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url)
    const res = await fetch(`${BACKEND}/v1/kprotect/library${url.search}`, {
      headers: { 'Content-Type': 'application/json' },
      signal: AbortSignal.timeout(8000),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch {
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_UNAVAILABLE', message: 'KProtect backend not running' } },
      { status: 503 }
    )
  }
}
