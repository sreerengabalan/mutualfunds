import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import FundLink from "../components/FundLink";
import { useFilters } from "../lib/FiltersContext";
import { hrefFor } from "../lib/persist";
import { api, catLabel, inr, n, SECTOR_COLORS } from "../lib/utils";

function Metric({ label, value, hint }) {
  return (
    <div className="metric">
      <b>{value}</b>
      <span>{label}</span>
      {hint ? <em>{hint}</em> : null}
    </div>
  );
}

function AllocBar({ label, pct, color }) {
  const w = Math.max(0, Math.min(100, Number(pct) || 0));
  return (
    <div className="alloc-row">
      <div>{label}</div>
      <div className="alloc-track">
        <div className="alloc-fill" style={{ width: `${w}%`, background: color || undefined }} />
      </div>
      <div className="num">{n(w, 1)}%</div>
    </div>
  );
}

export default function Fund({ funds }) {
  const { code } = useParams();
  const navTo = useNavigate();
  const { compare } = useFilters();
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [other, setOther] = useState("");

  useEffect(() => {
    setData(null);
    setErr("");
    api(`/api/funds/${code}`)
      .then((f) => {
        setData(f);
        const alt = funds.find((x) => String(x.code) !== String(f.code));
        setOther(String(alt?.code || ""));
      })
      .catch((e) => setErr(String(e.message || e)));
  }, [code, funds]);

  const navPts = data?.nav || [];
  const navMin = useMemo(() => (navPts.length ? Math.min(...navPts.map((p) => p[1])) : 0), [navPts]);
  const navMax = useMemo(() => (navPts.length ? Math.max(...navPts.map((p) => p[1])) : 1), [navPts]);
  const holdings = [...(data?.holdings || [])].sort((a, b) => (b.w || 0) - (a.w || 0));
  const secs = data?.sec || [];
  const themes = data?.themes || {};

  if (err) {
    return (
      <div className="warnbox" style={{ marginTop: 24 }}>
        Fund not found. <Link to="/funds">Back to all funds</Link>
        <div>{err}</div>
      </div>
    );
  }
  if (!data) return <p className="muted" style={{ marginTop: 24 }}>Loading fund…</p>;

  return (
    <>
      <section className="hero">
        <p className="muted" style={{ margin: 0 }}>
          <Link to="/funds">All funds</Link>
          {" · "}
          {catLabel(data.cat)}
          {" · "}
          Scheme code {data.code}
        </p>
        <h1>{data.name}</h1>
        <p>
          {data.full || data.name}
          <br />
          {data.house} · Manager: {data.mgr || "—"} · Inception {data.incept || "—"}
        </p>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 14 }}>
          <Link
            className="btn"
            to={hrefFor("/compare", {
              ...compare,
              a: String(data.code),
              b: compare.b && String(compare.b) !== String(data.code) ? compare.b : other,
              catA: data.cat || compare.catA,
            })}
          >
            Compare this fund
          </Link>
          <a className="btn ghost" href={`https://api.mfapi.in/mf/${data.code}`} target="_blank" rel="noreferrer">
            Verify NAV on mfapi
          </a>
          <a className="btn ghost" href="https://www.amfiindia.com/net-asset-value/nav-history" target="_blank" rel="noreferrer">
            AMFI NAV history
          </a>
        </div>
      </section>

      <div className="stats">
        <div className="stat"><b>{n(data.nav, 2)}</b><span>NAV ({data.navd || "—"})</span></div>
        <div className="stat"><b>₹{n(data.aum, 0)} Cr</b><span>AUM</span></div>
        <div className="stat"><b>{n(data.ter, 2)}%</b><span>TER (Direct)</span></div>
        <div className="stat"><b>{n(data.yrs, 1)}Y</b><span>Track record</span></div>
      </div>

      {data.cat_guide && (
        <div className="panel">
          <h2>{data.cat_guide.label || catLabel(data.cat)}</h2>
          <p className="muted" style={{ margin: 0 }}>{data.cat_guide.sebi}</p>
          <p style={{ margin: "8px 0 0", fontSize: 14 }}><b>Risk:</b> {data.cat_guide.risk}</p>
          <p style={{ margin: "4px 0 0", fontSize: 14 }}><b>Role in a 15Y plan:</b> {data.cat_guide.role}</p>
        </div>
      )}

      <div className="panel">
        <h2>Scheme identity</h2>
        <div style={{ overflow: "auto" }}>
          <table className="schema-table">
            <tbody>
              <tr><td>Full name</td><td>{data.full || data.name}</td></tr>
              <tr><td>AMFI scheme code</td><td>{data.code}</td></tr>
              <tr><td>AMC / house</td><td>{data.house}</td></tr>
              <tr><td>SEBI category</td><td>{catLabel(data.cat)}</td></tr>
              <tr><td>Plan</td><td>Direct Growth</td></tr>
              <tr><td>Fund manager</td><td>{data.mgr || "—"}</td></tr>
              <tr><td>Inception</td><td>{data.incept || "—"} ({n(data.yrs, 1)} years)</td></tr>
              <tr><td>Riskometer</td><td>{data.risk || "—"}</td></tr>
              <tr><td>Min SIP</td><td>{data.sip != null ? inr(data.sip) : "—"}</td></tr>
              <tr><td>Exit load</td><td>{data.load || "None listed"}</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <h2>Returns</h2>
        <div className="metric-grid">
          <Metric label="1 year" value={`${n(data.y1)}%`} hint="Trailing point-to-point" />
          <Metric label="3 year CAGR" value={`${n(data.y3)}%`} />
          <Metric label="5 year CAGR" value={`${n(data.y5)}%`} />
          <Metric label="10 year CAGR" value={`${n(data.y10)}%`} hint="Used in base forecast when available" />
          <Metric label="Rolling 3Y median" value={`${n(data.r3)}%`} hint="All 3-year windows" />
          <Metric label="Rolling 3Y worst" value={`${n(data.r3mn)}%`} />
          <Metric label="Rolling 3Y % positive" value={`${n(data.r3p)}%`} />
          <Metric label="Rolling 5Y median" value={`${n(data.r5)}%`} />
          <Metric label="SIP 5Y XIRR" value={`${n(data.sip5)}%`} hint="Monthly SIP on this NAV" />
        </div>
      </div>

      <div className="panel">
        <h2>Risk metrics</h2>
        <div className="metric-grid">
          <Metric label="Volatility (ann.)" value={`${n(data.vol)}%`} hint="Stdev of monthly returns × √12" />
          <Metric label="Max drawdown" value={`${n(data.dd)}%`} hint={data.ddd ? `Trough ${data.ddd}` : "Peak to trough"} />
          <Metric label="Sharpe" value={n(data.sh, 2)} hint="Excess return / vol (Rf 6.5%)" />
          <Metric label="Sortino" value={n(data.so, 2)} hint="Downside-only risk" />
        </div>
      </div>

      <div className="panel">
        <h2>How the fund is allocated</h2>
        <h3>Asset mix</h3>
        <AllocBar label="Equity" pct={data.eq} color="#0f4c5c" />
        <AllocBar label="Debt" pct={data.dt} color="#c17a3a" />
        <AllocBar label="Cash / others" pct={data.cash} color="#6b8f71" />
        <h3>Market-cap split</h3>
        <AllocBar label="Large cap" pct={data.l} color="#0f4c5c" />
        <AllocBar label="Mid cap" pct={data.m} color="#2a6f7a" />
        <AllocBar label="Small cap" pct={data.sml} color="#c17a3a" />
        <p className="muted" style={{ fontSize: 13 }}>
          L/M/S is the current book, not the SEBI label. A “flexi” fund can still be 90%+ large-cap.
        </p>

        {secs.length > 0 && (
          <>
            <h3>Sectors</h3>
            <div className="secbar" style={{ height: 14 }}>
              {secs.map((s, i) => (
                <i
                  key={s.s}
                  style={{ width: `${s.w}%`, background: SECTOR_COLORS[i % SECTOR_COLORS.length] }}
                  title={`${s.s} ${s.w}%`}
                />
              ))}
            </div>
            {secs.map((s, i) => (
              <AllocBar
                key={s.s}
                label={s.s}
                pct={s.w}
                color={SECTOR_COLORS[i % SECTOR_COLORS.length]}
              />
            ))}
          </>
        )}

        {["ai", "ev", "digital", "oil"].some((t) => (themes[t] || 0) > 0) && (
          <>
            <h3>Theme exposure (stock-name match)</h3>
            <AllocBar label="AI / IT" pct={themes.ai} />
            <AllocBar label="EV / auto" pct={themes.ev} />
            <AllocBar label="Digital / platforms" pct={themes.digital} />
            <AllocBar label="Oil / energy" pct={themes.oil} />
            <p className="muted" style={{ fontSize: 13 }}>
              Approximate: names in the book matching our theme lists. A stock can count in more than one theme.
            </p>
          </>
        )}
      </div>

      <div className="panel">
        <h2>Portfolio quality</h2>
        <div className="metric-grid">
          <Metric label="Holdings count" value={data.hold ?? holdings.length} />
          <Metric label="Top 5 weight" value={`${n(data.t5)}%`} />
          <Metric label="Top 10 weight" value={`${n(data.t10)}%`} />
          <Metric label="Portfolio P/E" value={n(data.pe, 1)} />
          <Metric label="Portfolio P/B" value={n(data.pb, 2)} />
          <Metric label="Turnover" value={data.turn != null ? `${n(data.turn)}%` : "—"} hint="How often the book is replaced" />
        </div>
      </div>

      <div className="panel">
        <h2>Holdings ({holdings.length})</h2>
        {holdings.length ? (
          <div style={{ overflow: "auto", maxHeight: 480 }}>
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Stock</th>
                  <th>Sector</th>
                  <th className="num">Weight</th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((h, i) => (
                  <tr key={h.k || h.n}>
                    <td>{i + 1}</td>
                    <td>{h.n}</td>
                    <td>{h.s || "—"}</td>
                    <td className="num">{n(h.w, 2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">Holdings not available for this scheme.</p>
        )}
      </div>

      {navPts.length > 1 && (
        <div className="panel">
          <h2>Month-end NAV ({navPts[0][0].slice(0, 7)} → {navPts[navPts.length - 1][0].slice(0, 7)})</h2>
          <div className="chart nav-spark">
            {navPts.map((p) => {
              const h = Math.max(4, ((p[1] - navMin) / (navMax - navMin || 1)) * 120);
              return (
                <div key={p[0]} className="bar" style={{ height: h }} title={`${p[0]}: ${n(p[1], 2)}`} />
              );
            })}
          </div>
          <p className="muted" style={{ fontSize: 13 }}>
            {navPts.length} month-end points from mfapi.in / AMFI. First {n(navPts[0][1], 2)} · last {n(navPts[navPts.length - 1][1], 2)}.
          </p>
        </div>
      )}

      {data.related?.length > 0 && (
        <div className="panel">
          <h2>Best pairs that include this fund</h2>
          <div style={{ overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Other fund</th>
                  <th>Split</th>
                  <th className="num">Overlap</th>
                  <th className="num">Hist CAGR</th>
                  <th className="num">15Y base</th>
                </tr>
              </thead>
              <tbody>
                {data.related.map((p) => {
                  const otherIsA = String(p.a) !== String(data.code);
                  const oc = otherIsA ? p.a : p.b;
                  const on = otherIsA ? p.an : p.bn;
                  return (
                    <tr
                      key={`${p.a}-${p.b}`}
                      className="clickable"
                      onClick={() => navTo(`/compare?a=${p.a}&b=${p.b}&split=${p.split}`)}
                    >
                      <td>{p.rank}</td>
                      <td><FundLink code={oc}>{on}</FundLink></td>
                      <td>{p.split}/{100 - p.split}</td>
                      <td className="num">{p.ov == null ? "—" : `${n(p.ov, 1)}%`}</td>
                      <td className="num">{n(p.hist_cagr, 1)}%</td>
                      <td className="num">{inr(p.forecast)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p className="note">
        Direct Growth · educational only. Holdings and allocation are a snapshot and change every month.
        Cross-check NAV on AMFI before you invest.
      </p>
    </>
  );
}
