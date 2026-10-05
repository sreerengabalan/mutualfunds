"""Build a light-theme HTML fund explorer with 2021 what-if + overlap."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FUNDS = json.loads((ROOT / "output" / "equity" / "selected_50.json").read_text(encoding="utf-8"))
WHATIF = json.loads((ROOT / "output" / "equity" / "whatif_data.json").read_text(encoding="utf-8"))
OUT = ROOT / "archive" / "html" / "fund_explorer.html"

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>50 Direct Growth equity funds</title>
  <style>
    :root {
      --bg: #f6f5f1;
      --ink: #1c1b18;
      --muted: #5c5a54;
      --line: #ddd9d0;
      --card: #ffffff;
      --accent: #1f4e79;
      --accent-soft: #e8eef4;
      --ok: #1f6b4a;
      --ok-bg: #e8f3ec;
      --warn: #8a5a12;
      --warn-bg: #f7eedc;
      --bad: #8b2e2e;
      --bad-bg: #f6e6e4;
      --chip: #efece4;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }
    header {
      background: var(--card);
      border-bottom: 1px solid var(--line);
      padding: 20px 24px 16px;
    }
    h1 { font-size: 22px; font-weight: 650; margin: 0 0 4px; }
    .sub { color: var(--muted); margin: 0; }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 16px 20px 48px; }
    .filters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 14px; }
    .chip {
      border: 1px solid var(--line); background: var(--card); color: var(--ink);
      padding: 6px 12px; border-radius: 999px; cursor: pointer; font: inherit;
    }
    .chip.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .controls { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 10px; margin-top: 12px; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    input, select {
      width: 100%; height: 34px; border: 1px solid var(--line);
      background: var(--card); color: var(--ink); padding: 0 10px; font: inherit;
    }
    .layout { display: grid; grid-template-columns: 1.35fr 0.9fr; gap: 16px; margin-top: 16px; }
    .panel { background: var(--card); border: 1px solid var(--line); padding: 14px; }
    h2 { font-size: 16px; margin: 0 0 10px; }
    h3 { font-size: 14px; margin: 16px 0 8px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { text-align: left; padding: 7px 6px; border-bottom: 1px solid var(--line); vertical-align: middle; }
    th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }
    td.num, th.num { text-align: right; white-space: nowrap; }
    tr.sel td { background: var(--accent-soft); }
    tr:hover td { background: #f3f1ea; }
    button.link { background: none; border: 0; color: var(--accent); cursor: pointer; font: inherit; text-align: left; padding: 0; }
    .muted { color: var(--muted); }
    .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
    .stat { background: var(--bg); border: 1px solid var(--line); padding: 10px; }
    .stat b { display: block; font-size: 18px; }
    .stat span { font-size: 11px; color: var(--muted); }
    .bar-row { display: grid; grid-template-columns: 90px 1fr 48px; gap: 8px; align-items: center; margin: 5px 0; font-size: 12px; }
    .track { height: 10px; background: var(--chip); overflow: hidden; }
    .fill { height: 100%; background: var(--accent); }
    .fill.mid { background: #c4a35a; }
    .fill.sml { background: #b56b5e; }
    .fill.debt { background: #7a8b73; }
    .kv td { font-size: 12px; }
    .note { background: #eef3e8; border: 1px solid #d3ddc8; padding: 10px 12px; color: #3d4a36; font-size: 13px; margin-top: 14px; }
    .compare { margin-top: 16px; }
    .stack { display: flex; height: 14px; background: var(--chip); overflow: hidden; }
    .stack span { display: block; height: 100%; }
    .legend { display: flex; gap: 14px; font-size: 12px; color: var(--muted); margin: 8px 0 12px; }
    .dot { width: 8px; height: 8px; display: inline-block; margin-right: 4px; }
    .whatif { margin-top: 16px; }
    .whatif-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    .ov { padding: 12px 14px; border: 1px solid var(--line); margin: 10px 0; }
    .ov.low { background: var(--ok-bg); border-color: #c5d9c9; }
    .ov.mid { background: var(--warn-bg); border-color: #e4d3ae; }
    .ov.high { background: var(--bad-bg); border-color: #e3c4c0; }
    .ov b.big { font-size: 28px; display: block; }
    .ovpill { display: inline-block; font-size: 11px; font-weight: 650; padding: 2px 7px; border-radius: 999px; }
    .ovpill.low { background: var(--ok-bg); color: var(--ok); }
    .ovpill.mid { background: var(--warn-bg); color: var(--warn); }
    .ovpill.high { background: var(--bad-bg); color: var(--bad); }
    .navlinks { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0; }
    .navlinks a {
      border: 1px solid var(--line); background: var(--card); color: var(--ink);
      padding: 6px 12px; border-radius: 999px; text-decoration: none; font-size: 13px;
    }
    .navlinks a.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    @media (max-width: 980px) {
      .layout, .controls, .whatif-grid { grid-template-columns: 1fr 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap" style="padding-top:0;padding-bottom:0">
      <h1>50 Direct Growth equity funds</h1>
      <p class="sub">Light research desk: filter funds, see allocation, run a 2021–today what-if, and check stock overlap before pairing two funds. NAV as of 11 Aug 2026.</p>
      <div class="navlinks">
        <a class="on" href="fund_explorer.html">Fund explorer</a>
        <a href="combo_2019.html">2019 two-fund combos</a>
        <a href="risk_forecast.html">Risk &amp; 10-year forecast</a>
        <a href="investment_plan.html">15Y detailed plan</a>
      </div>
      <div class="filters" id="cats"></div>
      <div class="controls">
        <div>
          <label for="q">Search name or AMC</label>
          <input id="q" placeholder="e.g. Parag Parikh, HDFC, mid" />
        </div>
        <div>
          <label for="sort">Sort</label>
          <select id="sort">
            <option value="r3">3Y rolling mean</option>
            <option value="y5">5Y CAGR</option>
            <option value="y10">10Y CAGR</option>
            <option value="aum">AUM</option>
            <option value="ter">TER (low to high)</option>
            <option value="dd">Max drawdown (least severe)</option>
            <option value="sh">Sharpe 3Y</option>
          </select>
        </div>
        <div>
          <label for="minYrs">Minimum history</label>
          <select id="minYrs">
            <option value="0">Any</option>
            <option value="3">3+ years</option>
            <option value="5">5+ years</option>
            <option value="10">10+ years</option>
          </select>
        </div>
      </div>
    </div>
  </header>

  <div class="wrap">
    <div class="panel whatif">
      <h2>If you had started investing</h2>
      <p class="muted">Pick a start date from Jan 2021 to today. Lumpsum and optional SIP use month-end NAVs. Direct Growth tax is the same as Regular: STCG 20% (≤12 months), LTCG 12.5% after ₹1.25 lakh. Direct only lowers TER.</p>
      <div class="whatif-grid">
        <div>
          <label for="start">Start date</label>
          <input id="start" type="date" min="2021-01-01" max="2026-08-11" value="2021-01-01" />
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
          <label for="split">Split to fund 1 (%)</label>
          <input id="split" type="number" min="10" max="90" step="5" value="50" />
        </div>
        <div>
          <label for="f1">Fund 1</label>
          <select id="f1"></select>
        </div>
        <div>
          <label for="f2">Fund 2 (optional)</label>
          <select id="f2"></select>
        </div>
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
      <div id="whatifOut" style="margin-top:14px"></div>
    </div>

    <div class="layout">
      <div class="panel">
        <h2 id="count">Funds</h2>
        <p class="muted">Tick funds to compare. Overlap vs the ticked funds shows in the table so you can avoid pairing similar portfolios. Click a name for the factsheet.</p>
        <div style="overflow:auto">
          <table>
            <thead>
              <tr>
                <th></th>
                <th>Fund</th>
                <th>Category</th>
                <th class="num">AUM</th>
                <th class="num">TER</th>
                <th class="num">3Y</th>
                <th class="num">5Y</th>
                <th class="num">Roll 3Y</th>
                <th class="num">Max DD</th>
                <th class="num" id="ovHead"></th>
              </tr>
            </thead>
            <tbody id="tbody"></tbody>
          </table>
        </div>
      </div>
      <div class="panel" id="detail"></div>
    </div>
    <div class="panel compare" id="compare" hidden></div>
    <p class="note">AMFI category, mfapi.in NAV (month-end from 2021), Groww holdings for overlap. Tax assumes resident individual, equity-oriented Direct Growth, FIFO lots, 4% cess, no STT on this screen. ₹1.25 lakh LTCG exemption is per PAN per year across all equity gains. Not a recommendation.</p>
  </div>

  <script src="desk_common.js"></script>
  <script>
    const FUNDS = __FUNDS__;
    const WHATIF = __WHATIF__;
    const CAT = {
      all: "All", large_cap: "Large cap", mid_cap: "Mid cap", small_cap: "Small cap",
      multi_cap: "Multi cap", flexi_cap: "Flexi cap", large_mid_cap: "Large & mid",
    };
    const CAT_ORDER = Object.keys(CAT);
    let cat = "all", q = "", sort = "r3", minYrs = 0, view = 118955, cmp = [];

    const $ = (id) => document.getElementById(id);
    const n = (v, d=2) => (v == null || Number.isNaN(v) ? "—" : Number(v).toFixed(d));
    const inr = (v) => v == null || Number.isNaN(v) ? "—" : "₹" + Math.round(v).toLocaleString("en-IN");
    const aum = (v) => v == null ? "—" : (v >= 1000 ? "₹" + (v/1000).toFixed(1) + "k Cr" : "₹" + v.toFixed(0) + " Cr");
    const fund = (code) => FUNDS.find(f => f.code === code);
    const pct = (v) => v == null ? "—" : (v * 100).toFixed(2) + "%";

    function bar(label, p, cls) {
      const w = Math.max(0, Math.min(100, p || 0));
      return `<div class="bar-row"><span>${label}</span><div class="track"><div class="fill ${cls||""}" style="width:${w}%"></div></div><span class="num">${n(p,1)}%</span></div>`;
    }

    function fillFundSelects(forceFromCmp) {
      const keep1 = $("f1").value, keep2 = $("f2").value;
      const opts = FUNDS.map(f => `<option value="${f.code}">${f.name}</option>`).join("");
      $("f1").innerHTML = opts;
      $("f2").innerHTML = `<option value="">None — one fund only</option>` + opts;
      if (forceFromCmp && cmp.length) {
        $("f1").value = String(cmp[0]);
        $("f2").value = cmp[1] ? String(cmp[1]) : "";
      } else {
        $("f1").value = keep1 || String(cmp[0] || 118955);
        $("f2").value = keep2 || (cmp[1] ? String(cmp[1]) : "");
      }
    }

    function ovClass(v) { return v >= 40 ? "high" : v >= 20 ? "mid" : "low"; }

    function overlapVsTicked(code) {
      if (!cmp.length) return null;
      let best = null, vs = null;
      cmp.forEach(c => {
        if (c === code) return;
        const oa = overlap(code, c);
        if (!oa) return;
        if (best == null || oa.ov > best) { best = oa.ov; vs = c; }
      });
      return best == null ? null : { ov: best, vs };
    }

    function overlap(a, b) {
      const ha = WHATIF.holdings[String(a)] || [];
      const hb = WHATIF.holdings[String(b)] || [];
      if (!ha.length || !hb.length) return null;
      const wa = {}, wb = {};
      ha.forEach(h => { wa[h.k] = (wa[h.k] || 0) + h.w; });
      hb.forEach(h => { wb[h.k] = (wb[h.k] || 0) + h.w; });
      const names = {};
      ha.forEach(h => { names[h.k] = h.n; });
      hb.forEach(h => { names[h.k] = names[h.k] || h.n; });
      const common = [];
      let ov = 0;
      Object.keys(wa).forEach(k => {
        if (wb[k] == null) return;
        const m = Math.min(wa[k], wb[k]);
        ov += m;
        common.push({ n: names[k], a: wa[k], b: wb[k], m });
      });
      common.sort((x,y) => y.m - x.m);
      return { ov, common, na: ha.length, nb: hb.length };
    }

    function overlapHtml(a, b) {
      const oa = overlap(a, b);
      const fa = fund(a), fb = fund(b);
      if (!oa) {
        return `<div class="ov mid"><b>Holdings not available</b><div class="muted">Cannot compute stock overlap for ${fa?.name || a} vs ${fb?.name || b}.</div></div>`;
      }
      const cls = oa.ov >= 40 ? "high" : oa.ov >= 20 ? "mid" : "low";
      const msg = oa.ov >= 40
        ? "High overlap. These two funds own many of the same stocks. Pairing them does not add much diversification."
        : oa.ov >= 20
        ? "Moderate overlap. Some of the same names appear in both. Fine as a satellite, not as two cores."
        : "Low overlap. The stock lists are reasonably different.";
      const rows = oa.common.slice(0, 12).map(r =>
        `<tr><td>${r.n}</td><td class="num">${n(r.a,2)}%</td><td class="num">${n(r.b,2)}%</td><td class="num">${n(r.m,2)}%</td></tr>`
      ).join("");
      return `<div class="ov ${cls}">
        <b class="big">${n(oa.ov,1)}%</b>
        <div>Portfolio overlap · ${oa.common.length} common stocks (of ${oa.na} and ${oa.nb} holdings)</div>
        <div style="margin-top:6px">${msg}</div>
      </div>
      ${oa.common.length ? `<table><thead><tr><th>Common stock</th><th class="num">${fa.name.slice(0,22)}</th><th class="num">${fb.name.slice(0,22)}</th><th class="num">Min weight</th></tr></thead><tbody>${rows}</tbody></table>` : ""}`;
    }

    function seriesFrom(code, start) {
      const s = (WHATIF.nav[String(code)] || []).filter(p => p[0] >= start);
      return s;
    }
    function yearsBetween(a, b) {
      return (new Date(b) - new Date(a)) / (365.25 * 24 * 3600 * 1000);
    }
    function cagr(pv, fv, yrs) {
      if (pv <= 0 || fv <= 0 || yrs <= 0) return null;
      return Math.pow(fv / pv, 1 / yrs) - 1;
    }
    function simOne(code, start, lump, sipAmt) {
      const s = seriesFrom(code, start);
      if (s.length < 2) return null;
      const startNav = s[0][1], endNav = s[s.length - 1][1], startD = s[0][0], endD = s[s.length - 1][0];
      const yrs = yearsBetween(startD, endD);
      let units = lump > 0 ? lump / startNav : 0;
      let invested = lump;
      if (sipAmt > 0) {
        s.forEach(p => { units += sipAmt / p[1]; invested += sipAmt; });
      }
      const value = units * endNav;
      const lots = MFDesk.lots(s, lump, sipAmt);
      return {
        startD, endD, yrs, invested, value,
        gain: value - invested,
        abs: invested > 0 ? (value / invested - 1) : null,
        cagr: lump > 0 && sipAmt === 0 ? cagr(lump, value, yrs) : cagr(invested, value, yrs),
        lots,
        tax: MFDesk.tax(lots),
      };
    }
    function resultCard(title, r) {
      if (!r) return `<div class="stat"><b>—</b><span>${title}: not enough NAV from this start date</span></div>`;
      const net = r.tax ? r.tax.net : r.value;
      return `<div class="stat"><b>${inr(net)}</b><span>${title} · in hand after tax</span></div>
        <div class="stat"><b>${inr(r.value)}</b><span>Gross value before tax</span></div>
        <div class="stat"><b>${inr(r.invested)}</b><span>Invested · ${r.startD} to ${r.endD}</span></div>
        <div class="stat"><b>${inr(r.gain)}</b><span>Profit before tax</span></div>
        <div class="stat"><b>${r.abs == null ? "—" : n(r.abs * 100, 1) + "%"}</b><span>Absolute return · CAGR ${pct(r.cagr)} · ${n(r.yrs,1)}y</span></div>
        <div class="stat"><b>${r.tax ? inr(r.tax.tax) : "—"}</b><span>Tax if withdrawn now</span></div>`;
    }

    function renderWhatIf() {
      const start = $("start").value || "2021-01-01";
      const lump = Number($("lump").value || 0);
      const sipAmt = Number($("sip").value || 0);
      const split = Math.min(90, Math.max(10, Number($("split").value || 50))) / 100;
      const c1 = Number($("f1").value);
      const c2 = $("f2").value ? Number($("f2").value) : 0;
      const f1 = fund(c1), f2 = c2 ? fund(c2) : null;
      const r1all = simOne(c1, start, lump, sipAmt);
      let html = `<div class="stats">${resultCard(f1.name, r1all)}</div>`;
      if (r1all && r1all.tax && !f2) html += MFDesk.taxBlock(r1all.tax);
      if (f2 && c2 !== c1) {
        const r1 = simOne(c1, start, lump * split, sipAmt * split);
        const r2 = simOne(c2, start, lump * (1 - split), sipAmt * (1 - split));
        html += `<h3 style="margin-top:14px">${f2.name}</h3><div class="stats">${resultCard(f2.name, simOne(c2, start, lump, sipAmt))}</div>`;
        if (r1 && r2) {
          const invested = r1.invested + r2.invested;
          const value = r1.value + r2.value;
          const yrs = Math.max(r1.yrs, r2.yrs);
          const lots = (r1.lots || []).concat(r2.lots || []);
          const tax = MFDesk.tax(lots);
          const comb = { startD: r1.startD, endD: r1.endD, yrs, invested, value, gain: value - invested, abs: value / invested - 1, cagr: cagr(invested, value, yrs), tax, lots };
          html += `<h3>Combined (${Math.round(split*100)} / ${Math.round((1-split)*100)}) — exemption applied once</h3>
            <div class="stats">${resultCard("Two-fund portfolio", comb)}</div>` + MFDesk.taxBlock(tax);
        }
        html += `<h3>Stock overlap</h3>` + overlapHtml(c1, c2);
      }
      $("whatifOut").innerHTML = html;
    }

    function renderCats() {
      $("cats").innerHTML = CAT_ORDER.map(id =>
        `<button class="chip ${cat===id?"on":""}" data-cat="${id}">${CAT[id]}</button>`
      ).join("");
    }

    function filtered() {
      const ql = q.trim().toLowerCase();
      const rows = FUNDS.filter(f => {
        if (cat !== "all" && f.cat !== cat) return false;
        if (minYrs > 0 && (f.yrs == null || f.yrs < minYrs)) return false;
        if (ql && !`${f.name} ${f.house} ${f.full}`.toLowerCase().includes(ql)) return false;
        return true;
      });
      const dir = (sort === "ter" || sort === "dd") ? 1 : -1;
      rows.sort((a,b) => {
        const av = a[sort], bv = b[sort];
        const an = typeof av === "number" ? av : -1e9 * dir;
        const bn = typeof bv === "number" ? bv : -1e9 * dir;
        return (an - bn) * dir;
      });
      return rows;
    }

    function renderTable() {
      const rows = filtered();
      $("count").textContent = rows.length + " funds";
      $("ovHead").textContent = cmp.length ? "Overlap vs ticked" : "";
      $("tbody").innerHTML = rows.map(f => {
        let ovCell = "";
        if (cmp.length) {
          if (cmp.includes(f.code)) ovCell = `<span class="muted">ticked</span>`;
          else {
            const o = overlapVsTicked(f.code);
            ovCell = o
              ? `<span class="ovpill ${ovClass(o.ov)}">${n(o.ov,0)}%</span>`
              : `<span class="muted">—</span>`;
          }
        }
        return `
        <tr class="${f.code===view?"sel":""}">
          <td><input type="checkbox" data-cmp="${f.code}" ${cmp.includes(f.code)?"checked":""} /></td>
          <td><button class="link" data-view="${f.code}">${f.name}</button><div class="muted">${f.house}</div></td>
          <td>${CAT[f.cat]}</td>
          <td class="num">${aum(f.aum)}</td>
          <td class="num">${n(f.ter)}</td>
          <td class="num">${n(f.y3)}</td>
          <td class="num">${n(f.y5)}</td>
          <td class="num">${n(f.r3)}</td>
          <td class="num">${n(f.dd)}</td>
          <td class="num">${ovCell}</td>
        </tr>`;
      }).join("");
    }

    function renderDetail() {
      const f = fund(view) || FUNDS[0];
      const secs = (f.sec || []).map(s => bar(s.s, s.w)).join("");
      $("detail").innerHTML = `
        <h2>${f.name}</h2>
        <p class="muted">${f.full}<br>${f.house} · ${CAT[f.cat]} · Direct Growth</p>
        <div class="stats">
          <div class="stat"><b>${aum(f.aum)}</b><span>AUM</span></div>
          <div class="stat"><b>${n(f.ter)}%</b><span>TER</span></div>
          <div class="stat"><b>${n(f.nav)}</b><span>NAV (${f.navd || "—"})</span></div>
          <div class="stat"><b>${n(f.yrs,1)} y</b><span>History</span></div>
          <div class="stat"><b>${n(f.y3)}%</b><span>3Y CAGR</span></div>
          <div class="stat"><b>${n(f.y5)}%</b><span>5Y CAGR</span></div>
          <div class="stat"><b>${n(f.r3)}%</b><span>3Y rolling mean</span></div>
          <div class="stat"><b>${n(f.dd)}%</b><span>Max drawdown</span></div>
        </div>
        <h3>Asset allocation</h3>
        ${bar("Equity", f.eq)}${bar("Debt", f.dt, "debt")}${bar("Cash", f.cash, "mid")}
        <h3>Market-cap mix</h3>
        ${bar("Large", f.l)}${bar("Mid", f.m, "mid")}${bar("Small", f.sml, "sml")}
        ${secs ? "<h3>Top sectors</h3>" + secs : ""}
        <h3>Fund facts</h3>
        <table class="kv">
          <tr><td>Manager</td><td>${f.mgr || "—"}</td></tr>
          <tr><td>Inception</td><td>${f.incept || "—"}</td></tr>
          <tr><td>Min SIP</td><td>${f.sip == null ? "—" : "₹" + f.sip}</td></tr>
          <tr><td>Exit load</td><td>${f.load || "—"}</td></tr>
          <tr><td>Sharpe / Sortino 3Y</td><td>${n(f.sh)} / ${n(f.so)}</td></tr>
          <tr><td>Volatility</td><td>${n(f.vol)}%</td></tr>
          <tr><td>10Y CAGR / SIP 5Y</td><td>${n(f.y10)}% / ${n(f.sip5)}%</td></tr>
          <tr><td>Top 5 / Top 10</td><td>${n(f.t5)}% / ${n(f.t10)}%</td></tr>
          <tr><td>Holdings / turnover</td><td>${f.hold ?? "—"} / ${f.turn == null ? "—" : n(f.turn,0) + "%"}</td></tr>
          <tr><td>PE / PB</td><td>${n(f.pe,1)} / ${n(f.pb,1)}</td></tr>
        </table>`;
    }

    function renderCompare() {
      const box = $("compare");
      if (cmp.length < 2) { box.hidden = true; box.innerHTML = ""; return; }
      const fs = cmp.map(fund).filter(Boolean);
      const head = "<th>Metric</th>" + fs.map(f => `<th>${f.name}</th>`).join("");
      const row = (label, fn) => `<tr><td>${label}</td>${fs.map(f => `<td>${fn(f)}</td>`).join("")}</tr>`;
      const stacks = fs.map(f => {
        const t = (f.l||0)+(f.m||0)+(f.sml||0) || 1;
        return `<div style="margin:8px 0 12px"><div class="muted">${f.name}</div>
          <div class="stack">
            <span style="width:${(f.l||0)/t*100}%;background:#1f4e79"></span>
            <span style="width:${(f.m||0)/t*100}%;background:#c4a35a"></span>
            <span style="width:${(f.sml||0)/t*100}%;background:#b56b5e"></span>
          </div></div>`;
      }).join("");
      let ovBlock = "";
      for (let i = 0; i < fs.length; i++) {
        for (let j = i + 1; j < fs.length; j++) {
          ovBlock += `<h3>${fs[i].name} vs ${fs[j].name}</h3>` + overlapHtml(fs[i].code, fs[j].code);
        }
      }
      box.hidden = false;
      box.innerHTML = `
        <h2>Compare (${fs.length}) — overlap first</h2>
        <p class="muted">If overlap is high, do not hold both as core funds. Use one of them plus a different category.</p>
        ${ovBlock}
        <div class="legend">
          <span><i class="dot" style="background:#1f4e79"></i>Large</span>
          <span><i class="dot" style="background:#c4a35a"></i>Mid</span>
          <span><i class="dot" style="background:#b56b5e"></i>Small</span>
        </div>
        ${stacks}
        <div style="overflow:auto"><table>
          <thead><tr>${head}</tr></thead>
          <tbody>
            ${row("AMC", f => f.house)}
            ${row("Category", f => CAT[f.cat])}
            ${row("AUM", f => aum(f.aum))}
            ${row("TER %", f => n(f.ter))}
            ${row("1Y / 3Y / 5Y / 10Y", f => [n(f.y1),n(f.y3),n(f.y5),n(f.y10)].join(" / "))}
            ${row("Roll 3Y mean", f => n(f.r3))}
            ${row("Vol / Max DD", f => n(f.vol) + " / " + n(f.dd))}
            ${row("L / M / S %", f => [n(f.l,0),n(f.m,0),n(f.sml,0)].join(" / "))}
          </tbody>
        </table></div>`;
    }

    function render() {
      renderCats();
      renderTable();
      renderDetail();
      renderCompare();
      fillFundSelects(false);
      renderWhatIf();
    }

    function persistExplorer() {
      MFDesk.save({
        q: q,
        "explorer.cat": cat,
        "explorer.sort": sort,
        "explorer.minYrs": minYrs,
        "explorer.view": view,
        "explorer.cmp": cmp,
        start: $("start").value,
        lump: $("lump").value,
        sip: $("sip").value,
        split: $("split").value,
        f1: $("f1").value,
        f2: $("f2").value,
        exempt: $("exempt").value,
        surch: $("surch").value,
      });
    }

    $("q").oninput = (e) => { q = e.target.value; persistExplorer(); renderTable(); };
    $("sort").onchange = (e) => { sort = e.target.value; persistExplorer(); renderTable(); };
    $("minYrs").onchange = (e) => { minYrs = Number(e.target.value); persistExplorer(); renderTable(); };
    ["start","lump","sip","split","f1","f2","exempt","surch"].forEach(id => {
      $(id).addEventListener("input", () => { persistExplorer(); renderWhatIf(); });
      $(id).addEventListener("change", () => { persistExplorer(); renderWhatIf(); });
    });
    $("cats").addEventListener("click", (e) => {
      const b = e.target.closest("[data-cat]");
      if (!b) return;
      cat = b.dataset.cat;
      persistExplorer();
      renderCats();
      renderTable();
    });
    document.addEventListener("click", (e) => {
      const v = e.target.closest("[data-view]");
      if (v) { view = Number(v.dataset.view); persistExplorer(); renderDetail(); renderTable(); }
    });
    document.addEventListener("change", (e) => {
      const c = e.target.closest("[data-cmp]");
      if (!c) return;
      const code = Number(c.dataset.cmp);
      if (c.checked) {
        if (cmp.length >= 4) { c.checked = false; return; }
        cmp = [...cmp, code];
      } else cmp = cmp.filter(x => x !== code);
      persistExplorer();
      renderCompare();
      fillFundSelects(true);
      renderWhatIf();
      renderTable();
      if (cmp.length >= 2) $("compare").scrollIntoView({ behavior: "smooth", block: "start" });
    });

    MFDesk.absorbHash();
    MFDesk.syncNav();
    const st = MFDesk.load();
    if (st.q) q = st.q;
    if (st["explorer.cat"]) cat = st["explorer.cat"];
    if (st["explorer.sort"]) sort = st["explorer.sort"];
    if (st["explorer.minYrs"] != null && st["explorer.minYrs"] !== "") minYrs = Number(st["explorer.minYrs"]);
    if (st["explorer.view"]) view = Number(st["explorer.view"]);
    if (Array.isArray(st["explorer.cmp"])) cmp = st["explorer.cmp"].map(Number);
    if ($("q") && st.q != null) $("q").value = st.q;
    if ($("sort") && st["explorer.sort"]) $("sort").value = st["explorer.sort"];
    if ($("minYrs") && st["explorer.minYrs"] != null) $("minYrs").value = String(st["explorer.minYrs"]);
    fillFundSelects(true);
    MFDesk.restore({
      start: "start", lump: "lump", sip: "sip", split: "split",
      f1: "f1", f2: "f2", exempt: "exempt", surch: "surch",
    });
    render();
    MFDesk.bindScroll("explorer");
  </script>
</body>
</html>
"""


def main() -> None:
    html = HTML.replace("__FUNDS__", json.dumps(FUNDS, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("__WHATIF__", json.dumps(WHATIF, ensure_ascii=False, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")
    print("wrote", OUT, "bytes", OUT.stat().st_size)


if __name__ == "__main__":
    main()
