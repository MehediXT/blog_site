'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  ApiFailure,
  ModerationQuestion,
  ModerationScholar,
  User,
  assignModerationQuestion,
  getCurrentUser,
  getModerationQuestions,
  getModerationScholars,
  moderateScholar,
  savedUser,
} from '../lib/api';

type Locale = 'bn' | 'en';
type Tab = 'applications' | 'assignments';
type ScholarFilter = 'pending' | 'approved' | 'rejected' | 'all';

function messageFor(error: unknown) {
  const failure = error as ApiFailure;
  if (failure.fields) {
    const field = Object.values(failure.fields).find((value) => Array.isArray(value) && value.length);
    if (Array.isArray(field) && typeof field[0] === 'string') return field[0];
  }
  return failure.message || 'Something went wrong. Please try again.';
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status status-${status}`}>{status.replaceAll('_', ' ')}</span>;
}

function formatDate(value: string | null, locale: Locale) {
  if (!value) return locale === 'bn' ? 'এখনও হয়নি' : 'Not yet';
  return new Intl.DateTimeFormat(locale === 'bn' ? 'bn-BD' : 'en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function AssignmentRow({
  question,
  scholars,
  locale,
  onAssigned,
}: {
  question: ModerationQuestion;
  scholars: ModerationScholar[];
  locale: Locale;
  onAssigned: (questionId: number, scholarId: number, reviewerId: number) => Promise<void>;
}) {
  const isBangla = locale === 'bn';
  const [scholarId, setScholarId] = useState('');
  const [reviewerId, setReviewerId] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function handleAssign() {
    if (!scholarId || !reviewerId) return;
    if (scholarId === reviewerId) {
      setError(isBangla ? 'উত্তরদাতা ও পর্যালোচক আলাদা হতে হবে।' : 'Choose two different scholars.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await onAssigned(question.id, Number(scholarId), Number(reviewerId));
    } catch (caught) {
      setError(messageFor(caught));
    } finally {
      setBusy(false);
    }
  }

  return <article className="moderation-question-card">
    <div className="moderation-question-heading">
      <div><span className="question-number">QUESTION #{String(question.id).padStart(4, '0')}</span><h3>{question.original_title}</h3></div>
      <StatusPill status={question.status} />
    </div>
    <p className="moderation-question-body">{question.original_body}</p>
    <div className="moderation-question-meta">
      <span>{isBangla ? 'প্রশ্নকারী' : 'Asked by'}: {question.asker_name}</span>
      {question.category_name ? <span>{question.category_name}</span> : null}
      <span>{question.language.toUpperCase()}</span>
    </div>
    <div className="moderation-assignment-controls">
      <label><span>{isBangla ? 'উত্তরদাতা আলেম' : 'Answering scholar'}</span><select value={scholarId} onChange={(event) => setScholarId(event.target.value)}><option value="">{isBangla ? 'স্কলার নির্বাচন করুন' : 'Select scholar'}</option>{scholars.map((scholar) => <option key={scholar.user_id} value={scholar.user_id} disabled={String(scholar.user_id) === reviewerId}>{scholar.display_name} · {scholar.institution}</option>)}</select></label>
      <label><span>{isBangla ? 'স্বতন্ত্র পর্যালোচক' : 'Independent reviewer'}</span><select value={reviewerId} onChange={(event) => setReviewerId(event.target.value)}><option value="">{isBangla ? 'পর্যালোচক নির্বাচন করুন' : 'Select reviewer'}</option>{scholars.map((scholar) => <option key={scholar.user_id} value={scholar.user_id} disabled={String(scholar.user_id) === scholarId}>{scholar.display_name} · {scholar.institution}</option>)}</select></label>
      <button className="button" type="button" disabled={busy || !scholarId || !reviewerId} onClick={handleAssign}>{busy ? (isBangla ? 'নির্ধারণ হচ্ছে…' : 'Assigning…') : (isBangla ? 'নির্ধারণ করুন' : 'Assign')}</button>
    </div>
    {error ? <p className="form-error" role="alert">{error}</p> : null}
  </article>;
}

export function ModerationPanel({ locale }: { locale: Locale }) {
  const isBangla = locale === 'bn';
  const [user, setUser] = useState<User | null>(null);
  const [scholars, setScholars] = useState<ModerationScholar[]>([]);
  const [questions, setQuestions] = useState<ModerationQuestion[]>([]);
  const [tab, setTab] = useState<Tab>('applications');
  const [filter, setFilter] = useState<ScholarFilter>('pending');
  const [loading, setLoading] = useState(true);
  const [busyScholar, setBusyScholar] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function loadDashboard() {
    const currentUser = await getCurrentUser();
    setUser(currentUser);
    if (!currentUser.moderator) return;
    const [scholarData, questionData] = await Promise.all([
      getModerationScholars(),
      getModerationQuestions(),
    ]);
    setScholars(scholarData.results);
    setQuestions(questionData.results);
  }

  useEffect(() => {
    setUser(savedUser());
    loadDashboard().catch((caught) => setError(messageFor(caught))).finally(() => setLoading(false));
  }, []);

  const activeScholars = useMemo(
    () => scholars.filter((scholar) => scholar.verification_status === 'approved' && !scholar.is_suspended),
    [scholars],
  );
  const visibleScholars = useMemo(
    () => filter === 'all' ? scholars : scholars.filter((scholar) => scholar.verification_status === filter),
    [filter, scholars],
  );

  async function handleDecision(scholar: ModerationScholar, action: 'approve' | 'reject' | 'suspend' | 'unsuspend') {
    const needsNote = action === 'reject' || action === 'suspend';
    const note = needsNote
      ? window.prompt(isBangla ? 'সিদ্ধান্তের কারণ লিখুন' : 'Add a note for this decision')?.trim() || ''
      : '';
    if (needsNote && !note) return;
    setBusyScholar(scholar.user_id);
    setError('');
    setNotice('');
    try {
      const result = await moderateScholar(scholar.user_id, action, note);
      setScholars((items) => items.map((item) => item.user_id === scholar.user_id ? result.scholar : item));
      setNotice(action === 'approve'
        ? (isBangla ? 'স্কলার প্রোফাইল অনুমোদিত হয়েছে।' : 'Scholar profile approved.')
        : action === 'reject'
          ? (isBangla ? 'আবেদনটি প্রত্যাখ্যান করা হয়েছে।' : 'Application rejected.')
          : action === 'suspend'
            ? (isBangla ? 'স্কলার অ্যাকাউন্ট স্থগিত করা হয়েছে।' : 'Scholar account suspended.')
            : (isBangla ? 'স্কলার অ্যাকাউন্ট পুনরায় সক্রিয় হয়েছে।' : 'Scholar account reinstated.'));
    } catch (caught) {
      setError(messageFor(caught));
    } finally {
      setBusyScholar(null);
    }
  }

  async function handleAssign(questionId: number, scholarId: number, reviewerId: number) {
    await assignModerationQuestion(questionId, scholarId, reviewerId);
    setQuestions((items) => items.filter((question) => question.id !== questionId));
    setNotice(isBangla ? 'প্রশ্নটি দুইজন স্কলারের কাছে নির্ধারণ করা হয়েছে।' : 'Question assigned to the scholar and independent reviewer.');
  }

  if (loading) return <div className="loading-card">{isBangla ? 'মডারেশন প্যানেল লোড হচ্ছে…' : 'Loading moderation panel…'}</div>;
  if (error && !user?.moderator) return <section className="moderation-gate"><span className="auth-required-mark">✦</span><p className="section-kicker">{isBangla ? 'প্রশাসক এলাকা' : 'Administrator area'}</p><h1>{isBangla ? 'মডারেটর অনুমতি প্রয়োজন' : 'Moderator access required'}</h1><p>{error}</p><Link className="button" href={`/${locale}/${user ? 'account' : 'auth'}`}>{user ? (isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account') : (isBangla ? 'লগইন করুন' : 'Sign in')}</Link></section>;
  if (!user?.moderator) return <section className="moderation-gate"><span className="auth-required-mark">✦</span><p className="section-kicker">{isBangla ? 'প্রশাসক এলাকা' : 'Administrator area'}</p><h1>{isBangla ? 'মডারেটর অনুমতি প্রয়োজন' : 'Moderator access required'}</h1><p>{isBangla ? 'এই প্যানেল শুধু অনুমোদিত মডারেটরদের জন্য।' : 'This panel is available to authorized moderators only.'}</p><Link className="button" href={`/${locale}/${user ? 'account' : 'auth'}`}>{user ? (isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account') : (isBangla ? 'লগইন করুন' : 'Sign in')}</Link></section>;

  return <div className="moderation-page">
    <header className="moderation-heading"><div><Link className="back-link" href={`/${locale}/account`}>← {isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account'}</Link><p className="section-kicker">{isBangla ? 'মডারেশন ও যাচাই' : 'Moderation & verification'}</p><h1>{isBangla ? 'যোগ্য আলেম, দায়িত্বশীল পর্যালোচনা।' : 'Steward the scholar network.'}</h1><p>{isBangla ? 'আলেমদের যোগ্যতা যাচাই করুন এবং প্রতিটি প্রশ্নে আলাদা উত্তরদাতা ও পর্যালোচক নির্ধারণ করুন।' : 'Review scholar credentials and assign a distinct answering scholar and independent reviewer to each question.'}</p></div></header>
    <div className="moderation-stats"><div><strong>{scholars.filter((item) => item.verification_status === 'pending').length}</strong><span>{isBangla ? 'আবেদন অপেক্ষমাণ' : 'Applications pending'}</span></div><div><strong>{activeScholars.length}</strong><span>{isBangla ? 'সক্রিয় স্কলার' : 'Active scholars'}</span></div><div><strong>{questions.length}</strong><span>{isBangla ? 'নির্ধারণ অপেক্ষমাণ' : 'Questions to assign'}</span></div></div>
    <div className="moderation-tabs"><button type="button" className={tab === 'applications' ? 'scholar-tab active' : 'scholar-tab'} onClick={() => setTab('applications')}>{isBangla ? 'স্কলার আবেদন' : 'Scholar applications'} <span>{scholars.filter((item) => item.verification_status === 'pending').length}</span></button><button type="button" className={tab === 'assignments' ? 'scholar-tab active' : 'scholar-tab'} onClick={() => setTab('assignments')}>{isBangla ? 'প্রশ্ন নির্ধারণ' : 'Question assignments'} <span>{questions.length}</span></button></div>
    {notice ? <p className="form-success moderation-feedback" role="status">{notice}</p> : null}
    {error ? <p className="form-error moderation-feedback" role="alert">{error}</p> : null}
    {tab === 'applications' ? <section className="moderation-section"><div className="moderation-filter" aria-label={isBangla ? 'আবেদনের অবস্থা' : 'Filter applications'}>{(['pending', 'approved', 'rejected', 'all'] as ScholarFilter[]).map((item) => <button key={item} className={filter === item ? 'moderation-filter-active' : ''} type="button" onClick={() => setFilter(item)}>{item === 'all' ? (isBangla ? 'সব' : 'All') : item === 'pending' ? (isBangla ? 'অপেক্ষমাণ' : 'Pending') : item === 'approved' ? (isBangla ? 'অনুমোদিত' : 'Approved') : (isBangla ? 'প্রত্যাখ্যাত' : 'Rejected')}</button>)}</div>
      {visibleScholars.length ? <div className="moderation-scholar-list">{visibleScholars.map((scholar) => <article className="moderation-scholar-card" key={scholar.user_id}>
        <div className="moderation-scholar-top"><div><p className="question-number">{scholar.email}</p><h2>{scholar.display_name}</h2><p>{scholar.institution} · @{scholar.username}</p></div><div className="moderation-badges"><StatusPill status={scholar.verification_status} />{scholar.is_suspended ? <StatusPill status="suspended" /> : null}</div></div>
        <div className="moderation-scholar-details"><div><strong>{isBangla ? 'যোগ্যতা' : 'Qualifications'}</strong><p>{scholar.qualifications}</p></div><div><strong>{isBangla ? 'বিশেষত্ব' : 'Specialties'}</strong><p>{scholar.specialties.join(' · ')}</p></div><div><strong>{isBangla ? 'ভাষা' : 'Languages'}</strong><p>{scholar.languages.join(' · ')}</p></div><div><strong>{isBangla ? 'যাচাইয়ের জন্য পরিচিতি' : 'Background for review'}</strong><p>{scholar.biography}</p></div><div><strong>{isBangla ? 'প্রকাশ্য পরিচিতি' : 'Public biography'}</strong><p>{scholar.public_bio}</p></div></div>
        <div className="moderation-record-meta"><span>{isBangla ? 'আবেদনের তারিখ' : 'Applied'}: {formatDate(scholar.created_at, locale)}</span><span>{isBangla ? 'সর্বশেষ হালনাগাদ' : 'Updated'}: {formatDate(scholar.updated_at, locale)}</span><span>{isBangla ? 'সিদ্ধান্তের তারিখ' : 'Decision date'}: {formatDate(scholar.verified_at, locale)}</span></div>
        {scholar.verification_note ? <p className="moderation-note"><strong>{isBangla ? 'আগের নোট' : 'Decision note'}:</strong> {scholar.verification_note}</p> : null}
        <div className="moderation-card-actions">{scholar.verification_status !== 'approved' ? <button className="button" type="button" disabled={busyScholar === scholar.user_id} onClick={() => handleDecision(scholar, 'approve')}>{isBangla ? 'অনুমোদন' : 'Approve'}</button> : null}{scholar.verification_status !== 'rejected' && !scholar.is_suspended ? <button className="button button-danger" type="button" disabled={busyScholar === scholar.user_id} onClick={() => handleDecision(scholar, scholar.verification_status === 'pending' ? 'reject' : 'suspend')}>{scholar.verification_status === 'pending' ? (isBangla ? 'প্রত্যাখ্যান' : 'Reject') : (isBangla ? 'স্থগিত করুন' : 'Suspend')}</button> : null}{scholar.is_suspended ? <button className="button button-ghost" type="button" disabled={busyScholar === scholar.user_id} onClick={() => handleDecision(scholar, 'unsuspend')}>{isBangla ? 'পুনরায় সক্রিয় করুন' : 'Reinstate'}</button> : null}</div>
      </article>)}</div> : <div className="empty-state">{isBangla ? 'এই ফিল্টারে কোনো স্কলার প্রোফাইল নেই।' : 'No scholar profiles match this filter.'}</div>}
    </section> : <section className="moderation-section">{activeScholars.length < 2 ? <div className="empty-state">{isBangla ? 'প্রশ্ন নির্ধারণের আগে কমপক্ষে দুইজন সক্রিয় স্কলার অনুমোদন করুন।' : 'Approve at least two active scholars before assigning questions.'}</div> : questions.length ? <div className="moderation-question-list">{questions.map((question) => <AssignmentRow key={question.id} question={question} scholars={activeScholars} locale={locale} onAssigned={handleAssign} />)}</div> : <div className="empty-state">{isBangla ? 'এখন কোনো প্রশ্ন নির্ধারণের অপেক্ষায় নেই।' : 'No questions are waiting for assignment.'}</div>}</section>}
  </div>;
}
