import { config as loadEnv } from "dotenv";
import type { NextConfig } from "next";
import { join } from "path";

loadEnv({ path: join(__dirname, "..", ".env"), override: false });

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
