import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_TENNETCTL_BACKEND:
      process.env.NEXT_PUBLIC_TENNETCTL_BACKEND ?? "http://localhost:51734",
  },
};

export default nextConfig;
