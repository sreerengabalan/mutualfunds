import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import FundDetailCard, { YearTable } from "../components/FundDetailCard";
import FundLink from "../components/FundLink";
import { useFilters } from "../lib/FiltersContext";
import { toQuery } from "../lib/persist";
import { api, catLabel, inr, n, CAT_ORDER } from "../lib/utils";

export default function Compare({ meta, funds }) {
  const [params, setParams] = useSearchParams();
  const { compare, setCompare } = useFilters();
  const [tab, setTab] = useState("base");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const a = params.get("a") || compare.a || String(funds[0]?.code || "");
  const b = params.get("b") || compare.b || String(funds[1]?.code || "");
  const split = params.get("split") || compare.split || "65";
  const histStart = params.get("histStart") || compare.histStart || "2016";
  const catA = params.get("catA") || compare.catA || "";
  const catB = params.get("catB") || compare.catB || "";
  const lump = params.get("lump") || compare.lump || String(meta?.plan?.lump || 300000);
  const sip = params.get("sip") || compare.sip || String(meta?.plan?.sip || 15000);
  const years = params.get("years") || compare.years || String(meta?.plan?.years || 15);

  const fundsA = useMemo(
    () => (catA ? funds.filter((f) => f.cat === catA) : funds),
    [funds, catA]
  );
  const fundsB = useMemo(
    () => (catB ? funds.filter((f) => f.cat === catB) : funds),
    [funds, catB]
  );

  function snapshot(extra = {}) {
    return {
      a, b, split, histStart, catA, catB, lump, sip, years,
      ...extra,
    };
  }

  function patch(obj) {
    const nextState = snapshot(obj);
    const next = toQuery(nextState);
    setParams(next, { replace: true });
    setCompare(nextState);
  }

  useEffect(() => {
    if (!params.get("a") && (compare.a || a)) {
      setParams(toQuery(snapshot()), { replace: true });
    }
    setCompare(snapshot());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [a, b, split, histStart, catA, catB, lump, sip, years]);

  useEffect(() => {
    if (!a || !b) return;
    setLoading(true);
    const qs = new URLSearchParams({ a, b, split, histStart, lump, sip, years });
    api(`/api/compare?${qs}`)
      .then(setResult)
      .catch(() => setResult(null))
      .finally(() => setLoading(false));
  }, [a, b, split, histStart, lump, sip, years]);

  function applyPreset(p) {
    patch({
      catA: p.catA,
      catB: p.catB,
      split: p.split,
      a: p.defaultA,
      b: p.defaultB,
    });
  }

  const ov = result?.overlap;
  const ovCls = !ov ? "mid" : ov.ov >= 40 ? "high" : ov.ov >= 20 ? "mid" : "low";
  const end = result?.yearly?.[tab === "history" ? "history" : tab];
  const last = end?.[end.length - 1];
  const inf = result?.inflation || meta?.inflation;
  const cpi = inf?.long_term_avg || 5.5;
  const maxCpi = inf ? Math.max(...inf.years.map((y) => y.cpi)) : 1;
  const sources = meta?.sources || {};

  return (
    <>
      <section className="hero">
        <h1>Compare two funds · full details</h1>
        <p>
          Change lumpsum, SIP and years. See both factsheets, overlap, 15Y base / bear / bull,
          real history, and what those rupees are worth after India inflation.
        </p>
      </section>

      <div className="panel">
        <h2>Your amounts</h2>
        <div className="controls">
          <div>
            <label>Lumpsum (₹)</label>
            <input type="number" min={0} step={50000} value={lump} onChange={(e) => patch({ lump: e.target.value })} />
          </div>
          <div>
            <label>Monthly SIP (₹)</label>
            <input type="number" min={0} step={1000} value={sip} onChange={(e) => patch({ sip: e.target.value })} />
          </div>
          <div>
            <label>Horizon (years)</label>
            <input type="number" min={5} max={30} step={1} value={years} onChange={(e) => patch({ years: e.target.value })} />
          </div>
          <div>
            <label>Total you will invest</label>
            <div style={{ height: 36, display: "flex", alignItems: "center", fontWeight: 600 }}>
              {inr(Number(lump) + Number(sip) * Number(years) * 12)}
            </div>
          </div>
        </div>
        <p className="muted" style={{ margin: 0 }}>
          Default was ₹3L + ₹15K/month. Change any box — forecast, history and inflation-adjusted value all recalculate.
        </p>
      </div>

      <div className="panel">
        <h2>Pick a combo</h2>
        <div className="presets">
          {(meta?.combo_presets || []).map((p) => (
            <button
              key={p.id}
              type="button"
              className={`preset ${catA === p.catA && catB === p.catB ? "on" : ""}`}
              onClick={() => applyPreset(p)}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div className="controls">
          <div>
            <label>Category A</label>
            <select value={catA} onChange={(e) => {
              const c = e.target.value;
              const list = c ? funds.filter((f) => f.cat === c) : funds;
              patch({ catA: c, a: list[0]?.code || a });
            }}>
              <option value="">All</option>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
            </select>
          </div>
          <div>
            <label>Fund A (core)</label>
            <select value={a} onChange={(e) => patch({ a: e.target.value })}>
              {fundsA.map((f) => (
                <option key={f.code} value={f.code}>{f.name} · 5Y {n(f.y5)}%</option>
              ))}
            </select>
            <div style={{ marginTop: 4, fontSize: 12 }}><FundLink code={a}>Open full scheme →</FundLink></div>
          </div>
          <div>
            <label>Category B</label>
            <select value={catB} onChange={(e) => {
              const c = e.target.value;
              const list = c ? funds.filter((f) => f.cat === c) : funds;
              patch({ catB: c, b: list[0]?.code || b });
            }}>
              <option value="">All</option>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
            </select>
          </div>
          <div>
            <label>Fund B (satellite)</label>
            <select value={b} onChange={(e) => patch({ b: e.target.value })}>
              {fundsB.map((f) => (
                <option key={f.code} value={f.code}>{f.name} · 5Y {n(f.y5)}%</option>
              ))}
            </select>
            <div style={{ marginTop: 4, fontSize: 12 }}><FundLink code={b}>Open full scheme →</FundLink></div>
          </div>
          <div>
            <label>Fund A %</label>
            <input type="number" min={20} max={80} step={5} value={split} onChange={(e) => patch({ split: e.target.value })} />
          </div>
          <div>
            <label>History from</label>
            <select value={histStart} onChange={(e) => patch({ histStart: e.target.value })}>
              <option value="2016">2016 (~10Y)</option>
              <option value="2019">Feb 2019</option>
              <option value="2021">2021</option>
            </select>
          </div>
        </div>
      </div>

      {loading && <p className="muted">Loading comparison…</p>}
      {result && (
        <>
          <div className="panel">
            <h2>Full fund details</h2>
            <p className="muted">Click a fund name for the complete scheme page (allocation, every holding, NAV history).</p>
            <div className="fcards">
              <FundDetailCard fund={result.a} pct={+split} role="Core" />
              <FundDetailCard fund={result.b} pct={100 - +split} role="Satellite" />
            </div>
          </div>

          <div className="panel">
            <h2>Overlap & scenarios</h2>
            <div className={`ov ${ovCls}`}>
              <b className="big">{ov ? `${n(ov.ov, 1)}%` : "—"}</b>
              <div>
                {ov
                  ? `${ov.common.length} common stocks (of ${ov.na} and ${ov.nb} holdings)`
                  : "Holdings unavailable"}
              </div>
              <div className="muted" style={{ marginTop: 6 }}>
                {ov?.ov >= 40
                  ? "High overlap — pairing adds little diversification."
                  : ov?.ov >= 20
                  ? "Moderate overlap — fine as satellite, not two cores."
                  : "Low overlap — reasonably different books."}
              </div>
            </div>
            {ov?.common?.length > 0 && (
              <div style={{ overflow: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Common stock</th>
                      <th className="num">{result.a.name.slice(0, 28)}</th>
                      <th className="num">{result.b.name.slice(0, 28)}</th>
                      <th className="num">Min wt</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ov.common.slice(0, 15).map((r) => (
                      <tr key={r.n}>
                        <td>{r.n}</td>
                        <td className="num">{n(r.a, 2)}%</td>
                        <td className="num">{n(r.b, 2)}%</td>
                        <td className="num">{n(r.m, 2)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="scenarios">
              <div className="scenario bear">
                <b>{inr(result.yearly.bear.at(-1)?.value)}</b>
                <span>Bear · {n(result.cagr.bear)}% · today {inr(result.yearly.bear.at(-1)?.real)}</span>
              </div>
              <div className="scenario">
                <b>{inr(result.yearly.base.at(-1)?.value)}</b>
                <span>Base · {n(result.cagr.base)}% · today {inr(result.yearly.base.at(-1)?.real)}</span>
              </div>
              <div className="scenario bull">
                <b>{inr(result.yearly.bull.at(-1)?.value)}</b>
                <span>Bull · {n(result.cagr.bull)}% · today {inr(result.yearly.bull.at(-1)?.real)}</span>
              </div>
            </div>
            {last && (
              <p className="muted">
                You invest <b>{inr(result.amounts?.invested)}</b>. Selected path ends at <b>{inr(last.value)}</b>
                ({last.ret}% on capital). After ~{cpi}% inflation that is about <b>{inr(last.real)}</b> in today’s rupees.
                Real CAGR ≈ {n(result.cagr.real_base)}%.
              </p>
            )}
          </div>

          <div className="panel">
            <h2>Year-by-year</h2>
            <div className="tabs">
              {[
                ["base", "Base forecast"],
                ["bear", "Bear forecast"],
                ["bull", "Bull forecast"],
                ["history", "Actual history"],
              ].map(([k, label]) => (
                <button key={k} type="button" className={`tab ${tab === k ? "on" : ""}`} onClick={() => setTab(k)}>
                  {label}
                </button>
              ))}
            </div>
            <YearTable
              showReal
              rows={tab === "history" ? result.yearly.history : result.yearly[tab]}
              title={
                tab === "history"
                  ? `Actual history from ${histStart} (real NAV) · ${inr(Number(lump))} + ${inr(Number(sip))}/mo`
                  : `${tab[0].toUpperCase()}${tab.slice(1)} forecast (~${n(result.cagr[tab])}%) · ${inr(Number(lump))} + ${inr(Number(sip))}/mo`
              }
            />
          </div>
        </>
      )}

      {inf && (
        <div className="panel" id="inflation">
          <h2>India inflation (with this plan)</h2>
          <p className="muted">{inf.note} Planning average: <b>~{cpi}% / year</b>.</p>
          <div className="inf-chart">
            {inf.years.map((y) => (
              <div
                key={y.y}
                className="inf-bar"
                style={{ height: Math.max(8, (y.cpi / maxCpi) * 120) }}
                title={`${y.y}: ${y.cpi}%`}
              >
                <em>{y.cpi}%</em>
                <span>{y.y}</span>
              </div>
            ))}
          </div>
          <div style={{ height: 36 }} />
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th className="num">CPI YoY avg %</th>
                <th>₹100 buying power next year</th>
              </tr>
            </thead>
            <tbody>
              {inf.years.map((y) => (
                <tr key={y.y}>
                  <td>{y.y}</td>
                  <td className="num">{n(y.cpi, 1)}%</td>
                  <td>₹{n(100 / (1 + y.cpi / 100), 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {last && (
            <div className="warnbox" style={{ marginTop: 16 }}>
              <b>On your amounts:</b> {inr(last.value)} in {years} years at {cpi}% inflation
              is about <b>{inr(last.real)}</b> in today’s money.
              Nominal base ~{n(result?.cagr?.base)}% minus {cpi}% ≈ <b>{n(result?.cagr?.real_base)}% real</b>.
            </div>
          )}
        </div>
      )}

      <div className="panel">
        <h2>Is this historical data valid? Where to verify</h2>
        <p className="muted">
          History is <b>real published NAVs</b>, not a simulation. Forecasts are a planning model (past CAGR ± 2–4%).
          Always cross-check a fund on AMFI before you invest.
        </p>
        <table>
          <thead>
            <tr>
              <th>What we show</th>
              <th>Source</th>
              <th>How you verify</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Daily / month-end NAV, 10Y history</td>
              <td>{sources.nav?.name || "mfapi.in"} (AMFI feed)</td>
              <td>
                <a href={sources.verify_nav || "https://www.amfiindia.com/net-asset-value/nav-history"} target="_blank" rel="noreferrer">
                  AMFI NAV history
                </a>
                {" · "}
                <a href="https://api.mfapi.in/" target="_blank" rel="noreferrer">mfapi.in</a>
              </td>
            </tr>
            <tr>
              <td>Scheme code, category, latest NAV</td>
              <td>{sources.universe?.name || "AMFI NAVAll.txt"}</td>
              <td>
                <a href={sources.universe?.url || "https://www.amfiindia.com/spages/NAVAll.txt"} target="_blank" rel="noreferrer">
                  AMFI NAVAll.txt
                </a>
              </td>
            </tr>
            <tr>
              <td>Holdings / overlap / AUM / TER</td>
              <td>{sources.holdings?.name || "Groww"}</td>
              <td>
                AMC factsheet,{" "}
                <a href="https://www.valueresearchonline.com/" target="_blank" rel="noreferrer">Value Research</a>,{" "}
                <a href="https://www.morningstar.in/" target="_blank" rel="noreferrer">Morningstar</a>
              </td>
            </tr>
            <tr>
              <td>India inflation %</td>
              <td>MoSPI CPI (planning averages)</td>
              <td>
                <a href="https://www.mospi.gov.in/" target="_blank" rel="noreferrer">MoSPI</a>
                {" · "}
                <a href="https://www.rbi.org.in/" target="_blank" rel="noreferrer">RBI</a>
              </td>
            </tr>
          </tbody>
        </table>
        <p className="note">
          Valid for education: yes — NAV history matches AMFI. Not a guarantee of future returns.
          Month-end NAVs can differ by a few paise from a daily chart. Holdings are a snapshot and change every month.
        </p>
      </div>
    </>
  );
}
