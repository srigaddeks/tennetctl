import { NextRequest, NextResponse } from 'next/server'

const TENNETCTL = process.env.TENNETCTL_URL ?? 'http://localhost:58000'

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const body = await req.json()
    const res = await fetch(`${TENNETCTL}/v1/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: body.username, password: body.password }),
      signal: AbortSignal.timeout(10_000),
    })
    const data = await res.json()
    if (!res.ok) {
      return NextResponse.json(
        { ok: false, error: { code: 'INVALID_CREDENTIALS', message: 'Invalid username or password' } },
        { status: 401 },
      )
    }
    const { access_token, session_id } = data.data

    // Decode JWT payload to get org_id (oid) and workspace_id (wid)
    const [, payloadB64] = access_token.split('.')
    const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString())
    const org_id: string = payload.oid ?? ''
    const workspace_id: string = payload.wid ?? ''

    if (!org_id || !workspace_id) {
      return NextResponse.json(
        { ok: false, error: { code: 'NO_ORG', message: 'Account has no org — please register first' } },
        { status: 422 },
      )
    }

    // Fetch username from sessions/me
    const meRes = await fetch(`${TENNETCTL}/v1/sessions/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
      signal: AbortSignal.timeout(5_000),
    })
    const me = meRes.ok ? (await meRes.json()).data : {}

    return NextResponse.json({
      ok: true,
      data: {
        access_token,
        session_id,
        user_id: me.user_id ?? payload.sub,
        username: me.username ?? body.username,
        org_id,
        workspace_id,
      },
    })
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_ERROR', message: String(err) } },
      { status: 503 },
    )
  }
}
