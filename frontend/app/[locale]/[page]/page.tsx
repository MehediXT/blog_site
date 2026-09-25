import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Footer, Header } from '../../../components/site';
import { isLocale, type Locale } from '../../../lib/api';

type Section = { title: string; body: string; points?: string[] };
type PageContent = { kicker: string; title: string; intro: string; sections: Section[] };

const content: Record<string, Record<Locale, PageContent>> = {
  about: {
    bn: {
      kicker: 'আমাদের পরিচয়', title: 'জ্ঞানের সঙ্গে যত্নও জরুরি।',
      intro: 'ইউনিভার্স অব ইলম বাংলা ও ইংরেজিতে ইসলামি প্রশ্নোত্তরের একটি বিশ্বস্ত, পাঠবান্ধব ও জবাবদিহিমূলক জায়গা।',
      sections: [
        { title: 'কেন এই উদ্যোগ', body: 'অনলাইনে উত্তর পাওয়া সহজ, কিন্তু উত্তরের উৎস, পর্যালোচনা ও প্রেক্ষাপট বোঝা সবসময় সহজ নয়। আমরা এই ব্যবধানটি কমাতে চাই—যোগ্য আলেম, স্বচ্ছ পদ্ধতি এবং মনোযোগী উপস্থাপনার মাধ্যমে।' },
        { title: 'আমাদের অঙ্গীকার', body: 'প্রতিটি প্রকাশ্য উত্তর একজন যাচাইকৃত আলেম লেখেন এবং ভিন্ন একজন যোগ্য আলেম সেটি পর্যালোচনা করেন। প্রশ্নকারীর পরিচয় কখনও প্রকাশ করা হয় না।', points: ['প্রকাশের আগে স্বতন্ত্র পর্যালোচনা', 'ব্যক্তিগত প্রশ্নের কঠোর গোপনীয়তা', 'তথ্যসূত্র ও পদ্ধতির স্বচ্ছ উল্লেখ'] },
        { title: 'এটি কী নয়', body: 'এই পাঠাগার জরুরি চিকিৎসা, আইনি পরামর্শ বা ব্যক্তিগত কাউন্সেলিংয়ের বিকল্প নয়। জটিল বা স্থানীয় বিষয়ে নিকটস্থ বিশ্বস্ত আলেম ও প্রাসঙ্গিক পেশাজীবীর সঙ্গে সরাসরি কথা বলুন।' },
      ],
    },
    en: {
      kicker: 'Who we are', title: 'Knowledge needs care, too.',
      intro: 'Universe of Ilm is a calm, accountable place for Islamic questions and answers in Bangla and English.',
      sections: [
        { title: 'Why we exist', body: 'Answers are easy to find online. Understanding their source, context, and level of review is much harder. We are narrowing that gap through qualified scholarship, a transparent process, and considered presentation.' },
        { title: 'Our commitment', body: 'Every public answer is written by a verified scholar and reviewed by another qualified scholar. The person asking is never identified publicly.', points: ['Independent review before release', 'Strict privacy for personal questions', 'Clear references and methodology labels'] },
        { title: 'What this is not', body: 'This library is not a substitute for emergency, medical, legal, or personal counselling. For complex or local circumstances, speak directly with a trusted local scholar and the relevant professional.' },
      ],
    },
  },
  methodology: {
    bn: {
      kicker: 'পর্যালোচনা পদ্ধতি', title: 'একটি উত্তর কীভাবে বিশ্বাসযোগ্য হয়।',
      intro: 'আমাদের প্রকাশনা প্রক্রিয়া এমনভাবে তৈরি, যাতে প্রতিটি উত্তরের উৎস, দায়িত্ব এবং পর্যালোচনার ধাপ স্পষ্ট থাকে।',
      sections: [
        { title: '১. প্রশ্ন গ্রহণ ও গোপনীয়তা', body: 'প্রশ্ন ডিফল্টভাবে ব্যক্তিগত থাকে। প্রশ্নকারী অনুমতি দিলে একজন মডারেটর পরিচয়বাহী তথ্য সরিয়ে প্রকাশযোগ্য ভাষা প্রস্তুত করেন। মূল প্রশ্ন কখনও সরাসরি প্রকাশিত হয় না।' },
        { title: '২. যোগ্যতার সঙ্গে মিল', body: 'বিষয়, ভাষা, প্রাসঙ্গিক মাজহাব ও আলেমের কাজের চাপ বিবেচনা করে একজন উত্তরদাতা এবং ভিন্ন একজন পর্যালোচক নির্বাচন করা হয়।' },
        { title: '৩. দলিলসহ উত্তর', body: 'উত্তরদাতা আলেম প্রাসঙ্গিক দলিল, ব্যাখ্যা এবং ব্যবহৃত পদ্ধতি উল্লেখ করে একটি খসড়া প্রস্তুত করেন। জমা দেওয়া প্রতিটি সংস্করণ সংরক্ষিত থাকে।' },
        { title: '৪. স্বতন্ত্র পর্যালোচনা', body: 'পর্যালোচক একই ব্যক্তি হতে পারেন না। তিনি উত্তর অনুমোদন করতে, পরিবর্তন চাইতে বা কারণসহ প্রত্যাখ্যান করতে পারেন। শুধু অনুমোদিত সংস্করণই প্রকাশিত হয়।' },
        { title: '৫. সংশোধন ও জবাবদিহি', body: 'প্রকাশের পর সংশোধন প্রয়োজন হলে নতুন সংস্করণ আবার পর্যালোচনার মধ্য দিয়ে যায়। আগের সিদ্ধান্ত ও সংশোধনের ইতিহাস সংরক্ষিত থাকে।' },
      ],
    },
    en: {
      kicker: 'Review methodology', title: 'How an answer earns trust.',
      intro: 'Our publishing process makes the source, responsibility, and review history behind each answer clear.',
      sections: [
        { title: '1. Intake and privacy', body: 'Questions are private by default. If the asker gives permission, a moderator removes identifying details and prepares public wording. The original submission is never published directly.' },
        { title: '2. Qualified matching', body: 'We assign an answering scholar and a different reviewer based on topic, language, relevant school of thought, and availability.' },
        { title: '3. Evidence-led drafting', body: 'The answering scholar prepares a draft with relevant evidence, explanation, references, and a methodology label. Every submitted revision is preserved.' },
        { title: '4. Independent review', body: 'The reviewer cannot be the author. They may approve the answer, request changes, or reject it with a reason. Only an approved revision can be released.' },
        { title: '5. Corrections and accountability', body: 'If an answer needs correction after publication, the new revision goes through review again. Earlier decisions and the correction history remain recorded.' },
      ],
    },
  },
  verification: {
    bn: {
      kicker: 'আলেম যাচাই', title: 'পরিচয়ের চেয়ে যোগ্যতা বড়।',
      intro: 'কেউ নিজে থেকে এই প্ল্যাটফর্মে আলেম হিসেবে কাজ শুরু করতে পারেন না। প্রতিটি প্রোফাইল প্রশাসনিক যাচাইয়ের মধ্য দিয়ে যায়।',
      sections: [
        { title: 'আমরা যা যাচাই করি', body: 'প্রাতিষ্ঠানিক শিক্ষা, স্বীকৃত শিক্ষকের অধীনে অধ্যয়ন, সংশ্লিষ্ট বিষয়ে অভিজ্ঞতা, ভাষাগত সক্ষমতা এবং প্রকাশ্য পরিচয়ের সামঞ্জস্য দেখা হয়।', points: ['যোগ্যতা ও শিক্ষাপ্রতিষ্ঠান', 'বিষয়ভিত্তিক বিশেষত্ব', 'বাংলা বা ইংরেজিতে উত্তর দেওয়ার সক্ষমতা', 'শিক্ষক ও প্রতিষ্ঠানের রেফারেন্স'] },
        { title: 'অনুমোদন স্থায়ী নয়', body: 'অভিযোগ, গুরুতর ভুল বা আচরণবিধি ভঙ্গের ক্ষেত্রে আলেমের কাজ স্থগিত করা যায়। স্থগিত অবস্থায় তিনি নতুন উত্তর বা পর্যালোচনা করতে পারেন না।' },
        { title: 'স্বচ্ছ প্রোফাইল', body: 'প্রকাশ্য প্রোফাইলে শুধু অনুমোদিত জীবনী, যোগ্যতা, প্রতিষ্ঠান, বিশেষত্ব ও ভাষা দেখানো হয়। ব্যক্তিগত যাচাই নোট কখনও প্রকাশ করা হয় না।' },
      ],
    },
    en: {
      kicker: 'Scholar verification', title: 'Credentials before visibility.',
      intro: 'No one can appoint themselves as a scholar on this platform. Every profile goes through an administrator-led verification process.',
      sections: [
        { title: 'What we examine', body: 'We consider formal study, learning under recognised teachers, relevant subject experience, language ability, and consistency of public identity.', points: ['Qualifications and institutions', 'Subject specialisms', 'Ability to answer in Bangla or English', 'Teacher and institutional references'] },
        { title: 'Approval is not permanent', body: 'Scholar activity may be suspended following a credible report, serious error, or breach of conduct. A suspended scholar cannot author or review new answers.' },
        { title: 'A transparent profile', body: 'Public profiles show only approved biographies, qualifications, institutions, specialisms, and languages. Private verification notes are never published.' },
      ],
    },
  },
  privacy: {
    bn: {
      kicker: 'গোপনীয়তা', title: 'আপনার গল্প আপনার নিয়ন্ত্রণে।',
      intro: 'প্রশ্ন করার জন্য যে আস্থা প্রয়োজন, আমরা সেটিকে একটি মৌলিক দায়িত্ব হিসেবে দেখি।',
      sections: [
        { title: 'ব্যক্তিগতই ডিফল্ট', body: 'নতুন প্রশ্ন ব্যক্তিগত হিসেবে শুরু হয়। শুধু আপনি স্পষ্ট অনুমতি দিলে বেনামি ও সম্পাদিত সংস্করণ প্রকাশের জন্য বিবেচিত হতে পারে।' },
        { title: 'কারা দেখতে পারেন', body: 'মূল প্রশ্ন শুধু আপনি, দায়িত্বপ্রাপ্ত আলেম ও পর্যালোচক এবং অনুমোদিত মডারেশন কর্মীরা দেখতে পারেন। অননুমোদিত অনুরোধে ব্যক্তিগত প্রশ্ন পাওয়া যায় না।' },
        { title: 'আপনার পছন্দ', body: 'প্রকাশের আগে আপনি সম্মতি ফিরিয়ে নিতে পারেন। প্রকাশের পরে প্রত্যাহারের অনুরোধ করলে পর্যালোচনা চলাকালীন প্রকাশনাটি লুকিয়ে রাখা হয়।' },
        { title: 'সঞ্চিত তথ্য', body: 'অ্যাকাউন্ট, প্রশ্ন, প্রয়োজনীয় যোগাযোগ, পর্যালোচনা সিদ্ধান্ত ও নিরাপত্তা অডিট সংরক্ষণ করা হয়। পরিচয়বাহী তথ্য জনসমক্ষে প্রকাশ করা হয় না।' },
      ],
    },
    en: {
      kicker: 'Privacy', title: 'Your story stays in your control.',
      intro: 'The trust required to ask a personal question is a responsibility we treat as foundational.',
      sections: [
        { title: 'Private by default', body: 'Every new question begins as private. Only your explicit permission allows an anonymised, edited version to be considered for publication.' },
        { title: 'Who can see it', body: 'The original question is visible only to you, the assigned scholar and reviewer, and authorised moderation staff. Inaccessible private records are not exposed.' },
        { title: 'Your choices', body: 'You can withdraw publication consent before release. If you request withdrawal after publication, the public answer is hidden while moderators review the request.' },
        { title: 'What we retain', body: 'We retain account details, questions, necessary correspondence, review decisions, and security audit records. Identifying information is never published with a fatwa.' },
      ],
    },
  },
  terms: {
    bn: {
      kicker: 'ব্যবহারের শর্ত', title: 'সম্মান, নিরাপত্তা ও সৎ ব্যবহার।',
      intro: 'এই সেবা ব্যবহার করে আপনি প্রশ্নোত্তর, গোপনীয়তা এবং কমিউনিটির নিরাপত্তা রক্ষায় কিছু মৌলিক নীতিতে সম্মত হন।',
      sections: [
        { title: 'সৎ ও নিরাপদ ব্যবহার', body: 'ভুল পরিচয়, হয়রানি, ঘৃণামূলক বক্তব্য, বেআইনি কনটেন্ট বা অন্যের ব্যক্তিগত তথ্য জমা দেওয়া যাবে না। প্রয়োজন হলে কনটেন্ট সরানো বা অ্যাকাউন্ট সীমিত করা হতে পারে।' },
        { title: 'দিকনির্দেশনার সীমা', body: 'প্রকাশিত উত্তর শিক্ষামূলক ধর্মীয় দিকনির্দেশনা। এটি জরুরি, চিকিৎসা, আইনি বা আর্থিক পেশাগত পরামর্শ নয়। ব্যক্তিগত সিদ্ধান্তে প্রাসঙ্গিক বিশেষজ্ঞের সাহায্য নিন।' },
        { title: 'কনটেন্ট ও সংশোধন', body: 'উত্তর উদ্ধৃত করলে প্রেক্ষাপট, উৎস ও অর্থ অক্ষুণ্ণ রাখুন। আমরা ভুল সংশোধন, কনটেন্ট প্রত্যাহার বা সেবার নীতি হালনাগাদ করতে পারি।' },
      ],
    },
    en: {
      kicker: 'Terms of use', title: 'Respectful, safe, honest use.',
      intro: 'By using this service, you agree to a few foundational rules that protect questions, privacy, and the safety of the community.',
      sections: [
        { title: 'Honest and safe use', body: 'Do not submit false identities, harassment, hateful or unlawful content, or another person’s private information. We may remove content or restrict accounts when necessary.' },
        { title: 'Limits of guidance', body: 'Published answers are educational religious guidance. They are not emergency, medical, legal, or regulated financial advice. Seek the relevant professional for personal decisions.' },
        { title: 'Content and corrections', body: 'If you quote an answer, preserve its context, source, and meaning. We may correct errors, withdraw material, or update service policies when necessary.' },
      ],
    },
  },
  contact: {
    bn: {
      kicker: 'যোগাযোগ', title: 'আপনার কথা আমরা শুনতে চাই।',
      intro: 'কনটেন্ট, গোপনীয়তা, প্রযুক্তিগত সমস্যা বা আলেম যাচাই—সঠিক পথে আপনার বার্তা পৌঁছাতে নিচের নির্দেশনা ব্যবহার করুন।',
      sections: [
        { title: 'প্রকাশিত উত্তর নিয়ে উদ্বেগ', body: 'সংশ্লিষ্ট ফতোয়া খুলে “রিপোর্ট” ব্যবহার করুন। এতে প্রকাশনার পরিচয় স্বয়ংক্রিয়ভাবে যুক্ত হয় এবং মডারেটর দ্রুত বিষয়টি খুঁজে পান।' },
        { title: 'অ্যাকাউন্ট বা গোপনীয়তা', body: 'আপনার অ্যাকাউন্টে ব্যবহৃত ইমেইল থেকে privacy@universeofilm.org ঠিকানায় লিখুন। প্রশ্নের সংবেদনশীল বিবরণ ইমেইলে পুনরায় পাঠাবেন না।' },
        { title: 'সাধারণ যোগাযোগ', body: 'সহযোগিতা, আলেম যাচাই বা সাধারণ মতামতের জন্য hello@universeofilm.org ঠিকানায় লিখুন। আমরা সাধারণত কয়েক কার্যদিবসের মধ্যে উত্তর দেওয়ার চেষ্টা করি।' },
      ],
    },
    en: {
      kicker: 'Contact', title: 'We would like to hear from you.',
      intro: 'For content, privacy, technical issues, or scholar verification, use the guidance below so your message reaches the right place.',
      sections: [
        { title: 'A concern about a published answer', body: 'Open the relevant fatwa and use “Report an issue”. This attaches the publication reference automatically and helps moderators find it quickly.' },
        { title: 'Account or privacy', body: 'Write from your account email to privacy@universeofilm.org. Please do not repeat sensitive details from your question in the email.' },
        { title: 'General enquiries', body: 'For partnerships, scholar verification, or general feedback, write to hello@universeofilm.org. We aim to reply within a few working days.' },
      ],
    },
  },
};

type Props = { params: Promise<{ locale: string; page: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale: rawLocale, page } = await params;
  if (!isLocale(rawLocale) || !content[page]) return {};
  const pageContent = content[page][rawLocale];
  return {
    title: pageContent.title,
    description: pageContent.intro,
    alternates: { canonical: `/${rawLocale}/${page}`, languages: { bn: `/bn/${page}`, en: `/en/${page}` } },
  };
}

export default async function InformationPage({ params }: Props) {
  const { locale: rawLocale, page } = await params;
  if (!isLocale(rawLocale) || !content[page]) notFound();
  const locale: Locale = rawLocale;
  const pageContent = content[page][locale];
  const isContact = page === 'contact';

  return (
    <div className="site-shell" lang={locale}>
      <Header locale={locale} />
      <main className="information-page">
        <header className="information-hero">
          <p className="section-kicker">{pageContent.kicker}</p>
          <h1>{pageContent.title}</h1>
          <p>{pageContent.intro}</p>
        </header>
        <div className="information-layout">
          <aside>
            <p>{locale === 'bn' ? 'এই পাতায়' : 'On this page'}</p>
            <ol>{pageContent.sections.map((section, index) => <li key={section.title}><a href={`#section-${index + 1}`}>{section.title}</a></li>)}</ol>
          </aside>
          <div className="information-sections">
            {pageContent.sections.map((section, index) => (
              <section id={`section-${index + 1}`} key={section.title}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <h2>{section.title}</h2>
                <p>{section.body}</p>
                {section.points ? <ul>{section.points.map((point) => <li key={point}>{point}</li>)}</ul> : null}
              </section>
            ))}
          </div>
        </div>
        <section className="information-cta">
          <div><p className="section-kicker">{isContact ? (locale === 'bn' ? 'প্রশ্ন আছে?' : 'Need help?') : (locale === 'bn' ? 'আরও জানুন' : 'Continue exploring')}</p><h2>{isContact ? (locale === 'bn' ? 'প্রকাশিত উত্তর নিয়ে উদ্বিগ্ন?' : 'Concerned about an answer?') : (locale === 'bn' ? 'পর্যালোচিত উত্তর পড়ুন।' : 'Read reviewed answers.')}</h2></div>
          <Link className="button" href={`/${locale}/fatwas`}>{locale === 'bn' ? 'ফতোয়া লাইব্রেরি' : 'Fatwa library'} →</Link>
        </section>
      </main>
      <Footer locale={locale} />
    </div>
  );
}
