import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FundLink from "../components/FundLink";
import { useFilters } from "../lib/FiltersContext";
import { catLabel, n, CAT_ORDER } from "../lib/utils";

export default function Funds({ funds }) {
  const nav = useNavigate();
  const { funds: filters, setFunds } = useFilters();
  const cat = filters.cat || "";
  const q = filters.q || "";
  const sort = filters.sort || "aum";

  const rows = useMemo(() => {
    let list = funds;
    if (cat) list = list.filter((f) => f.cat === cat);
    const s = q.trim().toLowerCase();
    if (s) {
      list = list.filter(
        (f) =>
          f.name.toLowerCase().includes(s) ||
          f.house.toLowerCase().includes(s) ||
          String(f.code).includes(s) ||
          (f.mgr || "").toLowerCase().includes(s)
      );
    }
    list = [...list].sort((a, b) => {
      if (sort === "y5") return (b.y5 || 0) - (a.y5 || 0);
      if (sort === "y10") return (b.y10 || 0) - (a.y10 || 0);
      if (sort === "name") return a.name.localeCompare(b.name);
      return (b.aum || 0) - (a.aum || 0);
    });
    return list;
  }, [funds, cat, q, sort]);

  return (
    <>
      <section className="hero">
        <h1>All {funds.length} funds</h1>
        <p>Click any name for the full scheme page — allocation, holdings, risk, NAV history, and pairs.</p>
      </section>
      <div className="panel">
        <div className="controls">
          <div>
            <label>Category</label>
            <select value={cat} onChange={(e) => setFunds({ cat: e.target.value })}>
              <option value="">All</option>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{catLabel(c)}</option>)}
            </select>
          </div>
          <div>
            <label>Search</label>
            <input value={q} onChange={(e) => setFunds({ q: e.target.value })} placeholder="Name, AMC, code, manager" />
          </div>
          <div>
            <label>Sort</label>
            <select value={sort} onChange={(e) => setFunds({ sort: e.target.value })}>
              <option value="aum">Largest AUM</option>
              <option value="y5">Best 5Y</option>
              <option value="y10">Best 10Y</option>
              <option value="name">Name</option>
            </select>
          </div>
        </div>
        <p className="muted">{rows.length} funds</p>
        <div style={{ overflow: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Fund</th>
                <th>Category</th>
                <th className="num">AUM Cr</th>
                <th className="num">TER</th>
                <th className="num">5Y</th>
                <th className="num">10Y</th>
                <th className="num">Vol</th>
                <th className="num">Max DD</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((f) => (
                <tr key={f.code} className="clickable" onClick={() => nav(`/fund/${f.code}`)}>
                  <td>
                    <FundLink code={f.code}><b>{f.name}</b></FundLink>
                    <div className="muted" style={{ fontSize: 12 }}>{f.house} · {f.code}</div>
                  </td>
                  <td>{catLabel(f.cat)}</td>
                  <td className="num">{n(f.aum, 0)}</td>
                  <td className="num">{n(f.ter, 2)}%</td>
                  <td className="num">{n(f.y5)}%</td>
                  <td className="num">{n(f.y10)}%</td>
                  <td className="num">{n(f.vol)}%</td>
                  <td className="num">{n(f.dd)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
