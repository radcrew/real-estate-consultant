import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Headless UI pulls in react-aria; webpack dev matches production and avoids Turbopack HMR issues.
  transpilePackages: ["@headlessui/react"],
  // Dev-only (dev:turbo): pnpm workspace hoists deps to the repo root.
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
      {
        protocol: "https",
        hostname: "images.pexels.com",
        pathname: "/**",
      },
      {
        // Supabase Storage public URLs (e.g. profile avatars).
        protocol: "https",
        hostname: "*.supabase.co",
        pathname: "/storage/v1/object/public/**",
      },
    ],
  },
};

export default nextConfig;
