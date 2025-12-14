import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone', // Docker deployment optimization
  
  // Proxy API requests to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL 
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`
          : 'http://api:8000/api/:path*', // In Docker, use service name
      },
    ];
  },
};

export default nextConfig;
