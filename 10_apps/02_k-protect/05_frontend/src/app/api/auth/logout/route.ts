import { NextRequest, NextResponse } from 'next/server'

const TENNETCTL = process.env.TENNETCTL_URL ?? 'http://localhost:58000'

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const token = req.headers.get('authorization') ?? ''
    if (token) {
      await fetch(`${TENNETCTL}/v1/sessions`, {
        method: 'DELETE',
        headers: { Authorization: token },
        signal: AbortSignal.timeout(5_000),
      })
    }
    return new NextResponse(null, { status: 204 })
  } catch {
    return new NextResponse(null, { status: 204 }) // best-effort
  }
}
