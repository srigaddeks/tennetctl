import { NextRequest, NextResponse } from 'next/server'

const KBIO_URL = (process.env.KBIO_BACKEND_URL ?? 'http://localhost:8100') + '/v1/demo-auth/logout'
const API_KEY = process.env.KBIO_API_KEY ?? 'kbio_demo_site_dev_key_2026'

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const token = req.headers.get('authorization') ?? ''
    const res = await fetch(KBIO_URL, {
      method: 'POST',
      headers: { 'X-API-Key': API_KEY, 'Authorization': token },
      signal: AbortSignal.timeout(5_000),
    })
    if (res.status === 204) return new NextResponse(null, { status: 204 })
    return NextResponse.json({ ok: true }, { status: 200 })
  } catch {
    return NextResponse.json({ ok: true }) // best-effort
  }
}
