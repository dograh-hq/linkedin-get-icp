/**
 * Next.js configuration - Proxy API requests to FastAPI backend
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy configuration - Routes /api/* requests to FastAPI backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',  // Frontend endpoint pattern
        destination: 'http://localhost:8000/api/:path*'  // Backend server URL
      }
    ];
  }
};

module.exports = nextConfig;
