import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://localhost:8200'

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const res = await fetch(`${BACKEND}/v1/kprotect/policy-sets/${id}`, {
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

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const body = await request.json()
    const res = await fetch(`${BACKEND}/v1/kprotect/policy-sets/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
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

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const res = await fetch(`${BACKEND}/v1/kprotect/policy-sets/${id}`, {
      method: 'DELETE',
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
