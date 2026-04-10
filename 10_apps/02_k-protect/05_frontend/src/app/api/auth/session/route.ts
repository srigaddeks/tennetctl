import { NextRequest, NextResponse } from 'next/server'

const TENNETCTL = process.env.TENNETCTL_URL ?? 'http://localhost:58000'

export async function GET(req: NextRequest): Promise<NextResponse> {
  try {
    const token = req.headers.get('authorization') ?? ''
    if (!token) {
      return NextResponse.json(
        { ok: false, error: { code: 'UNAUTHORIZED', message: 'No token' } },
        { status: 401 },
      )
    }
    const res = await fetch(`${TENNETCTL}/v1/sessions/me`, {
      headers: { Authorization: token },
      signal: AbortSignal.timeout(5_000),
    })
    if (!res.ok) {
      return NextResponse.json(
        { ok: false, error: { code: 'INVALID_TOKEN', message: 'Token invalid or expired' } },
        { status: 401 },
      )
    }
    const data = await res.json()

    // Decode JWT to get org_id / workspace_id from token claims
    const jwt = token.replace(/^Bearer\s+/i, '')
    const [, payloadB64] = jwt.split('.')
    const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString())

    return NextResponse.json({
      ok: true,
      data: {
        user_id: data.data.user_id,
        username: data.data.username,
        org_id: payload.oid ?? '',
        workspace_id: payload.wid ?? '',
      },
    })
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_ERROR', message: String(err) } },
      { status: 503 },
    )
  }
}
