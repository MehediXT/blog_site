import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { FatwaCard, Footer, Header, text } from '../../../components/site';
import { getCategories, getFatwas, getMethodologies, getScholars, isLocale, type Locale } from '../../../lib/api';

type Query = { q?: string; category?: string; methodology?: string; scholar?: string; page?: string };
type Props = { params: Promise<{ locale: string }>; searchParams: Promise<Query> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const isBangla = locale === 'bn';
  return {
    title: isBangla ? 'ফতোয়া লাইব্রেরি' : 'Fatwa library',
    description: isBangla ? 'বিষয়, আলেম ও পদ্ধতি ধরে পর্যালোচিত ইসলামি উত্তর খুঁজুন।' : 'Search reviewed Islamic answers by topic, scholar, and methodology.',
    alternates: { canonical: `/${isBangla ? 'bn' : 'en'}/fatwas`, languages: { bn: '/bn/fatwas', en: '/en/fatwas' } },
  };
}

function buildQuery(query: Query, changes: Partial<Query>) {
  const next = new URLSearchParams();
  Object.entries({ ...query, ...changes }).forEach(([key, value]) => {
    if (value && !(key === 'page' && value === '1')) next.set(key, value);
  });
  const value = next.toString();
  return value ? `?${value}` : '';
}

export default async function FatwaLibrary({ params, searchParams }: Props) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const query = await searchParams;
  const q = query.q || '';
  const page = Math.max(1, Number.parseInt(query.page || '1', 10) || 1);
  const [fatwaData, categoryData, methodologyData, scholarData] = await Promise.all([
    getFatwas(locale, q, query.category || '', query.methodology || '', query.scholar || '', 12, page),
    getCategories(),
    getMethodologies(),
    getScholars(),
  ]);
  const t = text(locale);
  const selectedCategory = query.category || '';
  const selectedMethodology = query.methodology || '';
  const selectedScholar = query.scholar || '';
  const visibleFatwas = fatwaData?.results || [];
  const total = fatwaData?.count || 0;
  const totalPages = Math.max(1, Math.ceil(total / 12));
  const isBangla = locale === 'bn';

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main className="library-page">
        <div className="page-heading library-heading">
          <p className="section-kicker">{t.library}</p>
          <h1>{isBangla ? 'প্রশ্ন থেকে প্রজ্ঞা' : 'Questions into understanding'}</h1>
          <p>{isBangla ? 'যোগ্য আলেমের উত্তর, স্বতন্ত্র পর্যালোচনা এবং স্পষ্ট তথ্যসূত্র—এক জায়গায়।' : 'Qualified answers, independent review, and clear references—gathered in one place.'}</p>
        </div>

        <form className="search-panel" action={`/${locale}/fatwas`}>
          <label htmlFor="fatwa-search">{t.search}</label>
          <div className="search-row">
            <input id="fatwa-search" name="q" defaultValue={q} placeholder={isBangla ? 'শব্দ, প্রশ্ন বা বিষয় লিখুন' : 'Enter a word, question, or topic'} />
            <button className="button" type="submit">{t.searchButton} <span aria-hidden="true">↗</span></button>
          </div>
          <div className="filter-selects">
            <label><span>{isBangla ? 'পদ্ধতি' : 'Methodology'}</span><select name="methodology" defaultValue={selectedMethodology}><option value="">{isBangla ? 'সব পদ্ধতি' : 'All methodologies'}</option>{methodologyData.map((item) => <option key={item.slug} value={item.slug}>{isBangla ? item.name_bn : item.name_en}</option>)}</select></label>
            <label><span>{isBangla ? 'আলেম' : 'Scholar'}</span><select name="scholar" defaultValue={selectedScholar}><option value="">{isBangla ? 'সব আলেম' : 'All scholars'}</option>{scholarData?.results.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          </div>
        </form>

        {categoryData?.results.length ? (
          <div className="filter-row" aria-label={isBangla ? 'বিষয় বাছাই' : 'Filter by topic'}>
            <Link className={!selectedCategory ? 'filter active' : 'filter'} href={`/${locale}/fatwas${buildQuery(query, { category: '', page: '1' })}`}>{isBangla ? 'সব বিষয়' : 'All topics'}</Link>
            {categoryData.results.map((category) => (
              <Link key={category.slug} className={selectedCategory === category.slug ? 'filter active' : 'filter'} href={`/${locale}/fatwas${buildQuery(query, { category: category.slug, page: '1' })}`}>
                {isBangla ? category.name_bn : category.name_en}
              </Link>
            ))}
          </div>
        ) : null}

        <div className="results-bar">
          <p>{total ? (isBangla ? `${new Intl.NumberFormat('bn-BD').format(total)}টি পর্যালোচিত উত্তর` : `${total} reviewed ${total === 1 ? 'answer' : 'answers'}`) : (isBangla ? 'কোনো ফল পাওয়া যায়নি' : 'No results found')}</p>
          {(q || selectedCategory || selectedMethodology || selectedScholar) ? <Link href={`/${locale}/fatwas`}>{isBangla ? 'সব ফিল্টার মুছুন' : 'Clear all filters'}</Link> : null}
        </div>

        {visibleFatwas.length ? (
          <div className="fatwa-grid">{visibleFatwas.map((fatwa) => <FatwaCard key={fatwa.id} fatwa={fatwa} locale={locale} />)}</div>
        ) : (
          <div className="empty-state empty-state-rich"><span aria-hidden="true">⌕</span><h3>{t.empty}</h3><p>{isBangla ? 'অন্য শব্দ বা বিষয় দিয়ে আবার চেষ্টা করুন।' : 'Try another word or remove one of the filters.'}</p><Link className="button button-ghost" href={`/${locale}/fatwas`}>{isBangla ? 'সব উত্তর দেখুন' : 'View all answers'}</Link></div>
        )}

        {totalPages > 1 ? (
          <nav className="pagination" aria-label={isBangla ? 'ফলাফলের পাতা' : 'Results pages'}>
            {page > 1 ? <Link href={`/${locale}/fatwas${buildQuery(query, { page: String(page - 1) })}`}>← {isBangla ? 'আগের পাতা' : 'Previous'}</Link> : <span />}
            <span>{isBangla ? `পৃষ্ঠা ${new Intl.NumberFormat('bn-BD').format(page)} / ${new Intl.NumberFormat('bn-BD').format(totalPages)}` : `Page ${page} of ${totalPages}`}</span>
            {page < totalPages ? <Link href={`/${locale}/fatwas${buildQuery(query, { page: String(page + 1) })}`}>{isBangla ? 'পরের পাতা' : 'Next'} →</Link> : <span />}
          </nav>
        ) : null}
      </main>
      <Footer locale={locale} />
    </div>
  );
}
