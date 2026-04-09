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
    // If kbio backend is not running, return a mock response
    return Response.json({
      ok: true,
      data: {
        batch_id: 'mock',
        processed_at: Date.now(),
        drift_score: Math.random() * 0.3,
        confidence: 0.6,
        action: 'allow',
      },
    })
  }
}
