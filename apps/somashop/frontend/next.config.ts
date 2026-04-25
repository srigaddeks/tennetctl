import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_SOMASHOP_API_URL:
      process.env.NEXT_PUBLIC_SOMASHOP_API_URL ?? "http://localhost:51740",
    NEXT_PUBLIC_TENNETCTL_BACKEND:
      process.env.NEXT_PUBLIC_TENNETCTL_BACKEND ?? "http://localhost:51734",
  },
};

export default nextConfig;
