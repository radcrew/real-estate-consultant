import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Dev-only: pnpm workspace hoists deps to the repo root; avoids Turbopack resolving from app/.
  turbopack: {
    root: path.join(__dirname, ".."),
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "api.apify.com",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
