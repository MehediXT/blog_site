import './globals.css';
import type { Metadata } from 'next';
import { headers } from 'next/headers';

export async function generateMetadata(): Promise<Metadata> {
  const incomingHeaders = await headers();
  const host = incomingHeaders.get('x-forwarded-host') || incomingHeaders.get('host') || 'localhost:3000';
  const protocol = incomingHeaders.get('x-forwarded-proto') || (host.startsWith('localhost') ? 'http' : 'https');
  const baseUrl = `${protocol}://${host}`;
  const title = 'Universe of Ilm';
  const description = 'Reviewed Islamic guidance in Bangla and English, with privacy and independent scholarly review built in.';

  return {
    metadataBase: new URL(baseUrl),
    title: { default: title, template: `%s — ${title}` },
    description,
    applicationName: title,
    keywords: ['Islamic guidance', 'fatwa', 'Bangla', 'scholars', 'reviewed answers'],
    openGraph: {
      type: 'website',
      siteName: title,
      title,
      description,
      images: [{ url: `${baseUrl}/og.png`, width: 1733, height: 907, alt: 'Universe of Ilm — reviewed guidance, shared with care' }],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [`${baseUrl}/og.png`],
    },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="bn" data-scroll-behavior="smooth"><body><a className="skip-link" href="#site-content">Skip to content</a><div id="site-content">{children}</div></body></html>;
}
