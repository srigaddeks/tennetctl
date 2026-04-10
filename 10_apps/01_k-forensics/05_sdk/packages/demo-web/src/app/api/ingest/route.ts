export async function POST(req: Request) {
  const body = await req.text()

  try {
    const res = await fetch('http://localhost:8100/v1/internal/ingest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Internal-Service-Token': 'kbio-dev-internal-token',
      },
      body,
    })
    const data = await res.json()
    return Response.json(data)
  } catch {
    return Response.json(
      { ok: false, error: { code: 'KBIO_UNAVAILABLE', message: 'kbio backend is not running' } },
      { status: 503 },
    )
  }
}
