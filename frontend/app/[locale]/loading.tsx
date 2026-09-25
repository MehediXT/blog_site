export default function Loading() {
  return (
    <main className="standalone-state loading-state" aria-live="polite" aria-busy="true">
      <div className="state-mark pulse" aria-hidden="true">✦</div>
      <p className="section-kicker">Universe of Ilm</p>
      <h1>Preparing this page…</h1>
    </main>
  );
}
