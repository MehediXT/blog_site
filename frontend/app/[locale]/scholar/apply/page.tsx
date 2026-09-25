import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { ScholarApplicationForm } from '../../../../components/scholar-application';
import { Footer, Header } from '../../../../components/site';
import { isLocale, type Locale } from '../../../../lib/api';

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  return { title: locale === 'bn' ? 'স্কলার প্রোফাইল আবেদন' : 'Scholar profile application' };
}

export default async function ScholarApplicationPage({ params }: Props) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;

  return <div className="site-shell" lang={locale}><Header locale={locale} /><main className="scholar-application-main"><ScholarApplicationForm locale={locale} /></main><Footer locale={locale} /></div>;
}
