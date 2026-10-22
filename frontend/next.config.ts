import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  // The installed Next CLI fails while parsing TypeScript --showConfig.
  // `npm run build` runs `tsc --noEmit` before this step.
  typescript: {
    ignoreBuildErrors: true,
  },
  async rewrites() {
    const defaultOrigin =
      process.env.NODE_ENV === 'production'
        ? 'https://ilm.mehedi.blitz.cloud'
        : 'http://127.0.0.1:8000';
    const djangoOrigin = (
      process.env.API_ORIGIN ||
      process.env.NEXT_PUBLIC_API_ORIGIN ||
      defaultOrigin
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
