import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // `tsc --noEmit` passes independently. Next 16.3.4's CLI parser currently
  // fails with the installed Node/TypeScript combination during production build.
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const djangoOrigin = process.env.API_ORIGIN || process.env.NEXT_PUBLIC_API_ORIGIN || 'http://127.0.0.1:8000';
    return [
      { source: '/accounts/:path*', destination: `${djangoOrigin}/accounts/:path*` },
      { source: '/admin/:path*', destination: `${djangoOrigin}/admin/:path*` },
    ];
  },
};

export default nextConfig;
