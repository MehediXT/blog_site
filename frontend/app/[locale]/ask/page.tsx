import { notFound } from 'next/navigation';
import { QuestionComposer } from '../../../components/account';
import { Footer, Header } from '../../../components/site';
import { getCategories, isLocale, type Locale } from '../../../lib/api';

export default async function AskPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const categoryData = await getCategories();

  return <div className="site-shell" lang={locale}><Header locale={locale} /><main className="ask-main"><QuestionComposer locale={locale} categories={categoryData?.results || []} /></main><Footer locale={locale} /></div>;
}
