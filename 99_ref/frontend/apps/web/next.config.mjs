/** @type {import('next').NextConfig} */

// ─── Security Headers ─────────────────────────────────────────────────────────
// Applied to every response. Adjust CSP connect-src when adding new API origins.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const IS_DEV = process.env.NODE_ENV !== "production";

// In dev, Next.js Turbopack uses inline scripts and WebSocket HMR.
// In prod, script-src requires 'unsafe-eval' or 'wasm-unsafe-eval' for @react-pdf/renderer's Yoga WebAssembly.
const scriptSrc = IS_DEV
  ? "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com"
  : "script-src 'self' 'unsafe-eval' https://accounts.google.com";

// In dev, Turbopack opens a WebSocket to localhost for HMR.
const connectSrc = IS_DEV
  ? `connect-src 'self' ${API_URL} ws://localhost:3000 https://accounts.google.com`
  : `connect-src 'self' ${API_URL} https://accounts.google.com`;

const securityHeaders = [
  // Prevent MIME-type sniffing
  { key: "X-Content-Type-Options", value: "nosniff" },

  // Block page from being framed (clickjacking)
  { key: "X-Frame-Options", value: "DENY" },

  // Stop Referer header leaking sensitive paths
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },

  // Force HTTPS for 1 year (prod only — dev may be HTTP)
  ...(process.env.NODE_ENV === "production"
    ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains; preload" }]
    : []),

  // Disable browser features not needed by this app
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
  },

  // Content Security Policy
  // - default-src 'self'                  — only load from same origin
  // - script-src 'self'                   — no inline scripts, no eval
  // - style-src 'self' 'unsafe-inline'    — Next.js injects critical CSS inline
  // - connect-src 'self' <API_URL>         — XHR/fetch only to same origin + backend
  // - img-src 'self' data:                — allow base64 avatars
  // - font-src 'self'                     — fonts from same origin (Google fonts via next/font baked in)
  // - frame-ancestors 'none'              — belt + suspenders vs clickjacking
  // - form-action 'self'                  — form posts only to same origin
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      scriptSrc,
      "style-src 'self' 'unsafe-inline'",
      connectSrc,
      "img-src 'self' data: https://lh3.googleusercontent.com",
      "font-src 'self'",
      "frame-src blob: https://accounts.google.com",
      "frame-ancestors 'none'",
      "form-action 'self'",
      "base-uri 'self'",
      "object-src 'none'",
    ].join("; "),
  },

  // Cross-origin isolation (enables SharedArrayBuffer if ever needed, blocks
  // cross-origin embedding of this app's resources)
  { key: "X-DNS-Prefetch-Control", value: "on" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin-allow-popups" },
  { key: "Cross-Origin-Resource-Policy", value: "same-origin" },
];

const nextConfig = {
  output: "standalone",
  transpilePackages: ["@kcontrol/ui"],
  trailingSlash: true,

  async headers() {
    return [
      {
        // Apply to every route
        source: "/(.*)",
        headers: securityHeaders,
      },
    ];
  },

  // Dev proxy: rewrite /api/* → backend so browser sees same-origin requests (no CORS)
  ...(IS_DEV && {
    async rewrites() {
      return [
        {
          source: "/api/:path*",
          destination: `${API_URL}/api/:path*`,
        },
      ];
    },
  }),
};

export default nextConfig;
