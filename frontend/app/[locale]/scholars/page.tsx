import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Footer, Header } from '../../../components/site';
import { getScholars, isLocale, type Locale } from '../../../lib/api';

function listValue(value: string[] | string) {
  return Array.isArray(value) ? value.join(' · ') : value;
}

export default async function ScholarsPage({ params }: { params: Promise<{ locale: string }> }) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const data = await getScholars();
  const scholars = data?.results || [];
  const isBangla = locale === 'bn';

  return <div className="site-shell" lang={locale}>
    <Header locale={locale} />
    <main className="directory-page">
      <div className="page-heading">
        <p className="section-kicker">{isBangla ? 'আলেমদের পরিচিতি' : 'Our scholars'}</p>
        <h1>{isBangla ? 'যাঁরা জ্ঞানের যত্ন নেন' : 'The people behind the answers'}</h1>
        <p>{isBangla ? 'অনুমোদিত আলেমদের অভিজ্ঞতা, বিষয় ও ভাষা সম্পর্কে জানুন।' : 'Meet the verified scholars who contribute careful, reviewed guidance.'}</p>
      </div>
      {scholars.length ? <div className="scholar-directory">{scholars.map((scholar) => <article className="directory-card" key={scholar.id}>
        <div className="directory-avatar">{scholar.name.slice(0, 1)}</div>
        <h2>{scholar.name}</h2>
        {scholar.institution ? <p className="directory-institution">{scholar.institution}</p> : null}
        {scholar.specialties ? <p><strong>{isBangla ? 'বিশেষত্ব' : 'Specialties'}:</strong> {listValue(scholar.specialties)}</p> : null}
        {scholar.languages ? <p><strong>{isBangla ? 'ভাষা' : 'Languages'}:</strong> {listValue(scholar.languages)}</p> : null}
        <Link className="text-link" href={`/${locale}/scholars/${scholar.id}`}>{isBangla ? 'প্রোফাইল দেখুন' : 'View profile'} →</Link>
      </article>)}</div> : <div className="empty-state">{isBangla ? 'এখনও কোনো স্কলার প্রোফাইল প্রকাশিত হয়নি।' : 'No scholar profiles are published yet.'}</div>}
    </main>
    <Footer locale={locale} />
  </div>;
}
