"""Generate combo_2019.html and risk_forecast.html from combo_risk.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "archive" / "html"
DATA = json.loads((ROOT / "output" / "equity" / "combo_risk.json").read_text(encoding="utf-8"))

CSS = r"""
    :root {
      --bg: #f6f5f1; --ink: #1c1b18; --muted: #5c5a54; --line: #ddd9d0;
      --card: #ffffff; --accent: #1f4e79; --accent-soft: #e8eef4;
      --ok: #1f6b4a; --ok-bg: #e8f3ec; --warn: #8a5a12; --warn-bg: #f7eedc;
      --bad: #8b2e2e; --bad-bg: #f6e6e4; --chip: #efece4;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font: 14px/1.45 "Segoe UI", system-ui, sans-serif; color: var(--ink); background: var(--bg); }
    header { background: var(--card); border-bottom: 1px solid var(--line); padding: 20px 24px 16px; }
    h1 { font-size: 22px; font-weight: 650; margin: 0 0 4px; }
    h2 { font-size: 16px; margin: 0 0 10px; }
    h3 { font-size: 14px; margin: 16px 0 8px; }
    .sub { color: var(--muted); margin: 0; }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 16px 20px 48px; }
    .navlinks { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0; }
    .navlinks a {
      border: 1px solid var(--line); background: var(--card); color: var(--ink);
      padding: 6px 12px; border-radius: 999px; text-decoration: none; font-size: 13px;
    }
    .navlinks a.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .chip {
      border: 1px solid var(--line); background: var(--card); color: var(--ink);
      padding: 6px 12px; border-radius: 999px; cursor: pointer; font: inherit;
    }
    .chip.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 12px; }
    .controls { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 12px; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    input, select {
      width: 100%; height: 34px; border: 1px solid var(--line);
      background: var(--card); color: var(--ink); padding: 0 10px; font: inherit;
    }
    .panel { background: var(--card); border: 1px solid var(--line); padding: 14px; margin-top: 16px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); vertical-align: middle; }
    th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }
    td.num, th.num { text-align: right; white-space: nowrap; }
    tr:hover td { background: #f3f1ea; }
    tr.sel td { background: var(--accent-soft); }
    .muted { color: var(--muted); }
    .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    .stat { background: var(--bg); border: 1px solid var(--line); padding: 10px; }
    .stat b { display: block; font-size: 18px; }
    .stat span { font-size: 11px; color: var(--muted); }
    .note { background: #eef3e8; border: 1px solid #d3ddc8; padding: 10px 12px; color: #3d4a36; font-size: 13px; margin-top: 14px; }
    .warnbox { background: var(--warn-bg); border: 1px solid #e4d3ae; padding: 10px 12px; color: #5c4a20; font-size: 13px; margin-top: 14px; }
    .ov { padding: 12px 14px; border: 1px solid var(--line); margin: 10px 0; }
    .ov.low { background: var(--ok-bg); } .ov.mid { background: var(--warn-bg); } .ov.high { background: var(--bad-bg); }
    .ovpill { display: inline-block; font-size: 11px; font-weight: 650; padding: 2px 7px; border-radius: 999px; }
    .ovpill.low { background: var(--ok-bg); color: var(--ok); }
    .ovpill.mid { background: var(--warn-bg); color: var(--warn); }
    .ovpill.high { background: var(--bad-bg); color: var(--bad); }
    .bar-row { display: grid; grid-template-columns: 78px 1fr 44px; gap: 8px; align-items: center; margin: 4px 0; font-size: 12px; }
    .track { height: 10px; background: var(--chip); overflow: hidden; }
    .fill { height: 100%; background: var(--accent); }
    .fill.ev { background: #c4a35a; } .fill.dig { background: #5b7c99; } .fill.oil { background: #7a8b73; }
    .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .card { border: 1px solid var(--line); padding: 12px; background: var(--bg); }
    .catgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .check { display: flex; align-items: center; gap: 8px; height: 34px; margin-top: 18px; font-size: 13px; }
    .check input { width: auto; height: auto; }
    button.link { background: none; border: 0; color: var(--accent); cursor: pointer; font: inherit; text-align: left; padding: 0; }
    @media (max-width: 980px) {
      .controls, .stats, .cards { grid-template-columns: 1fr 1fr; }
    }
"""

NAV = """
      <div class="navlinks">
        <a href="fund_explorer.html"{ex}>Fund explorer</a>
        <a href="combo_2019.html"{co}>2019 two-fund combos</a>
        <a href="risk_forecast.html"{rk}>Risk &amp; 10-year forecast</a>
        <a href="investment_plan.html">15Y detailed plan</a>
      </div>
"""


COMBO = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Two-fund combinations from Feb 2019</title>
  <style>__CSS__</style>
</head>
<body>
  <header>
    <div class="wrap" style="padding-top:0;padding-bottom:0">
      <h1>Best two-fund combinations · Feb 2019 to today</h1>
      <p class="sub">Every pair from the 50-fund list that has NAV from Feb 2019. Default is a core-style filter: different categories, overlap under 30%, not two small-cap funds. Search any fund to jump to that pair.</p>
      __NAV__
      <div class="controls" style="margin-top:14px">
        <div>
          <label for="q">Search a fund in the pair</label>
          <input id="q" placeholder="e.g. HDFC Flexi, Nippon Small, PPFAS" />
        </div>
        <div>
          <label for="start">Start date</label>
          <input id="start" type="date" min="2019-02-01" max="2026-08-11" value="2019-02-01" />
        </div>
        <div>
          <label for="lump">Lumpsum (₹)</label>
          <input id="lump" type="number" min="0" step="10000" value="300000" />
        </div>
        <div>
          <label for="sip">Monthly SIP (₹)</label>
          <input id="sip" type="number" min="0" step="1000" value="10000" />
        </div>
        <div>
          <label for="split">Split to fund A (%)</label>
          <input id="split" type="number" min="10" max="90" step="5" value="50" />
        </div>
        <div>
          <label for="ovmax">Max stock overlap %</label>
          <input id="ovmax" type="number" min="5" max="80" step="5" value="30" />
        </div>
        <div>
          <label for="sort">Sort pairs by</label>
          <select id="sort">
            <option value="cagr">CAGR</option>
            <option value="sh">Sharpe</option>
            <option value="abs">Absolute return</option>
            <option value="calmar">CAGR / |drawdown|</option>
            <option value="ov">Lowest overlap</option>
          </select>
        </div>
        <div>
          <label for="look">Look up fund A</label>
          <select id="look"></select>
        </div>
        <div>
          <label for="look2">Look up fund B</label>
          <select id="look2"></select>
        </div>
        <div class="check"><input id="diffcat" type="checkbox" checked /> Different categories</div>
        <div class="check"><input id="nosmall" type="checkbox" checked /> Not two small-cap funds</div>
        <div class="check"><input id="core" type="checkbox" checked /> At least one flexi / large / multi</div>
        <div>
          <label for="exempt">LTCG exemption</label>
          <select id="exempt">
            <option value="125000">Use ₹1.25 lakh on this withdrawal</option>
            <option value="0">Already used this year</option>
          </select>
        </div>
        <div>
          <label for="surch">Surcharge</label>
          <select id="surch">
            <option value="0">None</option>
            <option value="0.10">10%</option>
            <option value="0.15">15% cap (111A / 112A)</option>
          </select>
        </div>
      </div>
    </div>
  </header>
  <div class="wrap">
    <div class="warnbox">2019–2024 was a strong mid/small-cap run. The raw highest-return pairs are often two aggressive funds with high correlation. That is history, not a 10–20 year plan. Use the filters, then check overlap and drawdown before you copy a pair.</div>
    <div class="panel">
      <h2 id="count">Pairs</h2>
      <p class="muted">Click a row for the combined path. 40 of 50 funds existed in Feb 2019; newer funds appear if you move the start date forward.</p>
      <div style="overflow:auto">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Fund A</th>
              <th>Fund B</th>
              <th>Categories</th>
              <th class="num">Overlap</th>
              <th class="num">Value</th>
              <th class="num">After tax</th>
              <th class="num">CAGR</th>
              <th class="num">Sharpe</th>
              <th class="num">Max DD</th>
              <th class="num">Corr</th>
            </tr>
          </thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
    <div class="panel" id="detail"></div>
    <p class="note">Buy-and-hold split on month-end NAVs. Direct Growth tax is the same as Regular: STCG 20% on units held 12 months or less, LTCG 12.5% after ₹1.25 lakh, plus 4% cess. SIP lots in the last year are short-term. Not a recommendation.</p>
  </div>
  <script src="desk_common.js"></script>
  <script>
    const DATA = __DATA__;
    const FUNDS = DATA.funds;
    const NAV = DATA.nav;
    const CAT = {
      large_cap: "Large", mid_cap: "Mid", small_cap: "Small",
      multi_cap: "Multi", flexi_cap: "Flexi", large_mid_cap: "L&Mid",
    };
    const CORE = new Set(["flexi_cap","large_cap","multi_cap","large_mid_cap"]);
    const $ = (id) => document.getElementById(id);
    const n = (v, d=2) => (v == null || Number.isNaN(v) ? "—" : Number(v).toFixed(d));
    const inr = (v) => v == null ? "—" : "₹" + Math.round(v).toLocaleString("en-IN");
    const pct = (v, d=1) => v == null ? "—" : (v * 100).toFixed(d) + "%";
    const fund = (c) => FUNDS.find(f => f.code === c);
    const ovCls = (v) => v >= 40 ? "high" : v >= 20 ? "mid" : "low";
    let picked = null, cache = [];

    function series(code, start) {
      return (NAV[String(code)] || []).filter(p => p[0] >= start);
    }
    function years(a, b) { return (new Date(b) - new Date(a)) / (365.25 * 864e5); }
    function overlap(a, b) {
      const ha = (fund(a)?._h) || [], hb = (fund(b)?._h) || [];
      if (!ha.length || !hb.length) return null;
      const wa = {}, wb = {};
      ha.forEach(h => wa[h.k] = (wa[h.k] || 0) + h.w);
      hb.forEach(h => wb[h.k] = (wb[h.k] || 0) + h.w);
      let ov = 0;
      Object.keys(wa).forEach(k => { if (wb[k] != null) ov += Math.min(wa[k], wb[k]); });
      return ov;
    }
    function simPair(ca, cb, start, lump, sip, split) {
      const sa = series(ca, start), sb = series(cb, start);
      const da = {}, db = {};
      sa.forEach(p => da[p[0]] = p[1]);
      sb.forEach(p => db[p[0]] = p[1]);
      const dates = Object.keys(da).filter(d => db[d] != null).sort();
      if (dates.length < 24) return null;
      const va = dates.map(d => da[d]), vb = dates.map(d => db[d]);
      let ua = lump * split / va[0], ub = lump * (1 - split) / vb[0], invested = lump;
      const path = [];
      for (let i = 0; i < dates.length; i++) {
        if (sip > 0) { ua += sip * split / va[i]; ub += sip * (1 - split) / vb[i]; invested += sip; }
        path.push(ua * va[i] + ub * vb[i]);
      }
      const rets = [];
      for (let i = 1; i < path.length; i++) rets.push(path[i] / path[i-1] - 1);
      const ra = [], rb = [];
      for (let i = 1; i < va.length; i++) { ra.push(va[i]/va[i-1]-1); rb.push(vb[i]/vb[i-1]-1); }
      let peak = path[0], dd = 0, sum = 0;
      path.forEach(v => { if (v > peak) peak = v; dd = Math.min(dd, v / peak - 1); });
      rets.forEach(r => { sum += r; });
      const m = sum / rets.length;
      const variance = rets.reduce((s, r) => s + (r - m) * (r - m), 0) / (rets.length - 1);
      const volA = Math.sqrt(variance) * Math.sqrt(12);
      const yrs = years(dates[0], dates[dates.length - 1]);
      const fv = path[path.length - 1];
      const meanA = m * 12;
      let corr = null;
      if (ra.length > 2) {
        const ma = ra.reduce((s,x)=>s+x,0)/ra.length, mb = rb.reduce((s,x)=>s+x,0)/rb.length;
        let num = 0, da2 = 0, db2 = 0;
        for (let i = 0; i < ra.length; i++) {
          const xa = ra[i]-ma, xb = rb[i]-mb;
          num += xa*xb; da2 += xa*xa; db2 += xb*xb;
        }
        corr = num / Math.sqrt(da2 * db2);
      }
      return {
        start: dates[0], end: dates[dates.length-1], yrs, invested, value: fv,
        gain: fv - invested, abs: fv / invested - 1,
        cagr: Math.pow(fv / invested, 1 / yrs) - 1,
        vol: volA, dd, sh: volA > 0 ? (meanA - 0.065) / volA : null, corr,
      };
    }

    function eligible(start) {
      return FUNDS.filter(f => series(f.code, start).length >= 24);
    }

    function rank() {
      const start = $("start").value || "2019-02-01";
      const lump = Number($("lump").value || 0);
      const sip = Number($("sip").value || 0);
      const split = Math.min(90, Math.max(10, Number($("split").value || 50))) / 100;
      const ovmax = Number($("ovmax").value || 30);
      const q = $("q").value.trim().toLowerCase();
      const diff = $("diffcat").checked;
      const nosmall = $("nosmall").checked;
      const core = $("core").checked;
      const sort = $("sort").value;
      const look = Number($("look").value || 0);
      const look2 = Number($("look2").value || 0);
      const fs = eligible(start);
      const rows = [];
      for (let i = 0; i < fs.length; i++) {
        for (let j = i + 1; j < fs.length; j++) {
          const a = fs[i], b = fs[j];
          const looked = look && look2 && ((a.code===look && b.code===look2) || (a.code===look2 && b.code===look));
          if (look && look2 && !looked) continue;
          if (!looked) {
            if (diff && a.cat === b.cat) continue;
            if (nosmall && a.cat === "small_cap" && b.cat === "small_cap") continue;
            if (core && !CORE.has(a.cat) && !CORE.has(b.cat)) continue;
            const ov0 = a._ov && a._ov[b.code] != null ? a._ov[b.code] : null;
            if (ov0 != null && ov0 > ovmax) continue;
            if (q && !(`${a.name} ${a.house} ${b.name} ${b.house}`.toLowerCase().includes(q))) continue;
            if (look && a.code !== look && b.code !== look) continue;
          }
          const ov = a._ov && a._ov[b.code] != null ? a._ov[b.code] : null;
          const st = simPair(a.code, b.code, start, lump, sip, split);
          if (!st) continue;
          st.calmar = st.dd < 0 ? st.cagr / Math.abs(st.dd) : st.cagr;
          const lots = MFDesk.lots(series(a.code, start), lump * split, sip * split)
            .concat(MFDesk.lots(series(b.code, start), lump * (1 - split), sip * (1 - split)));
          st.tax = MFDesk.tax(lots);
          rows.push({ a, b, ov, ...st });
        }
      }
      const dir = sort === "ov" ? 1 : -1;
      rows.sort((x, y) => {
        const av = x[sort] == null ? -1e9 * dir : x[sort];
        const bv = y[sort] == null ? -1e9 * dir : y[sort];
        return (av - bv) * dir;
      });
      cache = rows;
      return rows;
    }

    function renderTable() {
      const rows = rank().slice(0, 40);
      $("count").textContent = cache.length + " pairs match · showing " + rows.length;
      $("tbody").innerHTML = rows.map((r, i) => `
        <tr data-i="${i}" class="${picked===i?"sel":""}">
          <td>${i+1}</td>
          <td><button class="link">${r.a.name}</button><div class="muted">${r.a.house}</div></td>
          <td><button class="link">${r.b.name}</button><div class="muted">${r.b.house}</div></td>
          <td>${CAT[r.a.cat]} + ${CAT[r.b.cat]}</td>
          <td class="num">${r.ov==null?"—":`<span class="ovpill ${ovCls(r.ov)}">${n(r.ov,0)}%</span>`}</td>
          <td class="num">${inr(r.value)}</td>
          <td class="num">${r.tax ? inr(r.tax.net) : "—"}</td>
          <td class="num">${pct(r.cagr)}</td>
          <td class="num">${n(r.sh,2)}</td>
          <td class="num">${pct(r.dd)}</td>
          <td class="num">${n(r.corr,2)}</td>
        </tr>`).join("");
      if (rows[0]) renderDetail(rows[0], 0);
    }

    function renderDetail(r, i) {
      picked = i;
      const split = Math.round(Number($("split").value || 50));
      $("detail").innerHTML = `
        <h2>${r.a.name} + ${r.b.name}</h2>
        <p class="muted">${r.start} to ${r.end} · ${n(r.yrs,1)} years · ${split}/${100-split} split</p>
        <div class="stats">
          <div class="stat"><b>${inr(r.value)}</b><span>Combined value</span></div>
          <div class="stat"><b>${inr(r.invested)}</b><span>Invested</span></div>
          <div class="stat"><b>${inr(r.gain)}</b><span>Profit</span></div>
          <div class="stat"><b>${pct(r.cagr)}</b><span>CAGR</span></div>
          <div class="stat"><b>${n(r.sh,2)}</b><span>Sharpe (monthly, rf 6.5%)</span></div>
          <div class="stat"><b>${pct(r.dd)}</b><span>Max drawdown on the pair</span></div>
          <div class="stat"><b>${pct(r.vol)}</b><span>Annualised volatility</span></div>
          <div class="stat"><b>${n(r.corr,2)}</b><span>Return correlation</span></div>
        </div>
        <div class="ov ${ovCls(r.ov||0)}">
          Stock overlap <b>${r.ov==null?"n/a":n(r.ov,1)+"%" }</b>
          · ${r.ov>=40?"High — these two own many of the same names.":r.ov>=20?"Moderate — some shared names.":"Low — reasonably different books."}
        </div>
        ${r.tax ? MFDesk.taxBlock(r.tax) : ""}
        <p class="muted">Open the fund explorer to see the common stocks. Correlation above ~0.8 means they bounce together in a crash. Direct plan does not change capital-gains tax.</p>`;
    }

    FUNDS.forEach(f => { f._h = []; f._ov = {}; });
    const HOLD = DATA.holdings || {};
    FUNDS.forEach(f => { f._h = HOLD[String(f.code)] || []; });
    for (let i = 0; i < FUNDS.length; i++) {
      for (let j = i + 1; j < FUNDS.length; j++) {
        const ov = overlap(FUNDS[i].code, FUNDS[j].code);
        FUNDS[i]._ov[FUNDS[j].code] = ov;
        FUNDS[j]._ov[FUNDS[i].code] = ov;
      }
    }
    const opts = `<option value="">Any</option>` + FUNDS.map(f => `<option value="${f.code}">${f.name}</option>`).join("");
    $("look").innerHTML = opts;
    $("look2").innerHTML = opts;
    const CO_MAP = {
      q: "q", start: "start", lump: "lump", sip: "sip", split: "split",
      exempt: "exempt", surch: "surch",
      "combo.ovmax": "ovmax", "combo.sort": "sort",
      "combo.look": "look", "combo.look2": "look2",
      "combo.diffcat": "diffcat", "combo.nosmall": "nosmall", "combo.core": "core",
    };
    MFDesk.restore(CO_MAP);
    ["q","start","lump","sip","split","ovmax","sort","look","look2","diffcat","nosmall","core","exempt","surch"].forEach(id => {
      $(id).addEventListener("input", () => { MFDesk.persistFrom(CO_MAP); renderTable(); });
      $(id).addEventListener("change", () => { MFDesk.persistFrom(CO_MAP); renderTable(); });
    });
    $("tbody").addEventListener("click", (e) => {
      const tr = e.target.closest("tr[data-i]");
      if (!tr) return;
      const i = Number(tr.dataset.i);
      document.querySelectorAll("#tbody tr").forEach(x => x.classList.remove("sel"));
      tr.classList.add("sel");
      renderDetail(cache[i], i);
    });
    renderTable();
    MFDesk.bindScroll("combo");
  </script>
</body>
</html>
"""

RISK = (HTML / "risk_template.inc").read_text(encoding="utf-8")


def slim_holdings(raw: dict) -> dict:
    out = {}
    for code, rows in raw.items():
        out[code] = [{"n": h["n"], "k": h["k"], "w": h["w"]} for h in rows]
    return out


def main() -> None:
    whatif = json.loads((ROOT / "output" / "equity" / "whatif_data.json").read_text(encoding="utf-8"))
    combo_payload = {
        "funds": DATA["funds"],
        "nav": DATA["nav"],
        "holdings": slim_holdings(whatif["holdings"]),
        "start": DATA["start"],
        "end": DATA["end"],
    }
    risk_payload = {
        "funds": DATA["funds"],
        "top10": DATA["top10"],
        "expert_pairs": DATA.get("expert_pairs", []),
        "cat_guide": DATA.get("cat_guide", {}),
        "cat_stats": DATA.get("cat_stats", {}),
        "plan": DATA.get("plan", {"lump": 300000, "sip": 15000, "years": 15}),
        "holdings": slim_holdings(whatif["holdings"]),
        "nav": DATA.get("nav", {}),
    }
    combo = (
        COMBO.replace("__CSS__", CSS)
        .replace("__NAV__", NAV.format(ex="", co=' class="on"', rk=""))
        .replace("__DATA__", json.dumps(combo_payload, ensure_ascii=False, separators=(",", ":")))
    )
    risk = (
        RISK.replace("__CSS__", CSS)
        .replace("__NAV__", NAV.format(ex="", co="", rk=' class="on"'))
        .replace("__DATA__", json.dumps(risk_payload, ensure_ascii=False, separators=(",", ":")))
    )
    p1 = HTML / "combo_2019.html"
    p2 = HTML / "risk_forecast.html"
    p1.write_text(combo, encoding="utf-8")
    p2.write_text(risk, encoding="utf-8")
    print("wrote", p1, p1.stat().st_size)
    print("wrote", p2, p2.stat().st_size)


if __name__ == "__main__":
    main()
