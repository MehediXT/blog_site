'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import {
  ApiFailure,
  Methodology,
  Question,
  ReviewItem,
  User,
  getCurrentUser,
  getReviewQueue,
  getScholarAssignments,
  reviewRevision,
  saveAnswer,
} from '../lib/api';

type Locale = 'bn' | 'en';

function messageFor(error: unknown) {
  const failure = error as ApiFailure;
  if (failure.fields) {
    const field = Object.values(failure.fields).find((value) => Array.isArray(value) && value.length);
    if (Array.isArray(field) && typeof field[0] === 'string') return field[0];
  }
  return failure.message || 'Something went wrong. Please try again.';
}

function statusText(status: string, locale: Locale) {
  const labels: Record<string, [string, string]> = {
    assigned: ['Assigned', 'নির্ধারিত'],
    in_progress: ['In progress', 'কাজ চলছে'],
    needs_clarification: ['Needs clarification', 'আরও ব্যাখ্যা প্রয়োজন'],
  };
  return labels[status]?.[locale === 'bn' ? 1 : 0] || status;
}

function AnswerEditor({ question, locale, methodologies, onSaved }: { question: Question; locale: Locale; methodologies: Methodology[]; onSaved: (questionId: number, status: string) => void }) {
  const isBangla = locale === 'bn';
  const [body, setBody] = useState('');
  const [references, setReferences] = useState('');
  const [methodology, setMethodology] = useState('');
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>, action: 'save' | 'submit_for_review') {
    event.preventDefault();
    setBusy(true);
    setNotice('');
    setError('');
    try {
      const result = await saveAnswer(question.id, {
        body,
        language: question.language,
        references: references.split('\n').map((item) => item.trim()).filter(Boolean),
        methodology_id: methodology ? Number(methodology) : null,
        action,
      });
      onSaved(question.id, result.status);
      setNotice(action === 'save' ? (isBangla ? 'খসড়া সংরক্ষিত হয়েছে।' : 'Draft saved.') : (isBangla ? 'উত্তর পর্যালোচনার জন্য জমা হয়েছে।' : 'Answer submitted for independent review.'));
    } catch (caught) {
      setError(messageFor(caught));
    } finally {
      setBusy(false);
    }
  }

  return <form className="answer-editor" onSubmit={(event) => submit(event, 'save')}>
    <label><span>{isBangla ? 'আপনার উত্তর' : 'Your answer'}</span><textarea required rows={8} value={body} onChange={(event) => setBody(event.target.value)} placeholder={isBangla ? 'দলিল ও প্রাসঙ্গিক ব্যাখ্যাসহ উত্তর লিখুন…' : 'Write a careful answer with relevant reasoning and evidence…'} /></label>
    <div className="field-grid"><label><span>{isBangla ? 'পদ্ধতি' : 'Methodology'}</span><select value={methodology} onChange={(event) => setMethodology(event.target.value)}><option value="">{isBangla ? 'পদ্ধতি নির্বাচন করুন' : 'Select methodology'}</option>{methodologies.map((item) => <option key={item.id || item.slug} value={item.id}>{isBangla ? item.name_bn : item.name_en}</option>)}</select></label><label><span>{isBangla ? 'ভাষা' : 'Language'}</span><input readOnly value={question.language === 'bn' ? 'বাংলা' : 'English'} /></label></div>
    <label><span>{isBangla ? 'তথ্যসূত্র' : 'References'} <small>({isBangla ? 'প্রতি লাইনে একটি' : 'one per line'})</small></span><textarea rows={3} value={references} onChange={(event) => setReferences(event.target.value)} placeholder="Qur'an 2:286\nSahih al-Bukhari 1" /></label>
    {error ? <p className="form-error" role="alert">{error}</p> : null}{notice ? <p className="form-success" role="status">{notice}</p> : null}
    <div className="answer-actions"><button className="button button-ghost" disabled={busy} type="submit">{busy ? (isBangla ? 'সংরক্ষণ…' : 'Saving…') : (isBangla ? 'খসড়া সংরক্ষণ' : 'Save draft')}</button><button className="button" disabled={busy} type="button" onClick={(event) => submit(event as unknown as FormEvent<HTMLFormElement>, 'submit_for_review')}>{isBangla ? 'পর্যালোচনায় পাঠান' : 'Submit for review'}</button></div>
  </form>;
}

function AssignmentCard({ question, locale, methodologies, onSaved }: { question: Question; locale: Locale; methodologies: Methodology[]; onSaved: (questionId: number, status: string) => void }) {
  const [open, setOpen] = useState(false);
  const isBangla = locale === 'bn';
  return <article className="scholar-assignment"><button className="assignment-trigger" type="button" onClick={() => setOpen((value) => !value)}><div><span className="question-number">#{String(question.id).padStart(3, '0')} · {statusText(question.status, locale)}</span><h3>{question.original_title}</h3><p>{question.original_body}</p></div><span className="assignment-chevron">{open ? '−' : '+'}</span></button>{open ? <div className="assignment-workspace"><div className="original-question"><p className="section-kicker">{isBangla ? 'প্রশ্ন' : 'Question'}</p><p>{question.original_body}</p>{question.is_public ? <span className="public-badge">{isBangla ? 'প্রকাশের অনুমতি আছে' : 'Public consent given'}</span> : <span className="private-badge">{isBangla ? 'ব্যক্তিগত' : 'Private'}</span>}</div><AnswerEditor question={question} locale={locale} methodologies={methodologies} onSaved={onSaved} /></div> : null}</article>;
}

export function ScholarPanel({ locale, methodologies }: { locale: Locale; methodologies: Methodology[] }) {
  const isBangla = locale === 'bn';
  const [user, setUser] = useState<User | null>(null);
  const [assignments, setAssignments] = useState<Question[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [tab, setTab] = useState<'assignments' | 'reviews'>('assignments');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function loadQueues() {
    const profile = await getCurrentUser();
    setUser(profile);
    if (!profile.scholar) return;
    const [assignmentData, reviewData] = await Promise.all([getScholarAssignments(), getReviewQueue()]);
    setAssignments(assignmentData.results);
    setReviews(reviewData.results);
  }

  useEffect(() => {
    loadQueues().catch((caught) => setError(messageFor(caught))).finally(() => setLoading(false));
  }, []);

  function markSaved(questionId: number, status: string) {
    setAssignments((items) => items.map((item) => item.id === questionId ? { ...item, status } : item));
  }

  async function decide(revisionId: number, action: 'approve' | 'request-changes' | 'reject') {
    const feedback = action === 'approve' ? '' : window.prompt(isBangla ? 'অনুগ্রহ করে ফিডব্যাক লিখুন' : 'Add feedback for the scholar') || '';
    if (action !== 'approve' && !feedback.trim()) return;
    try {
      await reviewRevision(revisionId, action, feedback);
      setReviews((items) => items.filter((item) => item.id !== revisionId));
    } catch (caught) {
      setError(messageFor(caught));
    }
  }

  if (loading) return <div className="loading-card">{isBangla ? 'স্কলার ওয়ার্কস্পেস লোড হচ্ছে…' : 'Loading your scholar workspace…'}</div>;
  if (error) return <div className="empty-state"><p>{error}</p><button className="button" type="button" onClick={() => { setError(''); setLoading(true); loadQueues().catch((caught) => setError(messageFor(caught))).finally(() => setLoading(false)); }}>{isBangla ? 'আবার চেষ্টা করুন' : 'Try again'}</button></div>;
  if (!user?.scholar) return <div className="scholar-gate"><span className="auth-required-mark">✦</span><p className="section-kicker">{isBangla ? 'অনুমোদিত স্কলারদের জন্য' : 'For approved scholars'}</p><h1>{isBangla ? 'আপনার স্কলার প্যানেল এখনও সক্রিয় নয়' : 'Your scholar panel is not active yet'}</h1><p>{isBangla ? 'স্কলার প্রোফাইল তৈরি করে যাচাইয়ের জন্য জমা দিন। অ্যাডমিন অনুমোদন করলে এখানে নির্ধারিত প্রশ্ন ও পর্যালোচনা দেখতে পাবেন।' : 'Create a scholar profile and submit it for verification. Once an administrator approves it, assigned questions and independent reviews will appear here.'}</p><div className="gate-actions"><Link className="button" href={`/${locale}/scholar/apply`}>{isBangla ? 'স্কলার প্রোফাইল তৈরি করুন' : 'Create scholar profile'}</Link><Link className="button button-ghost" href={`/${locale}/account`}>{isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account'}</Link></div></div>;

  return <div className="scholar-page"><div className="scholar-heading"><div><Link className="back-link" href={`/${locale}/account`}>← {isBangla ? 'অ্যাকাউন্টে ফিরুন' : 'Back to account'}</Link><p className="section-kicker">{isBangla ? 'স্কলার ওয়ার্কস্পেস' : 'Scholar workspace'}</p><h1>{isBangla ? 'জ্ঞানকে যত্নের সঙ্গে উত্তর দিন।' : 'Answer with knowledge and care.'}</h1><p>{isBangla ? 'নির্ধারিত প্রশ্নের উত্তর লিখুন এবং স্বাধীন পর্যালোচনার জন্য পাঠান।' : 'Respond to assigned questions and send each answer through independent review.'}</p></div></div><div className="scholar-stats"><div><strong>{assignments.length}</strong><span>{isBangla ? 'নির্ধারিত প্রশ্ন' : 'Assigned questions'}</span></div><div><strong>{assignments.filter((item) => item.status === 'needs_clarification').length}</strong><span>{isBangla ? 'ব্যাখ্যা প্রয়োজন' : 'Need clarification'}</span></div><div><strong>{reviews.length}</strong><span>{isBangla ? 'পর্যালোচনা অপেক্ষমাণ' : 'Reviews waiting'}</span></div></div><div className="scholar-tabs"><button className={tab === 'assignments' ? 'scholar-tab active' : 'scholar-tab'} type="button" onClick={() => setTab('assignments')}>{isBangla ? 'আমার নির্ধারিত প্রশ্ন' : 'My assignments'} <span>{assignments.length}</span></button><button className={tab === 'reviews' ? 'scholar-tab active' : 'scholar-tab'} type="button" onClick={() => setTab('reviews')}>{isBangla ? 'স্বাধীন পর্যালোচনা' : 'Review queue'} <span>{reviews.length}</span></button></div>{tab === 'assignments' ? <section className="scholar-queue">{assignments.length ? assignments.map((question) => <AssignmentCard key={question.id} question={question} locale={locale} methodologies={methodologies} onSaved={markSaved} />) : <div className="empty-state">{isBangla ? 'এখনও কোনো প্রশ্ন নির্ধারিত হয়নি।' : 'No questions have been assigned to you yet.'}</div>}</section> : <section className="scholar-queue">{reviews.length ? reviews.map((item) => <article className="review-card" key={item.id}><div className="review-meta"><span className="question-number">REVISION {item.revision_number} · QUESTION #{item.question.id}</span><time>{new Date(item.submitted_at).toLocaleDateString(locale === 'bn' ? 'bn-BD' : 'en-US')}</time></div><h3>{item.question.original_title}</h3><div className="review-question"><p className="section-kicker">{isBangla ? 'প্রশ্ন' : 'Question'}</p><p>{item.question.original_body}</p></div><div className="review-answer"><p className="section-kicker">{isBangla ? 'উত্তর' : 'Answer'}</p><p>{item.body}</p></div><div className="review-actions"><button className="button button-ghost" type="button" onClick={() => decide(item.id, 'request-changes')}>{isBangla ? 'সংশোধন চান' : 'Request changes'}</button><button className="button button-danger" type="button" onClick={() => decide(item.id, 'reject')}>{isBangla ? 'প্রত্যাখ্যান' : 'Reject'}</button><button className="button" type="button" onClick={() => decide(item.id, 'approve')}>{isBangla ? 'অনুমোদন ও প্রকাশ' : 'Approve & release'}</button></div></article>) : <div className="empty-state">{isBangla ? 'এখনও কোনো উত্তর পর্যালোচনার জন্য অপেক্ষমাণ নয়।' : 'No answers are waiting for review.'}</div>}</section>}</div>;
}
