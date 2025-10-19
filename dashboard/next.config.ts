import { config as loadEnv } from "dotenv";
import type { NextConfig } from "next";
import { join } from "path";

loadEnv({ path: join(__dirname, "..", ".env"), override: false });

function normaliseBackendUrl(candidate: string | undefined | null): string {
  if (!candidate) return "http://localhost:8000";
  const trimmed = candidate.trim();
  if (!/^https?:\/\//i.test(trimmed)) {
    return `http://${trimmed.replace(/^\/*/, "")}`.replace(/\/+$/, "");
  }
  return trimmed.replace(/\/+$/, "");
}

const backendTarget = normaliseBackendUrl(process.env.BACKEND_INTERNAL_URL);

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendTarget}/api/:path*`,
      },
      {
        source: "/ws",
        destination: `${backendTarget}/ws`,
      },
    ];
  },
};

export default nextConfig;
