import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_SOMACRM_API_URL:
      process.env.NEXT_PUBLIC_SOMACRM_API_URL ?? "http://localhost:51738",
  },
};

export default nextConfig;
