# syntax=docker/dockerfile:1.7
# ─────────────────────────────────────────────────────────────────────────────
# Multi-platform, cache-optimised build for the kcontrol Next.js frontend.
#
# Security notes
#   • --mount=type=cache  is build-time only — it is NEVER written into any
#     layer of the final image.  The finished image contains only what is
#     explicitly COPY'd from the builder stage.
#   • No secrets, no env files, no credentials are baked in.  All runtime
#     values are injected by env.sh at container start.
#
# Adding new npm/pnpm packages
#   pnpm install updates pnpm-lock.yaml.  The deps stage COPYs the lock file
#   first, so when the lock file changes Docker invalidates that layer and
#   re-runs pnpm install — downloading only the new/changed packages (the
#   rest are served from the BuildKit cache mount instantly).
#
# Platform independence
#   BUILDPLATFORM  = the machine running docker build  (e.g. linux/amd64 on CI,
#                    linux/arm64 on Apple Silicon)
#   TARGETPLATFORM = the platform the final image will run on (set via
#                    --platform flag or docker-compose platform: field)
#   The deps/builder stages run on BUILDPLATFORM for speed (native compilation).
#   The production stage is built for TARGETPLATFORM.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Install dependencies ─────────────────────────────────────────────
# Run on the build host's native arch so pnpm/node compile fast.
FROM --platform=$BUILDPLATFORM node:22-alpine AS deps

RUN corepack enable && corepack prepare pnpm@10.4.1 --activate

WORKDIR /app

# Copy only package manifests.  This layer is only invalidated when a manifest
# or the lock file changes — not on every source edit.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY apps/web/package.json                         ./apps/web/package.json
COPY packages/ui/package.json                      ./packages/ui/package.json
COPY packages/eslint-config/package.json           ./packages/eslint-config/package.json
COPY packages/prettier-config/package.json         ./packages/prettier-config/package.json
COPY packages/typescript-config/package.json       ./packages/typescript-config/package.json

# Cache the pnpm content-addressable store between builds.
# sharing=locked prevents corruption if two builds run in parallel (e.g. CI).
# --prefer-offline hits the cache before the network.
# --frozen-lockfile ensures the lock file is never auto-modified.
RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store,sharing=locked \
    pnpm install --frozen-lockfile --prefer-offline

# ── Stage 2: Build ────────────────────────────────────────────────────────────
FROM --platform=$BUILDPLATFORM node:22-alpine AS builder

RUN corepack enable && corepack prepare pnpm@10.4.1 --activate

WORKDIR /app

# Bring installed node_modules from deps stage (avoids re-running pnpm install)
COPY --from=deps /app ./
# Copy application source (.dockerignore excludes node_modules, .next, .turbo)
COPY . .

# Placeholder tokens — env.sh replaces these with real values at container start.
# They must be non-empty strings so Next.js bakes them into the JS bundles.
ENV NEXT_PUBLIC_API_URL=__NEXT_PUBLIC_API_URL__
ENV NEXT_PUBLIC_SITE_URL=__NEXT_PUBLIC_SITE_URL__
ENV NEXT_PUBLIC_APP_ENV=__NEXT_PUBLIC_APP_ENV__
ENV NEXT_PUBLIC_OAUTH_ENABLED=__NEXT_PUBLIC_OAUTH_ENABLED__
ENV NEXT_TELEMETRY_DISABLED=1
ENV TURBO_TELEMETRY_DISABLED=1

# Two BuildKit caches:
#   pnpm-store   — avoids re-fetching if any package slips through
#   nextjs-cache — Next.js/SWC incremental compilation cache.
#                  On code-only changes this cuts build time from ~5 min → ~30 s.
RUN --mount=type=cache,id=pnpm-store,target=/root/.local/share/pnpm/store,sharing=locked \
    --mount=type=cache,id=nextjs-cache,target=/app/apps/web/.next/cache,sharing=locked \
    pnpm build --filter=web

# Strip Windows CRLF line endings from env.sh so it runs correctly on any host
RUN sed -i 's/\r$//' /app/apps/web/env.sh

# ── Stage 3: Production runner ────────────────────────────────────────────────
# This stage targets TARGETPLATFORM — the arch the container will actually run on.
FROM --platform=$TARGETPLATFORM node:22-alpine AS production

WORKDIR /app

RUN addgroup --gid 10001 appgroup \
 && adduser  --uid 10001 --ingroup appgroup --disabled-password --gecos '' appuser

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Only the standalone output, static assets, and public files go into the image.
# The .next/cache and node_modules are NOT copied — final image stays small.
COPY --from=builder --chown=appuser:appgroup /app/apps/web/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/apps/web/.next/static      ./apps/web/.next/static
COPY --from=builder --chown=appuser:appgroup /app/apps/web/public            ./apps/web/public
COPY --from=builder --chown=appuser:appgroup /app/apps/web/env.sh            /app/env.sh

RUN chmod +x /app/env.sh

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/', r => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["/bin/sh", "-c", "/app/env.sh && node apps/web/server.js"]
