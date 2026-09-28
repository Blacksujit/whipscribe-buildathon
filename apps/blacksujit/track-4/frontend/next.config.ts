import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["127.0.0.1"],
  async redirects() {
    return [{ source: "/settings", destination: "/connections", permanent: false }];
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.join(process.cwd(), "src"),
    };
    return config;
  },
};

export default nextConfig;
