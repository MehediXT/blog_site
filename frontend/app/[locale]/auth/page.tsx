import { notFound } from 'next/navigation';
import { AuthPanel } from '../../../components/account';
import { isLocale, type Locale } from '../../../lib/api';

export default async function AuthPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;

  return <main className="auth-page" lang={locale}><AuthPanel locale={locale} /></main>;
}
