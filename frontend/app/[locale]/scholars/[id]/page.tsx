import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Footer, Header } from '../../../../components/site';
import { getJsonScholar, isLocale, type Locale } from '../../../../lib/api';

function listValue(value: string[] | string | undefined) {
  return Array.isArray(value) ? value.join(' · ') : value || '';
}

type Props = { params: Promise<{ locale: string; id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale: rawLocale, id } = await params;
  if (!isLocale(rawLocale)) return {};
  const data = await getJsonScholar(id);
  if (!data?.scholar) return {};
  const scholar = data.scholar;
  const description = scholar.biography?.replace(/\s+/g, ' ').slice(0, 160) || `${scholar.name} — verified scholar at Universe of Ilm.`;
  return {
    title: scholar.name,
    description,
    alternates: { canonical: `/${rawLocale}/scholars/${id}` },
    openGraph: { title: scholar.name, description, images: [] },
    twitter: { card: 'summary', title: scholar.name, description, images: [] },
  };
}

export default async function ScholarDetailPage({ params }: Props) {
  const { locale: rawLocale, id } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const data = await getJsonScholar(id);
  if (!data?.scholar) notFound();
  const scholar = data.scholar;
  const isBangla = locale === 'bn';

  return <div className="site-shell" lang={locale}>
    <Header locale={locale} />
    <main className="scholar-detail-page">
      <Link className="back-link" href={`/${locale}/scholars`}>← {isBangla ? 'সব স্কলার' : 'All scholars'}</Link>
      <div className="scholar-profile-card">
        <div className="directory-avatar large">{scholar.name.slice(0, 1)}</div>
        <p className="section-kicker">{isBangla ? 'অনুমোদিত স্কলার' : 'Verified scholar'}</p>
        <h1>{scholar.name}</h1>
        {scholar.institution ? <p className="directory-institution">{scholar.institution}</p> : null}
        {scholar.biography ? <p className="profile-biography">{scholar.biography}</p> : null}
        <div className="profile-facts">
          <div><span>{isBangla ? 'বিশেষত্ব' : 'Specialties'}</span><strong>{listValue(scholar.specialties)}</strong></div>
          <div><span>{isBangla ? 'ভাষা' : 'Languages'}</span><strong>{listValue(scholar.languages)}</strong></div>
          {scholar.qualifications ? <div><span>{isBangla ? 'যোগ্যতা' : 'Qualifications'}</span><strong>{listValue(scholar.qualifications)}</strong></div> : null}
        </div>
      </div>
    </main>
    <Footer locale={locale} />
  </div>;
}
