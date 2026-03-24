import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  images: {
    dangerouslyAllowSVG: true,
    // contentDispositionType: 'attachment',
    // contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    remotePatterns: [
      {
        hostname: 'localhost',
        port: '9000',
      },
      {
        hostname: '127.0.0.1',
        port: '9000',
      },
      {
        protocol: 'https',
        hostname: '**',
        pathname: '/**',
      },
    ],
  },
  turbopack: {
    root: './',
  },
  async rewrites() {
    return [
      {
        // 1. The Frontend path (what the browser sees)
        source: '/api/:path*',
        // 2. The Backend path (where Django lives)
        destination: `${process.env.API_ENDPOINT || 'http://localhost:8000'}/:path*`,
      },
    ]
  },
}

export default nextConfig
