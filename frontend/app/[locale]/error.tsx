'use client';

export default function LocaleError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="standalone-state">
      <div className="state-mark" aria-hidden="true">!</div>
      <p className="section-kicker">Something went wrong · কিছু সমস্যা হয়েছে</p>
      <h1>We could not open this page.</h1>
      <p>অনুগ্রহ করে আবার চেষ্টা করুন।</p>
      <button className="button" type="button" onClick={reset}>Try again · আবার চেষ্টা করুন</button>
    </main>
  );
}
