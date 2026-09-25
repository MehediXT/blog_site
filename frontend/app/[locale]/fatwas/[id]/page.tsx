import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Footer, Header, text } from '../../../../components/site';
import { FatwaActions } from '../../../../components/fatwa-actions';
import { getFatwa, isLocale, type Locale } from '../../../../lib/api';

type Props = { params: Promise<{ locale: string; id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale: rawLocale, id } = await params;
  if (!isLocale(rawLocale)) return {};
  const data = await getFatwa(rawLocale, id);
  if (!data?.fatwa) return {};
  const description = data.fatwa.question.replace(/\s+/g, ' ').slice(0, 160);
  return {
    title: data.fatwa.title,
    description,
    alternates: { canonical: `/${rawLocale}/fatwas/${id}` },
    openGraph: { title: data.fatwa.title, description, images: [] },
    twitter: { card: 'summary', title: data.fatwa.title, description, images: [] },
  };
}

export default async function FatwaDetail({ params }: Props) {
  const { locale: rawLocale, id } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const data = await getFatwa(locale, id);
  if (!data?.fatwa) notFound();
  const fatwa = data.fatwa;
  const t = text(locale);
  const references = Array.isArray(fatwa.references) ? fatwa.references : [fatwa.references];
  const published = fatwa.published_at
    ? new Intl.DateTimeFormat(locale === 'bn' ? 'bn-BD' : 'en-GB', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(fatwa.published_at))
    : null;
  const isBangla = locale === 'bn';

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main className="detail-page">
        <Link className="back-link" href={`/${locale}/fatwas`}>← {t.back}</Link>
        <article className="fatwa-detail">
          <div className="detail-meta"><span className="review-badge">✓ {t.published}</span><span>{fatwa.methodology || (isBangla ? 'সাধারণ পদ্ধতি' : 'General methodology')}</span></div>
          <h1>{fatwa.title}</h1>
          <div className="detail-byline"><div className="directory-avatar">{fatwa.scholar.name.slice(0, 1)}</div><div><span>{t.scholar}</span><strong>{fatwa.scholar.name}</strong></div>{published ? <div><span>{isBangla ? 'প্রকাশিত' : 'Published'}</span><time dateTime={fatwa.published_at || undefined}>{published}</time></div> : null}</div>
          <section className="question-block">
            <p className="section-kicker">{isBangla ? 'প্রশ্ন' : 'Question'}</p>
            <p>{fatwa.question}</p>
          </section>
          <section className="answer-block">
            <p className="section-kicker">{isBangla ? 'পর্যালোচিত উত্তর' : 'Reviewed answer'}</p>
            <div className="rich-copy">{fatwa.answer}</div>
          </section>
          {references.length && references[0] ? (
            <section className="references">
              <p className="section-kicker">{t.references}</p>
              <ul>{references.map((reference, index) => <li key={`${reference}-${index}`}>{reference}</li>)}</ul>
            </section>
          ) : null}
          <div className="detail-footer"><span>✓ {isBangla ? 'প্রকাশের আগে স্বতন্ত্রভাবে পর্যালোচিত' : 'Independently reviewed before publication'}</span><Link href={`/${locale}/methodology`}>{isBangla ? 'পদ্ধতি জানুন' : 'How review works'} →</Link></div>
          <FatwaActions publicationId={fatwa.id} locale={locale} />
        </article>
      </main>
      <Footer locale={locale} />
    </div>
  );
}
