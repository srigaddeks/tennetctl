import { NextRequest, NextResponse } from 'next/server'

const TENNETCTL = process.env.TENNETCTL_URL ?? 'http://localhost:58000'

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const body = await req.json()
    const res = await fetch(`${TENNETCTL}/v1/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: body.username,
        email: body.email,
        password: body.password,
        org_name: `${body.username}-org`,
        default_workspace_name: 'kprotect',
      }),
      signal: AbortSignal.timeout(10_000),
    })
    const data = await res.json()
    if (!res.ok) {
      return NextResponse.json(
        { ok: false, error: { code: 'REGISTRATION_FAILED', message: data.detail ?? 'Registration failed' } },
        { status: res.status },
      )
    }
    const { user, org, workspace, access_token, session_id } = data.data
    return NextResponse.json({
      ok: true,
      data: {
        access_token,
        session_id,
        user_id: user.id,
        username: user.username,
        org_id: org.id,
        workspace_id: workspace.id,
      },
    }, { status: 201 })
  } catch (err) {
    return NextResponse.json(
      { ok: false, error: { code: 'BACKEND_ERROR', message: String(err) } },
      { status: 503 },
    )
  }
}
