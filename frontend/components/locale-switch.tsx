'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import type { Locale } from '../lib/api';

export function LocaleSwitch({ locale }: { locale: Locale }) {
  const pathname = usePathname();
  const otherLocale = locale === 'bn' ? 'en' : 'bn';
  const nextPath = pathname.replace(/^\/(bn|en)(?=\/|$)/, `/${otherLocale}`);

  return (
    <Link className="locale-switch" href={nextPath || `/${otherLocale}`} aria-label={otherLocale === 'bn' ? 'বাংলায় দেখুন' : 'View in English'}>
      {otherLocale === 'bn' ? 'বাংলা' : 'EN'}
    </Link>
  );
}
