import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Universe of Ilm',
  description: 'Reviewed Islamic guidance in Bangla and English.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="bn"><body>{children}</body></html>;
}
