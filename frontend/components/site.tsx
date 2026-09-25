import Link from 'next/link';
import type { Category, Fatwa, Locale } from '../lib/api';
import { AuthNav } from './account';
import { LocaleSwitch } from './locale-switch';

const copy = {
  bn: {
    brand: 'ইউনিভার্স অব ইলম',
    library: 'ফতোয়া লাইব্রেরি',
    scholars: 'আলেমগণ',
    about: 'আমাদের সম্পর্কে',
    methodology: 'পর্যালোচনা পদ্ধতি',
    eyebrow: 'বিশ্বস্ত জ্ঞান · স্বতন্ত্র পর্যালোচনা',
    title: 'জিজ্ঞাসা থেকে নিশ্চয়তার পথে।',
    intro: 'যোগ্য আলেমের উত্তর, ভিন্ন একজন আলেমের পর্যালোচনা—যাতে ইসলামি দিকনির্দেশনা হয় যত্নশীল, স্বচ্ছ ও সহজবোধ্য।',
    browse: 'ফতোয়া পড়ুন',
    ask: 'প্রশ্ন করুন',
    search: 'কোন বিষয়ে জানতে চান?',
    searchButton: 'খুঁজুন',
    empty: 'এই মুহূর্তে কোনো প্রকাশিত ফতোয়া পাওয়া যায়নি।',
    categories: 'বিষয় ধরে খুঁজুন',
    reviewed: 'প্রতিটি উত্তর প্রকাশের আগে ভিন্ন একজন যোগ্য আলেম পর্যালোচনা করেন।',
    readMore: 'উত্তর পড়ুন',
    back: 'ফতোয়া লাইব্রেরিতে ফিরুন',
    published: 'পর্যালোচিত',
    scholar: 'উত্তরদাতা',
    references: 'তথ্যসূত্র',
    footerIntro: 'বাংলা ও ইংরেজিতে যত্নসহ পর্যালোচিত ইসলামি প্রশ্নোত্তরের একটি উন্মুক্ত পাঠাগার।',
    explore: 'অনুসন্ধান',
    trust: 'বিশ্বাস ও নীতি',
    privacy: 'গোপনীয়তা',
    terms: 'ব্যবহারের শর্ত',
    verification: 'আলেম যাচাই',
    contact: 'যোগাযোগ',
    menu: 'মেনু',
  },
  en: {
    brand: 'Universe of Ilm',
    library: 'Fatwa library',
    scholars: 'Scholars',
    about: 'About us',
    methodology: 'Review method',
    eyebrow: 'Trusted knowledge · Independent review',
    title: 'From questions to clarity.',
    intro: 'Answers from qualified scholars, reviewed by another scholar—so Islamic guidance is careful, transparent, and easier to understand.',
    browse: 'Browse fatwas',
    ask: 'Ask a question',
    search: 'What would you like to understand?',
    searchButton: 'Search',
    empty: 'There are no published fatwas to show right now.',
    categories: 'Explore by topic',
    reviewed: 'Every answer is checked by a different qualified scholar before it is released.',
    readMore: 'Read the answer',
    back: 'Back to the fatwa library',
    published: 'Reviewed',
    scholar: 'Answering scholar',
    references: 'References',
    footerIntro: 'An open library of carefully reviewed Islamic questions and answers in Bangla and English.',
    explore: 'Explore',
    trust: 'Trust & policy',
    privacy: 'Privacy',
    terms: 'Terms',
    verification: 'Scholar verification',
    contact: 'Contact',
    menu: 'Menu',
  },
} as const;

export function text(locale: Locale) {
  return copy[locale];
}

const mainLinks = (locale: Locale) => {
  const t = text(locale);
  return [
    { href: `/${locale}/fatwas`, label: t.library },
    { href: `/${locale}/scholars`, label: t.scholars },
    { href: `/${locale}/methodology`, label: t.methodology },
  ];
};

export function Header({ locale }: { locale: Locale }) {
  const t = text(locale);
  const links = mainLinks(locale);

  return (
    <header className="nav">
      <Link className="brand" href={`/${locale}`} aria-label={`${t.brand} — ${locale === 'bn' ? 'প্রচ্ছদ' : 'home'}`}>
        <span aria-hidden="true">✦</span>
        <span className="brand-copy"><strong>{t.brand}</strong><small>{locale === 'bn' ? 'পর্যালোচিত ইসলামি জ্ঞান' : 'Reviewed Islamic guidance'}</small></span>
      </Link>
      <nav className="nav-primary" aria-label={locale === 'bn' ? 'প্রধান নেভিগেশন' : 'Main navigation'}>
        {links.map((link) => <Link key={link.href} className="nav-link" href={link.href}>{link.label}</Link>)}
      </nav>
      <div className="nav-actions">
        <AuthNav locale={locale} />
        <LocaleSwitch locale={locale} />
        <details className="mobile-menu">
          <summary aria-label={t.menu}><span aria-hidden="true" /></summary>
          <nav aria-label={t.menu}>
            {links.map((link) => <Link key={link.href} href={link.href}>{link.label}</Link>)}
            <Link href={`/${locale}/about`}>{t.about}</Link>
            <Link href={`/${locale}/ask`}>{t.ask}</Link>
          </nav>
        </details>
      </div>
    </header>
  );
}

export function FatwaCard({ fatwa, locale }: { fatwa: Fatwa; locale: Locale }) {
  const t = text(locale);
  const published = fatwa.published_at
    ? new Intl.DateTimeFormat(locale === 'bn' ? 'bn-BD' : 'en-GB', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(fatwa.published_at))
    : t.published;

  return (
    <article className="fatwa-card">
      <div className="card-meta">
        <span>{fatwa.methodology || t.published}</span>
        <time dateTime={fatwa.published_at || undefined}>{published}</time>
      </div>
      <h3><Link href={`/${locale}/fatwas/${fatwa.id}`}>{fatwa.title}</Link></h3>
      <p className="question-preview">{fatwa.question}</p>
      <div className="card-footer">
        <span>{fatwa.scholar.name}</span>
        <Link className="text-link" href={`/${locale}/fatwas/${fatwa.id}`} aria-label={`${t.readMore}: ${fatwa.title}`}>{t.readMore} <span aria-hidden="true">↗</span></Link>
      </div>
    </article>
  );
}

export function Footer({ locale }: { locale: Locale }) {
  const t = text(locale);
  return (
    <footer className="footer">
      <div className="footer-main">
        <div className="footer-brand">
          <Link className="brand" href={`/${locale}`}><span aria-hidden="true">✦</span><span className="brand-copy"><strong>{t.brand}</strong></span></Link>
          <p>{t.footerIntro}</p>
        </div>
        <div className="footer-column">
          <strong>{t.explore}</strong>
          <Link href={`/${locale}/fatwas`}>{t.library}</Link>
          <Link href={`/${locale}/scholars`}>{t.scholars}</Link>
          <Link href={`/${locale}/ask`}>{t.ask}</Link>
        </div>
        <div className="footer-column">
          <strong>{t.trust}</strong>
          <Link href={`/${locale}/methodology`}>{t.methodology}</Link>
          <Link href={`/${locale}/verification`}>{t.verification}</Link>
          <Link href={`/${locale}/privacy`}>{t.privacy}</Link>
        </div>
        <div className="footer-column">
          <strong>{locale === 'bn' ? 'আরও' : 'More'}</strong>
          <Link href={`/${locale}/about`}>{t.about}</Link>
          <Link href={`/${locale}/contact`}>{t.contact}</Link>
          <Link href={`/${locale}/terms`}>{t.terms}</Link>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} Universe of Ilm</span>
        <span>{locale === 'bn' ? 'জ্ঞান · যত্ন · আমানতদারিতা' : 'Knowledge · Care · Trust'}</span>
      </div>
    </footer>
  );
}

export function CategoryList({ categories, locale }: { categories: Category[]; locale: Locale }) {
  const t = text(locale);
  if (!categories.length) return null;

  return (
    <section className="category-section" aria-labelledby="category-title">
      <div className="category-heading">
        <p className="section-kicker">{locale === 'bn' ? 'বিষয়সমূহ' : 'Topics'}</p>
        <h2 id="category-title">{t.categories}</h2>
      </div>
      <div className="category-list">
        {categories.map((category, index) => (
          <Link key={category.slug} href={`/${locale}/fatwas?category=${category.slug}`} className="category-pill">
            <span>{String(index + 1).padStart(2, '0')}</span>
            {locale === 'bn' ? category.name_bn : category.name_en}
            <b aria-hidden="true">↗</b>
          </Link>
        ))}
      </div>
    </section>
  );
}
