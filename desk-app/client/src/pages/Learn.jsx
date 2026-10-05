export default function Learn({ meta }) {
  const concepts = meta?.concepts || [];
  const guide = meta?.cat_guide || {};
  const stats = meta?.cat_stats || {};

  return (
    <>
      <section className="hero">
        <h1>Concepts</h1>
        <p>Base, bear, bull, CAGR, overlap, drawdown — and what each SEBI category is for.</p>
      </section>
      <div className="panel">
        <h2>Forecast & risk terms</h2>
        {concepts.map((c) => (
          <details key={c.id} className="concept">
            <summary>{c.term} — {c.short}</summary>
            <div className="body">{c.detail}</div>
          </details>
        ))}
      </div>
      <div className="panel">
        <h2>Category guide</h2>
        <div className="fcards">
          {Object.entries(guide).map(([k, g]) => {
            const s = stats[k] || {};
            return (
              <div key={k} className="fcard">
                <h3>{g.label}</h3>
                <p className="muted" style={{ margin: 0 }}>{g.sebi}</p>
                <p style={{ margin: "8px 0 0", fontSize: 13 }}><b>Risk:</b> {g.risk}</p>
                <p style={{ margin: "4px 0 0", fontSize: 13 }}><b>Role:</b> {g.role}</p>
                {s.n ? (
                  <p className="muted" style={{ fontSize: 12, marginTop: 8 }}>
                    Median in list: 3Y {s.r3}% · vol {s.vol}% · DD {s.dd}%
                  </p>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
}
