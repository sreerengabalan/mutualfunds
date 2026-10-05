import FundLink from "./FundLink";
import { catLabel, inr, n, SECTOR_COLORS } from "../lib/utils";

export default function FundDetailCard({ fund, pct, role }) {
  if (!fund) return null;
  const secs = fund.sec || [];
  const holds = (fund.holdings || []).slice(0, 12);
  const themes = fund.themes || {};

  return (
    <div className="fcard">
      <div className="muted" style={{ fontSize: 12 }}>{role || "Fund"} · {pct != null ? `${pct}%` : ""}</div>
      <h3><FundLink code={fund.code}>{fund.name}</FundLink></h3>
      <div className="muted" style={{ fontSize: 13 }}>
        {fund.house} · {catLabel(fund.cat)} · Manager: {fund.mgr || "—"}
      </div>
      <div className="kpi">
        <span>NAV {n(fund.nav, 2)}</span>
        <span>AUM ₹{n(fund.aum, 0)} Cr</span>
        <span>TER {n(fund.ter, 2)}%</span>
        <span>Age {n(fund.yrs, 1)}Y</span>
        <span>{fund.risk || "—"} risk</span>
      </div>
      <div className="kpi">
        <span>1Y {n(fund.y1)}%</span>
        <span>3Y {n(fund.y3)}%</span>
        <span>5Y {n(fund.y5)}%</span>
        <span>10Y {n(fund.y10)}%</span>
        <span>Roll 3Y {n(fund.r3)}%</span>
      </div>
      <div className="kpi">
        <span>Vol {n(fund.vol)}%</span>
        <span>Max DD {n(fund.dd)}%</span>
        <span>Sharpe {n(fund.sh, 2)}</span>
        <span>L/M/S {n(fund.l, 0)}/{n(fund.m, 0)}/{n(fund.sml, 0)}</span>
        <span>P/E {n(fund.pe, 1)}</span>
      </div>
      {["ai", "ev", "digital", "oil"].some((t) => (themes[t] || 0) > 2) && (
        <div className="kpi">
          {["ai", "ev", "digital", "oil"].filter((t) => (themes[t] || 0) > 2).map((t) => (
            <span key={t}>{t.toUpperCase()} {n(themes[t], 1)}%</span>
          ))}
        </div>
      )}
      {secs.length > 0 && (
        <>
          <h3 style={{ fontSize: "1rem" }}>Sectors</h3>
          <div className="secbar">
            {secs.slice(0, 6).map((s, i) => (
              <i key={s.s} style={{ width: `${s.w}%`, background: SECTOR_COLORS[i % SECTOR_COLORS.length] }} title={`${s.s} ${s.w}%`} />
            ))}
          </div>
          <div className="muted" style={{ fontSize: 12 }}>
            {secs.slice(0, 5).map((s) => `${s.s} ${n(s.w, 1)}%`).join(" · ")}
          </div>
        </>
      )}
      {holds.length > 0 && (
        <>
          <h3 style={{ fontSize: "1rem" }}>Top holdings</h3>
          <div className="holdlist">
            {holds.map((h) => (
              <div key={h.k || h.n}>
                <span>{h.n}</span>
                <span className="num">{n(h.w, 2)}%</span>
              </div>
            ))}
          </div>
        </>
      )}
      {fund.load && <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>{fund.load}</p>}
    </div>
  );
}

export function YearTable({ rows, title, showReal = false }) {
  if (!rows?.length) return <p className="muted">Not enough NAV history for this window.</p>;
  const maxV = Math.max(...rows.map((r) => r.value));
  return (
    <>
      <h3>{title}</h3>
      <div className="chart">
        {rows.map((r) => (
          <div key={r.y} className="bar" style={{ height: Math.max(4, (r.value / maxV) * 100) }} title={`${r.y}: ${inr(r.value)}`}>
            <span>{String(r.y).slice(2)}</span>
          </div>
        ))}
      </div>
      <div style={{ overflow: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th className="num">Added</th>
              <th className="num">Invested</th>
              <th className="num">Value</th>
              <th className="num">Profit</th>
              {showReal && <th className="num">Today’s ₹ (after inflation)</th>}
              <th className="num">Return</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.y}>
                <td>{r.y}</td>
                <td className="num">{inr(r.added)}</td>
                <td className="num">{inr(r.invested)}</td>
                <td className="num">{inr(r.value)}</td>
                <td className="num">{inr(r.profit)}</td>
                {showReal && <td className="num">{r.real != null ? inr(r.real) : "—"}</td>}
                <td className="num">{r.ret}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
