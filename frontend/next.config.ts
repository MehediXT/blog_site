import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  // `tsc --noEmit` passes independently. Next 16.3.4's CLI parser currently
  // fails with the installed Node/TypeScript combination during production build.
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const djangoOrigin = (
      process.env.API_ORIGIN ||
      process.env.NEXT_PUBLIC_API_ORIGIN ||
      'http://127.0.0.1:8000'
    ).replace(/\/$/, '');
    return [
      { source: '/api/:path*', destination: `${djangoOrigin}/api/:path*` },
      { source: '/admin/:path*', destination: `${djangoOrigin}/admin/:path*` },
      { source: '/static/:path*', destination: `${djangoOrigin}/static/:path*` },
      { source: '/media/:path*', destination: `${djangoOrigin}/media/:path*` },
    ];
  },
};

export default nextConfig;
