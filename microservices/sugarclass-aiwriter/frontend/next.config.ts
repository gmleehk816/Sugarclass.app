import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Base path for sub-path deployment (e.g., sugarclass.app/aiwriter)
  basePath: '/aiwriter',
  trailingSlash: true,

  // Output mode for Docker deployment
  output: 'standalone',

  // Disable React Compiler for faster development builds
  reactCompiler: false,

  // Optimize for development
  compiler: {
    removeConsole: process.env.NODE_ENV === "production",
  },

  // Speed up compilation with package optimization
  experimental: {
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Environment variables exposed to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
