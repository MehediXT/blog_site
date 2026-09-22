import Link from 'next/link';
import { notFound } from 'next/navigation';
import { FatwaCard, Footer, Header, text } from '../../../components/site';
import { getCategories, getFatwas, getMethodologies, getScholars, isLocale, type Locale } from '../../../lib/api';

export default async function FatwaLibrary({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string; category?: string; methodology?: string; scholar?: string }>;
}) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const query = await searchParams;
  const q = query.q || '';
  const [fatwaData, categoryData, methodologyData, scholarData] = await Promise.all([
    getFatwas(locale, q, query.category || '', query.methodology || '', query.scholar || ''),
    getCategories(),
    getMethodologies(),
    getScholars(),
  ]);
  const t = text(locale);
  const selectedCategory = query.category || '';
  const selectedMethodology = query.methodology || '';
  const selectedScholar = query.scholar || '';
  const visibleFatwas = fatwaData?.results || [];

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main className="library-page">
        <div className="page-heading">
          <p className="section-kicker">{t.library}</p>
          <h1>{locale === 'bn' ? 'প্রশ্ন থেকে প্রজ্ঞা' : 'Questions into understanding'}</h1>
          <p>{locale === 'bn' ? 'পর্যালোচিত উত্তর, এক জায়গায়।' : 'Reviewed answers, gathered in one place.'}</p>
        </div>

        <form className="search-panel" action={`/${locale}/fatwas`}>
          <label htmlFor="fatwa-search">{t.search}</label>
          <div className="search-row">
            <input id="fatwa-search" name="q" defaultValue={q} placeholder={t.search} />
            <button className="button" type="submit">{t.searchButton}</button>
          </div>
          <div className="filter-selects">
            <label><span>{locale === 'bn' ? 'পদ্ধতি' : 'Methodology'}</span><select name="methodology" defaultValue={selectedMethodology}><option value="">{locale === 'bn' ? 'সব পদ্ধতি' : 'All methodologies'}</option>{(methodologyData || []).map((item) => <option key={item.slug} value={item.slug}>{locale === 'bn' ? item.name_bn : item.name_en}</option>)}</select></label>
            <label><span>{locale === 'bn' ? 'আলেম' : 'Scholar'}</span><select name="scholar" defaultValue={selectedScholar}><option value="">{locale === 'bn' ? 'সব আলেম' : 'All scholars'}</option>{scholarData?.results.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          </div>
        </form>

        {categoryData?.results.length ? (
          <div className="filter-row">
            <Link className={!selectedCategory ? 'filter active' : 'filter'} href={`/${locale}/fatwas${q ? `?q=${encodeURIComponent(q)}` : ''}`}>{locale === 'bn' ? 'সব' : 'All'}</Link>
            {categoryData.results.map((category) => (
              <Link key={category.slug} className={selectedCategory === category.slug ? 'filter active' : 'filter'} href={`/${locale}/fatwas?category=${category.slug}${q ? `&q=${encodeURIComponent(q)}` : ''}`}>
                {locale === 'bn' ? category.name_bn : category.name_en}
              </Link>
            ))}
          </div>
        ) : null}

        {visibleFatwas.length ? (
          <div className="fatwa-grid">{visibleFatwas.map((fatwa) => <FatwaCard key={fatwa.id} fatwa={fatwa} locale={locale} />)}</div>
        ) : (
          <div className="empty-state">{t.empty}</div>
        )}
      </main>
      <Footer locale={locale} />
    </div>
  );
}
