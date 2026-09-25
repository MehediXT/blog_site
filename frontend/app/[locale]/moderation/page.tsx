import { notFound } from 'next/navigation';
import { ModerationPanel } from '../../../components/moderation';
import { Footer, Header } from '../../../components/site';
import { isLocale, type Locale } from '../../../lib/api';

export default async function ModerationPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;

  return <div className="site-shell" lang={locale}>
    <Header locale={locale} />
    <main className="moderation-main"><ModerationPanel locale={locale} /></main>
    <Footer locale={locale} />
  </div>;
}
