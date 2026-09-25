import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { CategoryList, FatwaCard, Footer, Header, text } from '../../components/site';
import { getCategories, getFatwas, isLocale, type Locale } from '../../lib/api';

type Props = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  const isBangla = locale === 'bn';
  return {
    title: isBangla ? 'পর্যালোচিত ইসলামি দিকনির্দেশনা' : 'Reviewed Islamic guidance',
    description: isBangla
      ? 'যোগ্য আলেমের উত্তর ও স্বতন্ত্র পর্যালোচনায় বিশ্বস্ত ইসলামি প্রশ্নোত্তর।'
      : 'Trusted Islamic questions and answers from qualified scholars, independently reviewed.',
    alternates: { canonical: `/${isBangla ? 'bn' : 'en'}`, languages: { bn: '/bn', en: '/en' } },
  };
}

const processCopy = {
  bn: [
    ['০১', 'আপনি প্রশ্ন করেন', 'প্রশ্ন ব্যক্তিগত থাকে, যদি না আপনি বেনামে প্রকাশের অনুমতি দেন।'],
    ['০২', 'আলেম উত্তর দেন', 'বিষয় ও ভাষার সঙ্গে মিলিয়ে একজন যাচাইকৃত আলেম দায়িত্ব নেন।'],
    ['০৩', 'স্বতন্ত্র পর্যালোচনা', 'ভিন্ন একজন জ্যেষ্ঠ আলেম উত্তরটি যাচাই করার পরই তা প্রকাশিত হয়।'],
  ],
  en: [
    ['01', 'You ask with context', 'Your question stays private unless you allow an anonymised version to be shared.'],
    ['02', 'A scholar responds', 'A verified scholar is matched by subject, language, and availability.'],
    ['03', 'Another scholar reviews', 'A separate senior scholar checks the answer before it is ever released.'],
  ],
} as const;

export default async function LocaleHome({ params }: Props) {
  const { locale: rawLocale } = await params;
  if (!isLocale(rawLocale)) notFound();
  const locale: Locale = rawLocale;
  const t = text(locale);
  const isBangla = locale === 'bn';
  const [fatwaData, categoryData] = await Promise.all([getFatwas(locale, '', '', '', '', 6), getCategories()]);
  const fatwas = fatwaData?.results || [];
  const categories = categoryData?.results || [];

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow"><span aria-hidden="true" />{t.eyebrow}</p>
            <h1>{t.title}</h1>
            <p className="hero-intro">{t.intro}</p>
            <form className="hero-search" action={`/${locale}/fatwas`}>
              <label htmlFor="home-search">{t.search}</label>
              <div>
                <input id="home-search" name="q" placeholder={isBangla ? 'যেমন: সফরে নামাজ' : 'e.g. prayer while travelling'} />
                <button type="submit" aria-label={t.searchButton}><span>{t.searchButton}</span><b aria-hidden="true">↗</b></button>
              </div>
            </form>
            <div className="hero-actions">
              <Link className="button" href={`/${locale}/ask`}>{t.ask} <span aria-hidden="true">→</span></Link>
              <Link className="quiet-link" href={`/${locale}/fatwas`}>{t.browse}</Link>
            </div>
          </div>
          <aside className="hero-trust" aria-label={isBangla ? 'পর্যালোচনা প্রক্রিয়া' : 'Review promise'}>
            <div className="trust-orbit" aria-hidden="true"><span>✦</span></div>
            <p className="hero-trust-number">02</p>
            <p>{isBangla ? 'একটি উত্তর' : 'One answer'}</p>
            <strong>{isBangla ? 'দুইজন আলেমের দায়িত্ব' : 'Two scholars accountable'}</strong>
            <div className="hero-trust-rule" />
            <small>{t.reviewed}</small>
          </aside>
        </section>

        <section className="trust-strip" aria-label={isBangla ? 'আমাদের অঙ্গীকার' : 'Our commitments'}>
          <p><span>✓</span>{isBangla ? 'যাচাইকৃত আলেম' : 'Verified scholars'}</p>
          <p><span>✓</span>{isBangla ? 'স্বতন্ত্র পর্যালোচনা' : 'Independent review'}</p>
          <p><span>✓</span>{isBangla ? 'গোপনীয়তা আগে' : 'Privacy by default'}</p>
          <p><span>✓</span>{isBangla ? 'বাংলা ও ইংরেজি' : 'Bangla & English'}</p>
        </section>

        <CategoryList categories={categories} locale={locale} />

        <section className="section-block recent-section">
          <div className="section-heading">
            <div>
              <p className="section-kicker">{t.library}</p>
              <h2>{isBangla ? 'সাম্প্রতিক পর্যালোচিত উত্তর' : 'Recently reviewed answers'}</h2>
            </div>
            <Link className="text-link" href={`/${locale}/fatwas`}>{isBangla ? 'সব ফতোয়া' : 'View the library'} <span aria-hidden="true">→</span></Link>
          </div>
          {fatwas.length ? (
            <div className="fatwa-grid">{fatwas.map((fatwa) => <FatwaCard key={fatwa.id} fatwa={fatwa} locale={locale} />)}</div>
          ) : (
            <div className="empty-state empty-state-rich">
              <span aria-hidden="true">✦</span>
              <h3>{t.empty}</h3>
              <p>{isBangla ? 'এর মধ্যে আপনার প্রশ্নটি নিরাপদে জমা দিতে পারেন।' : 'In the meantime, you can submit your own question securely.'}</p>
              <Link className="button button-ghost" href={`/${locale}/ask`}>{t.ask}</Link>
            </div>
          )}
        </section>

        <section className="process-section" aria-labelledby="process-title">
          <div className="process-heading">
            <p className="section-kicker">{isBangla ? 'কীভাবে কাজ করে' : 'How it works'}</p>
            <h2 id="process-title">{isBangla ? 'একটি উত্তর। তিনটি যত্নশীল ধাপ।' : 'One answer. Three careful steps.'}</h2>
            <p>{isBangla ? 'বিশ্বাস শুধু পরিচয় থেকে আসে না—একটি স্বচ্ছ প্রক্রিয়া থেকেও আসে।' : 'Trust comes not only from credentials, but from a process you can understand.'}</p>
            <Link className="text-link" href={`/${locale}/methodology`}>{isBangla ? 'সম্পূর্ণ পদ্ধতি দেখুন' : 'Read our full methodology'} <span aria-hidden="true">→</span></Link>
          </div>
          <ol className="process-list">
            {processCopy[locale].map(([number, title, body]) => (
              <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{body}</p></div></li>
            ))}
          </ol>
        </section>

        <section className="principles-section">
          <div className="principle-quote">
            <span aria-hidden="true">“</span>
            <blockquote>{isBangla ? 'জানা আর না-জানার মাঝখানে সবচেয়ে গুরুত্বপূর্ণ হলো—বিশ্বস্তভাবে জিজ্ঞাসা করার একটি জায়গা।' : 'Between uncertainty and understanding, people need a place where questions are handled with trust.'}</blockquote>
          </div>
          <div className="principle-copy">
            <p className="section-kicker">{isBangla ? 'আমাদের নীতি' : 'Our principle'}</p>
            <h2>{isBangla ? 'উত্তরের আগে আসে দায়িত্ব।' : 'Responsibility comes before answers.'}</h2>
            <p>{isBangla ? 'আমরা দ্রুততার চেয়ে যথার্থতা, পরিচয়ের চেয়ে গোপনীয়তা এবং একক মতের চেয়ে জবাবদিহিকে অগ্রাধিকার দিই।' : 'We prioritise care over speed, privacy over exposure, and accountability over any single voice.'}</p>
            <Link className="quiet-link" href={`/${locale}/about`}>{isBangla ? 'ইউনিভার্স অব ইলম সম্পর্কে' : 'About Universe of Ilm'} →</Link>
          </div>
        </section>

        <section className="home-cta">
          <div><p className="section-kicker">{isBangla ? 'আপনার প্রশ্ন গুরুত্বপূর্ণ' : 'Your question matters'}</p><h2>{isBangla ? 'নিশ্চিন্তে জিজ্ঞাসা করুন।' : 'Ask without hesitation.'}</h2></div>
          <div><p>{isBangla ? 'ব্যক্তিগতভাবে শুরু করুন। প্রকাশের সিদ্ধান্ত সবসময় আপনার।' : 'Start privately. The decision to share always stays with you.'}</p><Link className="button button-light" href={`/${locale}/ask`}>{t.ask} <span aria-hidden="true">→</span></Link></div>
        </section>
      </main>
      <Footer locale={locale} />
    </div>
  );
}
