'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  addBookmark,
  ApiFailure,
  getBookmarks,
  removeBookmark,
  reportFatwa,
  savedUser,
  type Locale,
} from '../lib/api';

export function FatwaActions({ publicationId, locale }: { publicationId: number; locale: Locale }) {
  const isBangla = locale === 'bn';
  const [signedIn, setSignedIn] = useState(false);
  const [bookmarked, setBookmarked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');

  useEffect(() => {
    setSignedIn(Boolean(savedUser()));
    if (!savedUser()) return;
    getBookmarks().then(({ results }) => {
      setBookmarked(results.some((item) => item.fatwa.id === publicationId));
    }).catch(() => undefined);
  }, [publicationId]);

  async function toggleBookmark() {
    setBusy(true);
    setNotice('');
    try {
      if (bookmarked) {
        await removeBookmark(publicationId);
        setBookmarked(false);
        setNotice(isBangla ? 'বুকমার্ক সরানো হয়েছে।' : 'Removed from bookmarks.');
      } else {
        await addBookmark(publicationId);
        setBookmarked(true);
        setNotice(isBangla ? 'বুকমার্কে রাখা হয়েছে।' : 'Saved to your bookmarks.');
      }
    } catch (caught) {
      const failure = caught as ApiFailure;
      setNotice(failure.message || (isBangla ? 'লগইন করে আবার চেষ্টা করুন।' : 'Please sign in and try again.'));
    } finally {
      setBusy(false);
    }
  }

  async function report() {
    const reason = window.prompt(isBangla ? 'সমস্যাটি সংক্ষেপে লিখুন' : 'Briefly describe the issue');
    if (!reason?.trim()) return;
    try {
      await reportFatwa(publicationId, reason.trim());
      setNotice(isBangla ? 'রিপোর্টটি পর্যালোচনার জন্য পাঠানো হয়েছে।' : 'Thank you. Your report was sent for review.');
    } catch (caught) {
      const failure = caught as ApiFailure;
      setNotice(failure.message || (isBangla ? 'রিপোর্ট পাঠানো যায়নি।' : 'The report could not be sent.'));
    }
  }

  async function share() {
    const shareData = { title: document.title, url: window.location.href };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(window.location.href);
        setNotice(isBangla ? 'লিংক কপি করা হয়েছে।' : 'Link copied to your clipboard.');
      }
    } catch {
      // Closing the native share sheet is not an error the reader needs to see.
    }
  }

  if (!signedIn) {
    return <div className="detail-actions"><Link className="button button-ghost" href={`/${locale}/auth`}>{isBangla ? 'সংরক্ষণ করতে লগইন করুন' : 'Sign in to save'}</Link><button className="text-button" type="button" onClick={share}>{isBangla ? 'শেয়ার' : 'Share'}</button><button className="text-button" type="button" onClick={() => window.print()}>{isBangla ? 'প্রিন্ট' : 'Print'}</button>{notice ? <span className="action-notice" role="status">{notice}</span> : null}</div>;
  }

  return <div className="detail-actions">
    <button className="button button-ghost" type="button" disabled={busy} onClick={toggleBookmark}>{bookmarked ? (isBangla ? '★ সংরক্ষিত' : '★ Saved') : (isBangla ? '☆ সংরক্ষণ' : '☆ Save')}</button>
    <button className="text-button" type="button" onClick={share}>{isBangla ? 'শেয়ার' : 'Share'}</button>
    <button className="text-button" type="button" onClick={() => window.print()}>{isBangla ? 'প্রিন্ট' : 'Print'}</button>
    <button className="text-button" type="button" onClick={report}>{isBangla ? 'রিপোর্ট' : 'Report an issue'}</button>
    {notice ? <span className="action-notice" role="status">{notice}</span> : null}
  </div>;
}
