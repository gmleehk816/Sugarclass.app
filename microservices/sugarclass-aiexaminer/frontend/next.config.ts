import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || '',
  // Use standalone output for smaller docker images
  output: 'standalone',
};

export default nextConfig;
