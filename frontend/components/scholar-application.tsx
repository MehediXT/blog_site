'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import {
  ApiFailure,
  Locale,
  ScholarApplication,
  getCurrentUser,
  getScholarApplication,
  savedUser,
  submitScholarApplication,
} from '../lib/api';

function errorMessage(error: unknown) {
  const failure = error as ApiFailure;
  if (failure.fields) {
    const firstField = Object.values(failure.fields).find((value) => Array.isArray(value) && value.length);
    if (Array.isArray(firstField) && typeof firstField[0] === 'string') return firstField[0];
  }
  return failure.message || 'Something went wrong. Please try again.';
}

function applicationStatus(status: ScholarApplication['verification_status'], locale: Locale) {
  const labels = {
    pending: locale === 'bn' ? 'পর্যালোচনা অপেক্ষমাণ' : 'Awaiting review',
    approved: locale === 'bn' ? 'অনুমোদিত' : 'Approved',
    rejected: locale === 'bn' ? 'সংশোধন প্রয়োজন' : 'Changes required',
  };
  return labels[status];
}

export function ScholarApplicationForm({ locale }: { locale: Locale }) {
  const isBangla = locale === 'bn';
  const [sessionReady, setSessionReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const [emailVerified, setEmailVerified] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [application, setApplication] = useState<ScholarApplication | null>(null);
  const [institution, setInstitution] = useState('');
  const [qualifications, setQualifications] = useState('');
  const [specialties, setSpecialties] = useState('');
  const [languages, setLanguages] = useState<Locale[]>([locale]);
  const [biography, setBiography] = useState('');
  const [publicBio, setPublicBio] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    const hasSession = Boolean(savedUser());
    setSignedIn(hasSession);
    setSessionReady(true);
    if (!hasSession) {
      setLoading(false);
      return;
    }

    async function loadApplication() {
      try {
        const user = await getCurrentUser();
        setEmailVerified(Boolean(user.email_verified));
        const { scholar_profile } = await getScholarApplication();
        setApplication(scholar_profile);
        if (!scholar_profile) return;
        setInstitution(scholar_profile.institution);
        setQualifications(scholar_profile.qualifications);
        setSpecialties(scholar_profile.specialties.join(', '));
        setLanguages(scholar_profile.languages);
        setBiography(scholar_profile.biography);
        setPublicBio(scholar_profile.public_bio);
      } catch (caught) {
        setError(errorMessage(caught));
      } finally {
        setLoading(false);
      }
    }
    void loadApplication();
  }, []);

  function toggleLanguage(language: Locale) {
    setLanguages((current) => current.includes(language)
      ? current.filter((item) => item !== language)
      : [...current, language]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setNotice('');
    if (emailVerified === false) {
      setError(isBangla
        ? 'স্কলার আবেদন করার আগে ইমেইল যাচাই করুন। আপনার যাচাইকরণ ইমেইলের লিংকে ক্লিক করুন।'
        : 'Verify your email before applying. Open the verification email and follow its link.');
      return;
    }
    if (!languages.length) {
      setError(isBangla ? 'কমপক্ষে একটি ভাষা নির্বাচন করুন।' : 'Select at least one language.');
      return;
    }
    const specialtyList = specialties.split(',').map((item) => item.trim()).filter(Boolean);
    if (!specialtyList.length) {
      setError(isBangla ? 'কমপক্ষে একটি বিশেষত্ব লিখুন।' : 'Add at least one specialty.');
      return;
    }

    setBusy(true);
    try {
      const result = await submitScholarApplication({
        institution: institution.trim(),
        qualifications: qualifications.trim(),
        specialties: specialtyList,
        languages,
        biography: biography.trim(),
        public_bio: publicBio.trim(),
      });
      setApplication(result.scholar_profile);
      setNotice(isBangla
        ? 'আপনার স্কলার প্রোফাইল যাচাইয়ের জন্য জমা হয়েছে।'
        : 'Your scholar profile has been submitted for verification.');
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(false);
    }
  }

  if (!sessionReady || loading) return <div className="loading-card">{isBangla ? 'স্কলার আবেদন লোড হচ্ছে…' : 'Loading scholar application…'}</div>;

  if (!signedIn) return (
    <div className="scholar-application-gate">
      <span className="auth-required-mark">✦</span>
      <p className="section-kicker">{isBangla ? 'স্কলার আবেদন' : 'Scholar application'}</p>
      <h1>{isBangla ? 'আবেদন করতে লগইন করুন' : 'Sign in before applying'}</h1>
      <p>{isBangla ? 'স্কলার প্রোফাইল আপনার যাচাইকৃত অ্যাকাউন্টের সঙ্গে যুক্ত হবে।' : 'Your scholar profile must be connected to your verified account.'}</p>
      <Link className="button" href={`/${locale}/auth`}>{isBangla ? 'লগইন করুন' : 'Log in'}</Link>
    </div>
  );

  return (
    <div className="scholar-application-page">
      <header className="scholar-application-heading">
        <Link className="back-link" href={`/${locale}/account`}>← {isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account'}</Link>
        <div className="scholar-application-title">
          <div><p className="section-kicker">{isBangla ? 'স্কলার যাচাই' : 'Scholar verification'}</p><h1>{isBangla ? 'আপনার স্কলার প্রোফাইল তৈরি করুন।' : 'Create your scholar profile.'}</h1></div>
          <p>{isBangla ? 'আপনার শিক্ষা, অভিজ্ঞতা ও বিশেষত্বের তথ্য দিন। প্রশাসক যাচাই ও অনুমোদন করার পর স্কলার ওয়ার্কস্পেস সক্রিয় হবে।' : 'Tell us about your study, experience, and specialisms. Your scholar workspace activates only after an administrator verifies and approves the profile.'}</p>
        </div>
      </header>

      {application ? (
        <div className={`application-status application-status-${application.verification_status}`}>
          <div><span aria-hidden="true">{application.verification_status === 'approved' ? '✓' : application.verification_status === 'rejected' ? '!' : '◌'}</span><div><small>{isBangla ? 'বর্তমান অবস্থা' : 'Current status'}</small><strong>{applicationStatus(application.verification_status, locale)}</strong></div></div>
          <p>{application.verification_status === 'approved'
            ? (isBangla ? 'আপনার স্কলার ওয়ার্কস্পেস সক্রিয়। তথ্য পরিবর্তন করলে আবার যাচাই প্রয়োজন হবে।' : 'Your scholar workspace is active. Editing these details will require verification again.')
            : application.verification_status === 'rejected'
              ? (isBangla ? 'তথ্য সংশোধন করে আবার জমা দিতে পারেন।' : 'Update the information below and submit it again.')
              : (isBangla ? 'অ্যাডমিন আপনার যোগ্যতা ও তথ্য যাচাই করবেন। এর মধ্যে আপনি আবেদনটি হালনাগাদ করতে পারেন।' : 'An administrator will verify your details. You can update the application while it is pending.')}</p>
          {application.can_author ? <Link className="text-link" href={`/${locale}/scholar`}>{isBangla ? 'স্কলার প্যানেল খুলুন' : 'Open scholar panel'} →</Link> : null}
        </div>
      ) : null}

      <form className="scholar-application-form" onSubmit={handleSubmit}>
        {emailVerified === false ? <div className="scholar-verification-notice" role="status">
          <strong>{isBangla ? 'ইমেইল যাচাই প্রয়োজন' : 'Email verification required'}</strong>
          <p>{isBangla ? 'প্রোফাইল জমা দেওয়ার আগে আপনার অ্যাকাউন্টের ইমেইল যাচাই করুন। নিবন্ধনের সময় পাঠানো ইমেইলের লিংক ব্যবহার করুন।' : 'Verify the email on your account before submitting a profile. Use the link sent when you registered.'}</p>
        </div> : null}
        <section>
          <div className="application-section-heading"><span>01</span><div><p className="section-kicker">{isBangla ? 'যোগ্যতা' : 'Credentials'}</p><h2>{isBangla ? 'আপনার শিক্ষা ও প্রতিষ্ঠান' : 'Your study and institution'}</h2></div></div>
          <label><span>{isBangla ? 'প্রতিষ্ঠান' : 'Institution'}</span><input required maxLength={200} value={institution} onChange={(event) => setInstitution(event.target.value)} placeholder={isBangla ? 'প্রধান শিক্ষা প্রতিষ্ঠান বা মাদরাসা' : 'Primary institution or seminary'} /></label>
          <label><span>{isBangla ? 'যোগ্যতা' : 'Qualifications'}</span><textarea required rows={4} value={qualifications} onChange={(event) => setQualifications(event.target.value)} placeholder={isBangla ? 'ডিগ্রি, ইজাযাহ, শিক্ষক ও সম্পন্ন শিক্ষাক্রম লিখুন' : 'List degrees, ijazahs, teachers, and completed programmes'} /></label>
          <label><span>{isBangla ? 'বিশেষত্ব' : 'Specialties'}</span><input required value={specialties} onChange={(event) => setSpecialties(event.target.value)} placeholder={isBangla ? 'যেমন: ফিকহ, পরিবার, ইসলামি অর্থনীতি' : 'e.g. Fiqh, family matters, Islamic finance'} /><small>{isBangla ? 'কমা দিয়ে আলাদা করুন' : 'Separate each specialty with a comma'}</small></label>
          <fieldset><legend>{isBangla ? 'যে ভাষায় উত্তর দিতে পারেন' : 'Languages you can answer in'}</legend><label className="language-option"><input type="checkbox" checked={languages.includes('bn')} onChange={() => toggleLanguage('bn')} /><span>বাংলা</span></label><label className="language-option"><input type="checkbox" checked={languages.includes('en')} onChange={() => toggleLanguage('en')} /><span>English</span></label></fieldset>
        </section>

        <section>
          <div className="application-section-heading"><span>02</span><div><p className="section-kicker">{isBangla ? 'অভিজ্ঞতা' : 'Background'}</p><h2>{isBangla ? 'যাচাইয়ের জন্য পরিচিতি' : 'Background for verification'}</h2></div></div>
          <label><span>{isBangla ? 'বিস্তারিত ব্যক্তিগত পরিচিতি' : 'Detailed background'}</span><textarea required rows={7} value={biography} onChange={(event) => setBiography(event.target.value)} placeholder={isBangla ? 'আপনার পড়াশোনা, শিক্ষকতা, গবেষণা ও কাজের অভিজ্ঞতা লিখুন' : 'Describe your studies, teaching, research, and relevant experience'} /><small>{isBangla ? 'এই লেখা যাচাইয়ের কাজে ব্যবহৃত হবে।' : 'Used by administrators during verification.'}</small></label>
          <label><span>{isBangla ? 'প্রকাশ্য সংক্ষিপ্ত জীবনী' : 'Public biography'}</span><textarea required rows={5} value={publicBio} onChange={(event) => setPublicBio(event.target.value)} placeholder={isBangla ? 'অনুমোদনের পর স্কলার ডিরেক্টরিতে যে পরিচিতি দেখাবেন' : 'The biography shown in the scholar directory after approval'} /><small>{isBangla ? 'ব্যক্তিগত যোগাযোগের তথ্য লিখবেন না।' : 'Do not include private contact information.'}</small></label>
        </section>

        <div className="application-submit">
          <div><strong>{isBangla ? 'জমা দেওয়ার আগে' : 'Before submitting'}</strong><p>{isBangla ? 'তথ্য সত্য ও সম্পূর্ণ কিনা নিশ্চিত করুন। অনুমোদন শুধু প্রশাসক দিতে পারেন।' : 'Confirm that your information is accurate and complete. Only an administrator can approve a profile.'}</p></div>
          {error ? <p className="form-error" role="alert">{error}</p> : null}
          {notice ? <p className="form-success" role="status">{notice}</p> : null}
          <button className="button" type="submit" disabled={busy || emailVerified === false}>{busy ? (isBangla ? 'জমা হচ্ছে…' : 'Submitting…') : application ? (isBangla ? 'হালনাগাদ করে আবার জমা দিন' : 'Update and resubmit') : (isBangla ? 'যাচাইয়ের জন্য জমা দিন' : 'Submit for verification')}</button>
        </div>
      </form>
    </div>
  );
}
