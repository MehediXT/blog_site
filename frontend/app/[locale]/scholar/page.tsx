import { notFound } from 'next/navigation';
import { ScholarPanel } from '../../../components/scholar';
import { Footer, Header } from '../../../components/site';
import { getMethodologies, isLocale, type Locale, type Methodology } from '../../../lib/api';

export default async function ScholarPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  let methodologies: Methodology[] = [];
  try {
    methodologies = await getMethodologies();
  } catch {
    methodologies = [];
  }

  return <div className="site-shell" lang={locale}><Header locale={locale} /><main className="scholar-main"><ScholarPanel locale={locale} methodologies={methodologies} /></main><Footer locale={locale} /></div>;
}
