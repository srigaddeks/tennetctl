import { NextRequest, NextResponse } from 'next/server'

const KBIO_URL = (process.env.KBIO_BACKEND_URL ?? 'http://localhost:8100') + '/v1/demo-auth/register'
const API_KEY = process.env.KBIO_API_KEY ?? 'kbio_demo_site_dev_key_2026'

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const res = await fetch(KBIO_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
      body: await req.text(),
      signal: AbortSignal.timeout(10_000),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json({ ok: false, error: { code: 'BACKEND_ERROR', message: String(err) } }, { status: 503 })
  }
}
