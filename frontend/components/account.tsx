'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useEffect, useState } from 'react';
import {
  ApiFailure,
  Category,
  Fatwa,
  Notification,
  Question,
  User,
  clearAuth,
  createQuestion,
  getBookmarks,
  getCurrentUser,
  getMyQuestions,
  getNotifications,
  login,
  logout,
  register,
  savedUser,
  submitQuestion,
} from '../lib/api';

type Locale = 'bn' | 'en';

function errorMessage(error: unknown) {
  const failure = error as ApiFailure;
  if (failure.fields) {
    const firstField = Object.values(failure.fields).find((value) => Array.isArray(value) && value.length);
    if (Array.isArray(firstField) && typeof firstField[0] === 'string') return firstField[0];
  }
  return failure.message || 'Something went wrong. Please try again.';
}

export function AuthNav({ locale }: { locale: Locale }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(savedUser());
  }, []);

  return user ? (
    <>
      <Link className="nav-link nav-ask" href={`/${locale}/ask`}>{locale === 'bn' ? 'প্রশ্ন করুন' : 'Ask a question'}</Link>
      {user.scholar ? <Link className="nav-link nav-scholar" href={`/${locale}/scholar`}>{locale === 'bn' ? 'স্কলার প্যানেল' : 'Scholar panel'}</Link> : null}
      <Link className="account-chip" href={`/${locale}/account`} aria-label="Open your account">
        <span className="avatar">{(user.display_name || user.username).slice(0, 1).toUpperCase()}</span>
        <span>{user.display_name || user.username}</span>
      </Link>
    </>
  ) : (
    <Link className="button button-small nav-auth" href={`/${locale}/auth`}>
      {locale === 'bn' ? 'শুরু করুন' : 'Get started'}
    </Link>
  );
}

export function AuthPanel({ locale }: { locale: Locale }) {
  const router = useRouter();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const isBangla = locale === 'bn';

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (mode === 'login') await login(username, password);
      else await register(username, email, password);
      router.push(`/${locale}/account`);
      router.refresh();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-layout">
      <section className="auth-intro">
        <span className="eyebrow">{isBangla ? 'আপনার জ্ঞানের যাত্রা' : 'Your space for reflection'}</span>
        <h1>{isBangla ? 'প্রশ্ন করুন। বুঝুন। এগিয়ে চলুন।' : 'Ask with confidence. Learn with care.'}</h1>
        <p>{isBangla ? 'আপনার প্রশ্ন নিরাপদে সংরক্ষণ করুন এবং যোগ্য আলেমদের পর্যালোচিত উত্তরের পথে এগিয়ে যান।' : 'Keep your questions safe, follow their progress, and receive thoughtful guidance from qualified scholars.'}</p>
        <div className="trust-list">
          <div><span className="trust-icon">✦</span><span>{isBangla ? 'গোপনীয়তা আপনার নিয়ন্ত্রণে' : 'Privacy stays in your hands'}</span></div>
          <div><span className="trust-icon">✓</span><span>{isBangla ? 'পর্যালোচিত ও দায়িত্বশীল উত্তর' : 'Reviewed, responsible answers'}</span></div>
          <div><span className="trust-icon">◌</span><span>{isBangla ? 'আপনার প্রশ্নের অগ্রগতি দেখুন' : 'Track every question you ask'}</span></div>
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs" role="tablist">
          <button className={mode === 'login' ? 'auth-tab active' : 'auth-tab'} type="button" onClick={() => { setMode('login'); setError(''); }}>
            {isBangla ? 'লগইন' : 'Log in'}
          </button>
          <button className={mode === 'register' ? 'auth-tab active' : 'auth-tab'} type="button" onClick={() => { setMode('register'); setError(''); }}>
            {isBangla ? 'নতুন অ্যাকাউন্ট' : 'Create account'}
          </button>
        </div>
        <div className="auth-card-copy">
          <p className="section-kicker">{mode === 'login' ? (isBangla ? 'ফিরে আসুন' : 'Welcome back') : (isBangla ? 'আজই শুরু করুন' : 'Join the community')}</p>
          <h2>{mode === 'login' ? (isBangla ? 'আপনার অ্যাকাউন্টে প্রবেশ করুন' : 'Sign in to your account') : (isBangla ? 'আপনার নিরাপদ জায়গা তৈরি করুন' : 'Create your private space')}</h2>
        </div>
        <form className="stack-form" onSubmit={handleSubmit}>
          <label>
            <span>{mode === 'login' ? (isBangla ? 'ইউজারনেম বা ইমেইল' : 'Username or email') : (isBangla ? 'ইউজারনেম' : 'Username')}</span>
            <input required value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder={mode === 'login' ? 'you@example.com' : 'yourname'} />
          </label>
          {mode === 'register' ? (
            <label>
              <span>{isBangla ? 'ইমেইল' : 'Email address'}</span>
              <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" placeholder="you@example.com" />
            </label>
          ) : null}
          <label>
            <span>{isBangla ? 'পাসওয়ার্ড' : 'Password'}</span>
            <input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder={isBangla ? 'কমপক্ষে ৮ অক্ষর' : 'At least 8 characters'} />
          </label>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          <button className="button button-wide" disabled={busy} type="submit">
            {busy ? (isBangla ? 'অপেক্ষা করুন…' : 'Please wait…') : mode === 'login' ? (isBangla ? 'লগইন করুন' : 'Log in') : (isBangla ? 'অ্যাকাউন্ট তৈরি করুন' : 'Create my account')}
          </button>
        </form>
        <p className="form-note">{isBangla ? 'অ্যাকাউন্ট খুললে আপনি প্রশ্ন সংরক্ষণ এবং তার অগ্রগতি অনুসরণ করতে পারবেন।' : 'Your account lets you save questions and follow their progress.'}</p>
      </section>
    </div>
  );
}

function statusLabel(status: string, locale: Locale) {
  const labels: Record<string, [string, string]> = {
    draft: ['Draft', 'খসড়া'],
    submitted: ['Submitted', 'জমা হয়েছে'],
    assigned: ['Assigned', 'আলেমকে দেওয়া হয়েছে'],
    in_progress: ['In review', 'পর্যালোচনা চলছে'],
    needs_clarification: ['Needs clarification', 'আরও তথ্য প্রয়োজন'],
    answered: ['Answered', 'উত্তর প্রস্তুত'],
    rejected: ['Needs changes', 'সংশোধন প্রয়োজন'],
    withdrawn: ['Withdrawn', 'প্রত্যাহার করা হয়েছে'],
  };
  return labels[status]?.[locale === 'bn' ? 1 : 0] || status;
}

export function AccountPanel({ locale }: { locale: Locale }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [bookmarks, setBookmarks] = useState<Fatwa[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const isBangla = locale === 'bn';

  useEffect(() => {
    let active = true;
    Promise.all([getCurrentUser(), getMyQuestions(), getBookmarks(), getNotifications()]).then(([profile, ownQuestions, bookmarkData, notificationData]) => {
      if (!active) return;
      setUser(profile);
      setQuestions(ownQuestions);
      setBookmarks(bookmarkData.results.map((item) => item.fatwa));
      setNotifications(notificationData.results);
    }).catch((caught) => {
      if (!active) return;
      clearAuth();
      setError(errorMessage(caught));
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function handleLogout() {
    await logout();
    router.push(`/${locale}`);
    router.refresh();
  }

  if (loading) return <div className="loading-card">{isBangla ? 'আপনার অ্যাকাউন্ট লোড হচ্ছে…' : 'Loading your account…'}</div>;
  if (error || !user) return <div className="empty-state"><p>{error || (isBangla ? 'অ্যাকাউন্ট পাওয়া যায়নি।' : 'Your account could not be loaded.')}</p><Link className="button" href={`/${locale}/auth`}>{isBangla ? 'লগইন' : 'Log in'}</Link></div>;

  return (
    <div className="account-page">
      <div className="account-heading">
        <div>
          <p className="section-kicker">{isBangla ? 'আপনার জায়গা' : 'Your space'}</p>
          <h1>{isBangla ? `স্বাগতম, ${user.display_name || user.username}` : `Welcome, ${user.display_name || user.username}`}</h1>
          <p>{isBangla ? 'আপনার প্রশ্ন, তাদের অগ্রগতি এবং আপনার গোপনীয়তা—সব এক জায়গায়।' : 'Your questions, their progress, and your privacy — all in one place.'}</p>
        </div>
        <div className="account-actions"><Link className="button" href={`/${locale}/ask`}>{isBangla ? '+ প্রশ্ন করুন' : '+ Ask a question'}</Link><button className="button button-ghost" type="button" onClick={handleLogout}>{isBangla ? 'লগআউট' : 'Log out'}</button></div>
      </div>

      <div className="account-stats">
        <div><strong>{questions.length}</strong><span>{isBangla ? 'মোট প্রশ্ন' : 'Total questions'}</span></div>
        <div><strong>{questions.filter((question) => question.status === 'answered').length}</strong><span>{isBangla ? 'উত্তর পাওয়া' : 'Answered'}</span></div>
        <div><strong>{user.email_verified ? '✓' : '!'}</strong><span>{user.email_verified ? (isBangla ? 'ইমেইল যাচাইকৃত' : 'Email verified') : (isBangla ? 'ইমেইল যাচাই বাকি' : 'Verify your email')}</span></div>
      </div>

      <section className="question-list-section">
        <div className="section-heading"><div><p className="section-kicker">{isBangla ? 'আপনার প্রশ্ন' : 'Your questions'}</p><h2>{isBangla ? 'যাত্রার অগ্রগতি' : 'Follow your journey'}</h2></div></div>
        {questions.length ? <div className="question-list">{questions.map((question) => <article className="question-row" key={question.id}><div><span className="question-number">#{String(question.id).padStart(3, '0')}</span><h3>{question.original_title}</h3><p>{question.original_body}</p></div><div className="question-row-meta"><span className={`status status-${question.status}`}>{statusLabel(question.status, locale)}</span><time>{new Date(question.created_at).toLocaleDateString(locale === 'bn' ? 'bn-BD' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</time></div></article>)}</div> : <div className="empty-state"><p>{isBangla ? 'এখনও কোনো প্রশ্ন করা হয়নি।' : 'You have not asked a question yet.'}</p><Link className="button" href={`/${locale}/ask`}>{isBangla ? 'প্রথম প্রশ্ন করুন' : 'Ask your first question'}</Link></div>}
      </section>
      <section className="account-secondary-grid">
        <div className="secondary-card"><p className="section-kicker">{isBangla ? 'সংরক্ষিত' : 'Saved for later'}</p><h2>{isBangla ? 'বুকমার্ক' : 'Bookmarks'}</h2>{bookmarks.length ? <ul className="compact-list">{bookmarks.map((fatwa) => <li key={fatwa.id}><Link href={`/${locale}/fatwas/${fatwa.id}`}>{fatwa.title}</Link></li>)}</ul> : <p className="muted-copy">{isBangla ? 'এখনও কিছু সংরক্ষণ করা হয়নি।' : 'You have not saved any fatwas yet.'}</p>}</div>
        <div className="secondary-card"><p className="section-kicker">{isBangla ? 'আপডেট' : 'Updates'}</p><h2>{isBangla ? 'নোটিফিকেশন' : 'Notifications'}</h2>{notifications.length ? <ul className="compact-list">{notifications.slice(0, 5).map((item) => <li key={item.id}><strong>{item.title}</strong><small>{new Date(item.created_at).toLocaleDateString(locale === 'bn' ? 'bn-BD' : 'en-US')}</small></li>)}</ul> : <p className="muted-copy">{isBangla ? 'নতুন কোনো আপডেট নেই।' : 'You are all caught up.'}</p>}</div>
      </section>
    </div>
  );
}

export function QuestionComposer({ locale, categories }: { locale: Locale; categories: Category[] }) {
  const [session, setSession] = useState<User | null>(null);
  const [sessionReady, setSessionReady] = useState(false);
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [language, setLanguage] = useState(locale);
  const [category, setCategory] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [publicTitle, setPublicTitle] = useState('');
  const [publicBody, setPublicBody] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const isBangla = locale === 'bn';

  useEffect(() => {
    setSession(savedUser());
    setSessionReady(true);
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const question = await createQuestion({ title, body, language, category: category || null, is_public: isPublic });
      try {
        await submitQuestion(question.id, { is_public: isPublic, public_title: isPublic ? publicTitle : undefined, public_body: isPublic ? publicBody : undefined });
        setMessage(isBangla ? 'আপনার প্রশ্ন সফলভাবে জমা হয়েছে।' : 'Your question has been submitted successfully.');
      } catch (caught) {
        const failure = caught as ApiFailure;
        if (failure.code === 'email_unverified') {
          setMessage(isBangla ? 'প্রশ্নটি ডাটাবেজে খসড়া হিসেবে সংরক্ষিত হয়েছে। জমা দিতে ইমেইল যাচাই করুন।' : 'Your question is safely saved as a draft. Verify your email to submit it for review.');
        } else {
          throw caught;
        }
      }
      setTitle('');
      setBody('');
      setPublicTitle('');
      setPublicBody('');
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  if (sessionReady && !session) {
    return <div className="auth-required"><span className="auth-required-mark">✦</span><p className="section-kicker">{isBangla ? 'একটি নিরাপদ জায়গা তৈরি করুন' : 'A private space comes first'}</p><h1>{isBangla ? 'প্রশ্ন করতে লগইন করুন' : 'Log in to ask your question'}</h1><p>{isBangla ? 'আপনার প্রশ্ন নিরাপদে সংরক্ষণ এবং তার অগ্রগতি দেখতে একটি ফ্রি অ্যাকাউন্ট প্রয়োজন।' : 'Create a free account so your question is saved securely and you can follow its progress.'}</p><Link className="button" href={`/${locale}/auth`}>{isBangla ? 'লগইন বা রেজিস্টার' : 'Log in or create an account'}</Link></div>;
  }

  return (
    <div className="ask-layout">
      <section className="ask-intro"><Link className="back-link" href={`/${locale}/account`}>← {isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account'}</Link><p className="section-kicker">{isBangla ? 'আপনার প্রশ্ন' : 'Your question'}</p><h1>{isBangla ? 'যা জানতে চান, বলুন।' : 'Bring your question into the light.'}</h1><p>{isBangla ? 'যত বেশি প্রেক্ষাপট দেবেন, আমাদের আলেমরা তত ভালোভাবে সাহায্য করতে পারবেন।' : 'Share the context that matters. The more we understand, the more thoughtfully our scholars can respond.'}</p><div className="privacy-callout"><span className="trust-icon">✦</span><div><strong>{isBangla ? 'আপনার গোপনীয়তা আগে' : 'Privacy, by design'}</strong><p>{isBangla ? 'প্রশ্ন ডিফল্টভাবে ব্যক্তিগত থাকে। প্রকাশ করতে চাইলে আপনি আলাদা করে অনুমতি দেবেন।' : 'Questions are private by default. You choose separately if a redacted version may be shared publicly.'}</p></div></div></section>
      <section className="composer-card"><form className="stack-form" onSubmit={handleSubmit}><div className="form-section-heading"><span>01</span><div><p className="section-kicker">{isBangla ? 'বিষয়' : 'The essentials'}</p><h2>{isBangla ? 'প্রশ্নটি সংক্ষেপে বলুন' : 'Start with the essentials'}</h2></div></div><label><span>{isBangla ? 'শিরোনাম' : 'Question title'}</span><input required maxLength={240} value={title} onChange={(event) => setTitle(event.target.value)} placeholder={isBangla ? 'যেমন: সফরে নামাজ সম্পর্কে জানতে চাই' : 'e.g. I have a question about prayer while travelling'} /></label><label><span>{isBangla ? 'বিস্তারিত' : 'Share the details'}</span><textarea required rows={7} value={body} onChange={(event) => setBody(event.target.value)} placeholder={isBangla ? 'আপনার পরিস্থিতি, প্রাসঙ্গিক তথ্য এবং আপনি যে বিষয়টি বুঝতে চান তা লিখুন…' : 'Describe your situation, the relevant context, and what you would like to understand…'} /></label><div className="field-grid"><label><span>{isBangla ? 'ভাষা' : 'Answer language'}</span><select value={language} onChange={(event) => setLanguage(event.target.value as Locale)}><option value="bn">বাংলা</option><option value="en">English</option></select></label><label><span>{isBangla ? 'বিষয়' : 'Topic'}</span><select value={category} onChange={(event) => setCategory(event.target.value)}><option value="">{isBangla ? 'বিষয় নির্বাচন করুন' : 'Choose a topic'}</option>{categories.map((item) => <option key={item.slug} value={item.slug}>{isBangla ? item.name_bn : item.name_en}</option>)}</select></label></div><div className="form-section-heading consent-heading"><span>02</span><div><p className="section-kicker">{isBangla ? 'গোপনীয়তা' : 'Your choice'}</p><h2>{isBangla ? 'প্রকাশের অনুমতি' : 'Choose your privacy'}</h2></div></div><label className="checkbox-row"><input type="checkbox" checked={isPublic} onChange={(event) => setIsPublic(event.target.checked)} /><span><strong>{isBangla ? 'পর্যালোচনার পর বেনামে প্রকাশ করা যেতে পারে' : 'Allow a redacted version to be published after review'}</strong><small>{isBangla ? 'আপনার পরিচয় কখনও প্রকাশ করা হবে না।' : 'Your identity is never published.'}</small></span></label>{isPublic ? <div className="public-fields"><label><span>{isBangla ? 'প্রকাশ্য শিরোনাম' : 'Public title'}</span><input required maxLength={240} value={publicTitle} onChange={(event) => setPublicTitle(event.target.value)} /></label><label><span>{isBangla ? 'প্রকাশ্য প্রশ্ন' : 'Public wording'}</span><textarea required rows={4} value={publicBody} onChange={(event) => setPublicBody(event.target.value)} /></label></div> : null}{error ? <p className="form-error" role="alert">{error}</p> : null}{message ? <p className="form-success" role="status">{message}</p> : null}<button className="button button-wide" disabled={busy} type="submit">{busy ? (isBangla ? 'সংরক্ষণ হচ্ছে…' : 'Saving securely…') : (isBangla ? 'প্রশ্ন জমা দিন' : 'Save and submit question')}</button><p className="form-note">{isBangla ? 'প্রথমে আপনার প্রশ্নটি নিরাপদে সংরক্ষণ হবে, তারপর পর্যালোচনার জন্য জমা হবে।' : 'Your question is saved securely first, then sent for review.'}</p></form></section>
    </div>
  );
}
