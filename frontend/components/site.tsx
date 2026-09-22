import Link from 'next/link';
import type { Category, Fatwa, Locale } from '../lib/api';
import { AuthNav } from './account';

const copy = {
  bn: {
    brand: 'ইউনিভার্স অব ইলম',
    library: 'ফতোয়া লাইব্রেরি',
    eyebrow: 'বিশ্বস্ত জ্ঞান, পর্যালোচিত উত্তর',
    title: 'ইসলামি প্রশ্নের শান্ত, নির্ভরযোগ্য উত্তর।',
    intro: 'যোগ্য আলেমদের উত্তর এবং স্বতন্ত্র পর্যালোচনার মাধ্যমে জ্ঞানকে সবার কাছে সহজ করে তুলি।',
    browse: 'ফতোয়া পড়ুন',
    process: 'আমাদের পর্যালোচনা প্রক্রিয়া',
    recent: 'সাম্প্রতিক ফতোয়া',
    search: 'আপনার প্রশ্ন বা বিষয় খুঁজুন',
    searchButton: 'খুঁজুন',
    empty: 'এখনও কোনো প্রকাশিত ফতোয়া পাওয়া যায়নি।',
    categories: 'বিষয়ভিত্তিক অনুসন্ধান',
    reviewed: 'প্রতিটি উত্তর প্রকাশের আগে পর্যালোচিত হয়',
    readMore: 'সম্পূর্ণ উত্তর পড়ুন',
    back: 'ফতোয়া লাইব্রেরিতে ফিরুন',
    published: 'প্রকাশিত',
    scholar: 'উত্তরদাতা',
    references: 'তথ্যসূত্র',
  },
  en: {
    brand: 'Universe of Ilm',
    library: 'Fatwa library',
    eyebrow: 'Trusted knowledge, carefully reviewed',
    title: 'Calm, reliable answers to Islamic questions.',
    intro: 'We make guidance easier to access through qualified scholars and independent review.',
    browse: 'Browse fatwas',
    process: 'How our review works',
    recent: 'Recent fatwas',
    search: 'Search a question or topic',
    searchButton: 'Search',
    empty: 'No published fatwas are available yet.',
    categories: 'Explore by topic',
    reviewed: 'Every answer is reviewed before publication',
    readMore: 'Read the full answer',
    back: 'Back to the fatwa library',
    published: 'Published',
    scholar: 'Scholar',
    references: 'References',
  },
} as const;

export function text(locale: Locale) {
  return copy[locale];
}

export function Header({ locale }: { locale: Locale }) {
  const t = text(locale);
  const otherLocale = locale === 'bn' ? 'en' : 'bn';

  return (
    <header className="nav">
      <Link className="brand" href={`/${locale}`}>
        <span>◈</span> {t.brand}
      </Link>
      <nav className="nav-actions" aria-label="Main navigation">
        <Link className="nav-link" href={`/${locale}/fatwas`}>{t.library}</Link>
        <Link className="nav-link nav-scholars" href={`/${locale}/scholars`}>{locale === 'bn' ? 'আলেমগণ' : 'Scholars'}</Link>
        <AuthNav locale={locale} />
        <Link className="locale-switch" href={`/${otherLocale}`} aria-label={otherLocale === 'bn' ? 'বাংলা' : 'English'}>
          {otherLocale.toUpperCase()}
        </Link>
      </nav>
    </header>
  );
}

export function FatwaCard({ fatwa, locale }: { fatwa: Fatwa; locale: Locale }) {
  const t = text(locale);
  return (
    <article className="fatwa-card">
      <div className="card-meta">
        <span>{fatwa.methodology || t.published}</span>
        <span>{fatwa.scholar.name}</span>
      </div>
      <h3><Link href={`/${locale}/fatwas/${fatwa.id}`}>{fatwa.title}</Link></h3>
      <p className="question-preview">{fatwa.question}</p>
      <Link className="text-link" href={`/${locale}/fatwas/${fatwa.id}`}>{t.readMore} →</Link>
    </article>
  );
}

export function Footer({ locale }: { locale: Locale }) {
  return (
    <footer className="footer">
      <span>© {new Date().getFullYear()} Universe of Ilm</span>
      <span>{locale === 'bn' ? 'জ্ঞান, যত্ন এবং আমানতদারিতা' : 'Knowledge, care, and trust'}</span>
    </footer>
  );
}

export function CategoryList({ categories, locale }: { categories: Category[]; locale: Locale }) {
  const t = text(locale);
  if (!categories.length) return null;

  return (
    <section className="category-section">
      <p className="section-kicker">{t.categories}</p>
      <div className="category-list">
        {categories.map((category) => (
          <Link key={category.slug} href={`/${locale}/fatwas?category=${category.slug}`} className="category-pill">
            {locale === 'bn' ? category.name_bn : category.name_en}
          </Link>
        ))}
      </div>
    </section>
  );
}
