/**
 * Next.js configuration - Proxy API requests to FastAPI backend
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Proxy configuration - Routes /api/* requests to FastAPI backend
  async rewrites() {
    const apiEndpoint = process.env.NEXT_PUBLIC_API_ENDPOINT || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',  // Frontend endpoint pattern
        destination: `${apiEndpoint}/api/:path*`  // Backend server URL from env
      }
    ];
  }
};

module.exports = nextConfig;
