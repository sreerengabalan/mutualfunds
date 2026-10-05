import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FundLink from "../components/FundLink";
import { useFilters } from "../lib/FiltersContext";
import { hrefFor } from "../lib/persist";
import { api, catLabel, inr, n, CAT_ORDER } from "../lib/utils";

export default function Home({ meta }) {
  const nav = useNavigate();
  const { pairs: filters, setPairs, compare } = useFilters();
  const [data, setData] = useState({ total: 0, pairs: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== ""))
    );
    setLoading(true);
    api(`/api/pairs?${qs}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [filters]);

  function set(k, v) {
    setPairs({ [k]: v });
  }

  function openCompare(p) {
    const next = {
      ...compare,
      a: String(p.a),
      b: String(p.b),
      split: String(p.split),
      catA: p.ac || compare.catA,
      catB: p.bc || compare.catB,
      lump: compare.lump || String(meta?.plan?.lump || 300000),
      sip: compare.sip || String(meta?.plan?.sip || 15000),
      years: compare.years || String(meta?.plan?.years || 15),
    };
    nav(hrefFor("/compare", next));
  }

  return (
    <>
      <section className="hero">
        <h1>Best two-fund combinations</h1>
        <p>
          All {meta?.n_pairs?.toLocaleString("en-IN") || "1,225"} pairs from {meta?.n_funds || 50} Direct Growth equity funds —
          ranked on ~10Y live NAV history, fit score, overlap, and 15Y base-case forecast (₹3L + ₹15K SIP).
          Pick any row to open full fund details and year-by-year plan.
        </p>
        <div className="stats">
          <div className="stat"><b>{meta?.n_pairs || "—"}</b><span>Pairs scored</span></div>
          <div className="stat"><b>{meta?.n_funds || "—"}</b><span>Funds in universe</span></div>
          <div className="stat"><b>{inr(meta?.plan?.lump)}</b><span>Default lumpsum</span></div>
          <div className="stat"><b>{inr(meta?.plan?.sip)}/mo</b><span>Default SIP · {meta?.plan?.years || 15}Y</span></div>
        </div>
      </section>

      <div className="panel">
        <h2>Filter & rank</h2>
        <div className="controls">
          <div>
            <label>Category A</label>
            <select value={filters.catA} onChange={(e) => set("catA", e.target.value)}>
              <option value="">Any</option>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
            </select>
          </div>
          <div>
            <label>Category B</label>
            <select value={filters.catB} onChange={(e) => set("catB", e.target.value)}>
              <option value="">Any</option>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
            </select>
          </div>
          <div>
            <label>Max overlap %</label>
            <select value={filters.maxOv} onChange={(e) => set("maxOv", e.target.value)}>
              <option value="20">≤ 20%</option>
              <option value="30">≤ 30%</option>
              <option value="40">≤ 40%</option>
              <option value="100">Any</option>
            </select>
          </div>
          <div>
            <label>Sort by</label>
            <select value={filters.sort} onChange={(e) => set("sort", e.target.value)}>
              <option value="score">Best overall score</option>
              <option value="forecast">Highest 15Y forecast</option>
              <option value="hist">Highest history CAGR</option>
              <option value="ov">Lowest overlap</option>
            </select>
          </div>
          <div>
            <label>Different categories only</label>
            <select value={filters.differentCats} onChange={(e) => set("differentCats", e.target.value)}>
              <option value="1">Yes</option>
              <option value="0">No</option>
            </select>
          </div>
          <div>
            <label>Search fund / AMC</label>
            <input value={filters.q} onChange={(e) => set("q", e.target.value)} placeholder="e.g. PPFAS, Nippon" />
          </div>
        </div>
        <p className="muted">{loading ? "Loading…" : `${data.total} pairs match · showing top ${data.pairs.length}`}</p>
        <div style={{ overflow: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Pair</th>
                <th>Split</th>
                <th className="num">Overlap</th>
                <th className="num">Hist CAGR</th>
                <th className="num">Hist value</th>
                <th className="num">15Y base</th>
                <th className="num">Score</th>
              </tr>
            </thead>
            <tbody>
              {data.pairs.map((p) => (
                <tr
                  key={`${p.a}-${p.b}`}
                  className="clickable"
                  onClick={() => openCompare(p)}
                >
                  <td>{p.rank}</td>
                  <td>
                    <FundLink code={p.a}><b>{p.an}</b></FundLink>
                    <div className="muted" style={{ fontSize: 12 }}>{catLabel(p.ac)} · {p.ah}</div>
                    <FundLink code={p.b}><b>{p.bn}</b></FundLink>
                    <div className="muted" style={{ fontSize: 12 }}>{catLabel(p.bc)} · {p.bh}</div>
                  </td>
                  <td>{p.split}/{100 - p.split}</td>
                  <td className="num">
                    <span className={`tag ${p.ov >= 40 ? "bad" : p.ov >= 20 ? "warn" : "ok"}`}>
                      {p.ov == null ? "n/a" : `${n(p.ov, 1)}%`}
                    </span>
                  </td>
                  <td className="num">{n(p.hist?.cagr, 1)}%</td>
                  <td className="num">{inr(p.hist?.value)}</td>
                  <td className="num"><b>{inr(p.forecast?.value)}</b></td>
                  <td className="num">{n(p.score, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="note">
          History uses actual month-end NAV from ~2016 (or later inception). Forecast is educational — past returns do not guarantee future results.
          Click a <b>fund name</b> for its full scheme page. Click the rest of the row to open the pair in Compare.
        </p>
      </div>
    </>
  );
}
