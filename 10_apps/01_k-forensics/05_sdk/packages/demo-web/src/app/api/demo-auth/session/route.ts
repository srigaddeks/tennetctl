import { NextRequest, NextResponse } from 'next/server'

const KBIO_URL = (process.env.KBIO_BACKEND_URL ?? 'http://localhost:8100') + '/v1/demo-auth/session'
const API_KEY = process.env.KBIO_API_KEY ?? 'kbio_demo_site_dev_key_2026'

export async function GET(req: NextRequest): Promise<NextResponse> {
  try {
    const token = req.headers.get('authorization') ?? ''
    const res = await fetch(KBIO_URL, {
      headers: { 'X-API-Key': API_KEY, 'Authorization': token },
      signal: AbortSignal.timeout(5_000),
    })
    const data = await res.json()
    return NextResponse.json(data, { status: res.status })
  } catch (err) {
    return NextResponse.json({ ok: false, error: { code: 'BACKEND_ERROR', message: String(err) } }, { status: 503 })
  }
}
