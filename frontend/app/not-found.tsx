import Link from 'next/link';

export default function NotFound() {
  return (
    <main className="standalone-state">
      <div className="state-mark" aria-hidden="true">✦</div>
      <p className="section-kicker">404 · পথটি পাওয়া যায়নি</p>
      <h1>This page could not be found.</h1>
      <p>পাতাটি হয়তো সরানো হয়েছে, অথবা ঠিকানাটি সঠিক নয়।</p>
      <div className="state-actions"><Link className="button" href="/bn">বাংলা প্রচ্ছদ</Link><Link className="button button-ghost" href="/en">English home</Link></div>
    </main>
  );
}
