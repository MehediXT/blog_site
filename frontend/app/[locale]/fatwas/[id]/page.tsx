import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Footer, Header, text } from '../../../../components/site';
import { getFatwa, isLocale, type Locale } from '../../../../lib/api';

export default async function FatwaDetail({ params }: { params: Promise<{ locale: string; id: string }> }) {
  const { locale: rawLocale, id } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const data = await getFatwa(id);
  if (!data?.fatwa) notFound();
  const fatwa = data.fatwa;
  const t = text(locale);
  const references = Array.isArray(fatwa.references) ? fatwa.references : [fatwa.references];

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main className="detail-page">
        <Link className="back-link" href={`/${locale}/fatwas`}>← {t.back}</Link>
        <article className="fatwa-detail">
          <div className="detail-meta"><span>{t.published}</span><span>{fatwa.scholar.name}</span></div>
          <h1>{fatwa.title}</h1>
          <section className="question-block">
            <p className="section-kicker">{locale === 'bn' ? 'প্রশ্ন' : 'Question'}</p>
            <p>{fatwa.question}</p>
          </section>
          <section className="answer-block">
            <p className="section-kicker">{locale === 'bn' ? 'উত্তর' : 'Answer'}</p>
            <div className="rich-copy">{fatwa.answer}</div>
          </section>
          {references.length && references[0] ? (
            <section className="references">
              <p className="section-kicker">{t.references}</p>
              <ul>{references.map((reference, index) => <li key={`${reference}-${index}`}>{reference}</li>)}</ul>
            </section>
          ) : null}
          <div className="detail-footer"><span>{t.scholar}: {fatwa.scholar.name}</span><span>{fatwa.methodology || ''}</span></div>
        </article>
      </main>
      <Footer locale={locale} />
    </div>
  );
}
