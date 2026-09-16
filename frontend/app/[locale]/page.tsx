import Link from 'next/link';
import { notFound } from 'next/navigation';
import { CategoryList, FatwaCard, Footer, Header, text } from '../../components/site';
import { getCategories, getFatwas, isLocale, type Locale } from '../../lib/api';

export default async function LocaleHome({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const t = text(locale);
  const [fatwaData, categoryData] = await Promise.all([getFatwas(), getCategories()]);
  const fatwas = fatwaData?.results || [];
  const categories = categoryData?.results || [];

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">{t.eyebrow}</p>
            <h1>{t.title}</h1>
            <p className="hero-intro">{t.intro}</p>
            <div className="hero-actions">
              <Link className="button" href={`/${locale}/fatwas`}>{t.browse}</Link>
              <Link className="quiet-link" href={`/accounts/register/`}>{t.ask} ↗</Link>
            </div>
          </div>
          <div className="hero-note">
            <span className="seal">✦</span>
            <p>{t.reviewed}</p>
          </div>
        </section>

        <CategoryList categories={categories} locale={locale} />

        <section className="section-block">
          <div className="section-heading">
            <div>
              <p className="section-kicker">{t.library}</p>
              <h2>{t.recent}</h2>
            </div>
            <Link className="text-link" href={`/${locale}/fatwas`}>{t.library} →</Link>
          </div>
          {fatwas.length ? (
            <div className="fatwa-grid">{fatwas.map((fatwa) => <FatwaCard key={fatwa.id} fatwa={fatwa} locale={locale} />)}</div>
          ) : (
            <div className="empty-state">{t.empty}</div>
          )}
        </section>
      </main>
      <Footer locale={locale} />
    </div>
  );
}
