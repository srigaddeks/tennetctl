# Contributing to TennetCTL

## Development Setup

```bash
# Clone and install
git clone https://github.com/your-org/tennetctl
cd tennetctl

# Python environment (3.13+)
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Start backend
.venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0 --reload

# Frontend (Node 20+)
cd frontend && npm install && npm run dev
```

## Architecture

See [CLAUDE.md](./CLAUDE.md) for the full coding guide and architectural decisions.

Key points:
- Backend: Python 3.13 + FastAPI + asyncpg (no ORM, raw SQL)
- Frontend: Next.js + Tailwind CSS
- Database: PostgreSQL with PG-specific features (RLS, advisory locks)
- All IDs are UUID v7

## Workflow

1. **Research first** — check existing code before writing new
2. **Tests first** — write failing test (RED), then implementation (GREEN)
3. **One concern per PR** — keep scope tight
4. **Commit format**: `feat|fix|refactor|docs|test|chore: description`

## Testing

```bash
# Backend tests
.venv/bin/pytest tests/ -q --ignore=tests/features/05_monitoring/test_dlq_replay.py

# Frontend type check
cd frontend && npx tsc --noEmit
```

## Pull Requests

- Target the `main` branch
- Include a clear description of the change and why
- Ensure all tests pass
- One logical change per PR

## Reporting Issues

Use [GitHub Issues](https://github.com/your-org/tennetctl/issues). Include:
- TennetCTL version
- Steps to reproduce
- Expected vs actual behavior

## Security Issues

See [SECURITY.md](./SECURITY.md) for responsible disclosure.
