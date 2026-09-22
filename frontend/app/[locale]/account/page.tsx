import { notFound } from 'next/navigation';
import { AccountPanel } from '../../../components/account';
import { Footer, Header } from '../../../components/site';
import { isLocale, type Locale } from '../../../lib/api';

export default async function AccountPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;

  return <div className="site-shell" lang={locale}><Header locale={locale} /><main className="account-main"><AccountPanel locale={locale} /></main><Footer locale={locale} /></div>;
}
