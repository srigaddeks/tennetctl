# Environment Configuration

This project uses environment variables to manage configuration across different environments (development, staging, production).

## 🛠️ Local Development

For local development, we use `.env.local` files which are excluded from source control.

### Web Application (`apps/web`)

Create a `.env.local` file in `apps/web/`:

```bash
# Example environment variables
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

### Shared Configuration

If a package needs environment variables, it should typically receive them via props or a provider from the consuming application, rather than accessing `process.env` directly, to ensure portability.

## 🔒 Secret Management

**Never commit `.env` files or secrets to GitHub.**

- Use the provided `.env.example` as a template for new variables.
- Secrets for production are managed via the hosting platform (e.g., Vercel, AWS Secrets Manager) or CI/CD secrets (GitHub Actions).

## 🧪 Adding New Variables

When adding a new environment variable:
1. Update `.env.example` in the relevant app/package.
2. Document the variable's purpose here if it's a core system variable.
3. Inform the team so they can update their local `.env.local` files.
