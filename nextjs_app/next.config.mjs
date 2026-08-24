const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/:path*` },
      { source: "/public/sections/:path*", destination: `${BACKEND_URL}/public/sections/:path*` },
    ];
  },
};

export default nextConfig;
