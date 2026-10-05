"""Generate investment_plan.html — detailed 15-year planner with year-by-year tables."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "output" / "equity" / "plan_detail.json").read_text(encoding="utf-8"))
OUT = ROOT / "archive" / "html" / "investment_plan.html"

CSS = """
    :root {
      --bg: #f6f5f1; --ink: #1c1b18; --muted: #5c5a54; --line: #ddd9d0;
      --card: #fff; --accent: #1f4e79; --accent-soft: #e8eef4;
      --ok: #1f6b4a; --ok-bg: #e8f3ec; --warn: #8a5a12; --warn-bg: #f7eedc;
      --bad: #8b2e2e; --bad-bg: #f6e6e4; --chip: #efece4;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font: 14px/1.5 "Segoe UI", system-ui, sans-serif; color: var(--ink); background: var(--bg); }
    header { background: var(--card); border-bottom: 1px solid var(--line); padding: 18px 24px; position: sticky; top: 0; z-index: 10; }
    h1 { font-size: 21px; margin: 0 0 4px; font-weight: 650; }
    h2 { font-size: 16px; margin: 0 0 10px; }
    h3 { font-size: 14px; margin: 12px 0 6px; }
    .sub { color: var(--muted); margin: 0; font-size: 13px; }
    .wrap { max-width: 1200px; margin: 0 auto; padding: 16px 20px 60px; }
    .navlinks { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 0; }
    .navlinks a, .anchor a {
      border: 1px solid var(--line); background: var(--card); color: var(--ink);
      padding: 6px 12px; border-radius: 999px; text-decoration: none; font-size: 13px;
    }
    .navlinks a.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .anchor { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0; }
    .controls { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 12px; }
    label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
    input, select {
      width: 100%; height: 34px; border: 1px solid var(--line);
      background: var(--card); padding: 0 10px; font: inherit;
    }
    .panel { background: var(--card); border: 1px solid var(--line); padding: 16px; margin-top: 16px; }
    .note { background: #eef3e8; border: 1px solid #d3ddc8; padding: 10px 12px; color: #3d4a36; font-size: 13px; margin-top: 14px; }
    .warnbox { background: var(--warn-bg); border: 1px solid #e4d3ae; padding: 12px; margin-top: 14px; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 8px 6px; border-bottom: 1px solid var(--line); text-align: left; }
    th { font-size: 11px; text-transform: uppercase; color: var(--muted); letter-spacing: .03em; }
    td.num, th.num { text-align: right; white-space: nowrap; }
    tr:hover td { background: #f8f7f3; }
    .concept { border: 1px solid var(--line); margin: 8px 0; background: var(--bg); }
    .concept summary { padding: 10px 12px; cursor: pointer; font-weight: 600; list-style: none; }
    .concept summary::-webkit-details-marker { display: none; }
    .concept .body { padding: 0 12px 12px; color: var(--muted); font-size: 13px; }
    .pair { border: 1px solid var(--line); margin: 12px 0; }
    .pair-h { padding: 12px 14px; cursor: pointer; background: var(--bg); display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
    .pair-h:hover { background: #f0efe8; }
    .pair-b { padding: 0 14px 14px; display: none; }
    .pair.open .pair-b { display: block; }
    .tabs { display: flex; gap: 6px; flex-wrap: wrap; margin: 10px 0; }
    .tab {
      border: 1px solid var(--line); background: var(--card); padding: 5px 10px;
      border-radius: 999px; cursor: pointer; font-size: 12px;
    }
    .tab.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .chart { display: flex; align-items: flex-end; gap: 4px; height: 120px; margin: 12px 0; padding: 8px 0; border-bottom: 1px solid var(--line); }
    .bar { flex: 1; min-width: 0; background: var(--accent); border-radius: 2px 2px 0 0; position: relative; }
    .bar.profit { background: var(--ok); opacity: 0.85; }
    .bar span { position: absolute; bottom: -18px; left: 50%; transform: translateX(-50%); font-size: 9px; color: var(--muted); white-space: nowrap; }
    .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; background: var(--chip); margin: 2px 4px 2px 0; }
    .tag.ok { background: var(--ok-bg); color: var(--ok); }
    .tag.warn { background: var(--warn-bg); color: var(--warn); }
    .highlight { background: var(--accent-soft); padding: 12px; border-radius: 4px; margin: 10px 0; }
    .presets { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
    .preset {
      border: 1px solid var(--line); background: var(--card); padding: 8px 14px;
      border-radius: 999px; cursor: pointer; font-size: 13px;
    }
    .preset.on { background: var(--accent); color: #fff; border-color: var(--accent); }
    .catgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0; }
    .catbox { border: 1px solid var(--line); padding: 10px 12px; background: var(--bg); font-size: 13px; }
    .fcards { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0; }
    .fcard { border: 1px solid var(--line); padding: 12px; background: var(--bg); font-size: 13px; }
    .fcard b { display: block; margin-bottom: 4px; }
    .fcard .kpi { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
    .fcard .kpi span { font-size: 11px; background: var(--chip); padding: 2px 8px; border-radius: 999px; }
    .ov { padding: 12px; border: 1px solid var(--line); margin: 12px 0; background: var(--bg); }
    .ov.low { border-color: #b8d4c4; background: var(--ok-bg); }
    .ov.mid { border-color: #e4d3ae; background: var(--warn-bg); }
    .ov.high { border-color: #e0b4b4; background: var(--bad-bg); }
    .ov .big { font-size: 22px; display: block; margin-bottom: 4px; }
    .scenarios { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 12px 0; }
    .scenario { border: 1px solid var(--line); padding: 12px; background: var(--bg); }
    .scenario b { display: block; font-size: 18px; }
    .scenario span { font-size: 12px; color: var(--muted); }
    .scenario.bear { border-color: #e0b4b4; }
    .scenario.bull { border-color: #b8d4c4; }
    .btn-link {
      border: none; background: none; color: var(--accent); cursor: pointer;
      font: inherit; font-size: 12px; text-decoration: underline; padding: 0;
    }
    @media (max-width: 900px) {
      .controls { grid-template-columns: 1fr 1fr; }
      .fcards, .catgrid, .scenarios { grid-template-columns: 1fr; }
    }
"""

NAV = """
      <div class="navlinks">
        <a href="fund_explorer.html">Fund explorer</a>
        <a href="combo_2019.html">2019 combos</a>
        <a href="risk_forecast.html">Risk forecast</a>
        <a class="on" href="investment_plan.html">15Y detailed plan</a>
        <a href="http://localhost:5177/" target="_blank" rel="noreferrer">React MF Desk ↗</a>
      </div>
"""

BODY = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>15-year investment plan · detailed</title>
  <style>__CSS__</style>
</head>
<body>
  <header>
    <div class="wrap" style="padding-top:0;padding-bottom:0">
      <h1>15-year plan · year-by-year detail</h1>
      <p class="sub">₹3 lakh lumpsum + ₹15,000/month · 10 expert pairs · build Flexi+Mid (or any combo) · year-by-year forecast &amp; history</p>
      __NAV__
      <div class="controls">
        <div><label for="lump">Lumpsum (₹)</label><input id="lump" type="number" step="50000" value="300000" /></div>
        <div><label for="sip">Monthly SIP (₹)</label><input id="sip" type="number" step="1000" value="15000" /></div>
        <div><label for="years">Horizon (years)</label><input id="years" type="number" min="5" max="25" value="15" /></div>
        <div><label for="quickPreset">Category combo</label>
          <select id="quickPreset"><option value="">— jump to builder —</option></select>
        </div>
      </div>
    </div>
  </header>
  <div class="wrap">
    <div class="anchor">
      <a href="#learn">Concepts</a>
      <a href="#pairs">10 expert pairs</a>
      <a href="#builder">Build your pair</a>
    </div>
    <div class="warnbox"><b>How ₹30L can become ₹1.5 crore+ (base case):</b> You put in ₹3L on day one, then ₹15K every month for 15 years = ₹30L total. If the blended portfolio earns ~19% CAGR (base case for core+satellite), compounding on the early money plus 180 SIP instalments can reach ~₹1.6–2 crore before tax. Bear (~15%) might land near ₹80L–1Cr; bull (~21%) could exceed ₹2Cr. None of this is guaranteed.</div>

    <div class="panel" id="learn">
      <h2>Concepts — read before you pick</h2>
      <div id="concepts"></div>
    </div>

    <div class="panel" id="pairs">
      <h2>10 expert-style pairs · 15-year forecast + real history</h2>
      <p class="muted">Click a pair to expand. Tables show each calendar year: money added that year, total invested so far, portfolio value, profit, and return on invested capital. History uses actual NAV — not a forecast.</p>
      <div id="pairlist"></div>
    </div>

    <div class="panel" id="builder">
      <h2>Build your pair — pick categories, then funds</h2>
      <p class="muted">Choose a category combo (e.g. Flexi + Mid), pick the exact funds, set split. Full details: category guide, fund KPIs, stock overlap, risk, and year-by-year forecast or real history.</p>
      <div class="presets" id="presets"></div>
      <p class="muted" id="presetHint" style="margin-top:0"></p>
      <div class="controls" style="margin-top:0">
        <div><label for="bcatA">Category A (core)</label><select id="bcatA"></select></div>
        <div><label for="ba">Fund A</label><select id="ba"></select></div>
        <div><label for="bcatB">Category B (satellite)</label><select id="bcatB"></select></div>
        <div><label for="bb">Fund B</label><select id="bb"></select></div>
        <div><label for="bsplit">Fund A %</label><input id="bsplit" type="number" min="20" max="80" step="5" value="65" /></div>
        <div><label for="bhistStart">History from</label>
          <select id="bhistStart"><option value="2016">2016 (10Y)</option><option value="2019">Feb 2019</option><option value="2021" selected>2021</option></select>
        </div>
      </div>
      <div id="builderDetail"></div>
      <div class="tabs" id="builderTabs">
        <button type="button" class="tab on" data-bsc="base">Base forecast</button>
        <button type="button" class="tab" data-bsc="bear">Bear forecast</button>
        <button type="button" class="tab" data-bsc="bull">Bull forecast</button>
        <button type="button" class="tab" data-bsc="hist">Actual history</button>
      </div>
      <div id="builderTable"></div>
    </div>
    <p class="note">Direct Growth · educational only · not investment advice. Tax on withdrawal: STCG 20% (≤12 months), LTCG 12.5% after ₹1.25L/year exemption, plus 4% cess.</p>
  </div>
  <script src="desk_common.js"></script>
  <script>
    const DATA = __DATA__;
    const FUNDS = DATA.funds;
    const PAIRS = DATA.expert_pairs;
    const NAV = DATA.nav;
    const HOLD = DATA.holdings || {};
    const THEMES = DATA.themes || {};
    const CATG = DATA.cat_guide || {};
    const CSTATS = DATA.cat_stats || {};
    const PRESETS = DATA.combo_presets || [];
    const CAT = { large_cap:"Large cap", mid_cap:"Mid cap", small_cap:"Small cap", multi_cap:"Multi cap", flexi_cap:"Flexi cap", large_mid_cap:"Large & mid" };
    const CAT_ORDER = ["flexi_cap","large_cap","large_mid_cap","multi_cap","mid_cap","small_cap"];
    const $ = id => document.getElementById(id);
    const inr = v => "₹" + Math.round(v||0).toLocaleString("en-IN");
    const n = (v,d=1) => v==null||Number.isNaN(v)?"—":Number(v).toFixed(d);
    const fund = c => FUNDS.find(f => f.code === Number(c));
    let builderTab = "base", activePreset = PRESETS[0]?.id || "";

    function cagrDec(f) {
      for (const k of ["y10","y5","r3","y3"]) if (f && f[k] > 0) return f[k]/100;
      return 0.12;
    }
    function cagrPct(f) { return cagrDec(f)*100; }
    function mRate(cagr) { return Math.pow(1+cagr, 1/12)-1; }
    function blendCagr(fa, fb, split) {
      const w = split/100;
      return w*cagrDec(fa) + (1-w)*cagrDec(fb);
    }
    function scenarioCagrs(base) {
      return { base, bear: Math.max(base-0.04,0.06), bull: Math.min(base+0.02,0.22) };
    }
    function forecastEnd(cagr, lump, sip, years) {
      const m = years*12, rm = cagr/12;
      const fvL = lump*Math.pow(1+rm,m);
      const fvS = rm>1e-9 ? sip*((Math.pow(1+rm,m)-1)/rm) : sip*m;
      const invested = lump+sip*m;
      const value = fvL+fvS;
      return { invested, value, gain: value-invested, cagr };
    }
    function overlapDetail(a, b) {
      const ha = HOLD[String(a)]||[], hb = HOLD[String(b)]||[];
      if (!ha.length||!hb.length) return null;
      const wa={}, wb={}, names={};
      ha.forEach(h => { wa[h.k]=(wa[h.k]||0)+h.w; names[h.k]=h.n; });
      hb.forEach(h => { wb[h.k]=(wb[h.k]||0)+h.w; names[h.k]=names[h.k]||h.n; });
      const common=[];
      let ov=0;
      Object.keys(wa).forEach(k => {
        if (wb[k]==null) return;
        const m=Math.min(wa[k],wb[k]);
        ov+=m;
        common.push({n:names[k],a:wa[k],b:wb[k],m});
      });
      common.sort((x,y)=>y.m-x.m);
      return { ov, common, na:ha.length, nb:hb.length };
    }
    function corrFromNav(ca, cb) {
      const da={}, db={};
      (NAV[String(ca)]||[]).forEach(p => da[p[0]]=p[1]);
      (NAV[String(cb)]||[]).forEach(p => db[p[0]]=p[1]);
      const dates=Object.keys(da).filter(d=>db[d]).sort();
      if (dates.length<24) return 0.7;
      const ra=[], rb=[];
      for (let i=1;i<dates.length;i++) {
        ra.push(da[dates[i]]/da[dates[i-1]]-1);
        rb.push(db[dates[i]]/db[dates[i-1]]-1);
      }
      const ma=ra.reduce((s,x)=>s+x,0)/ra.length, mb=rb.reduce((s,x)=>s+x,0)/rb.length;
      let num=0,d1=0,d2=0;
      for (let i=0;i<ra.length;i++) { const xa=ra[i]-ma,xb=rb[i]-mb; num+=xa*xb; d1+=xa*xa; d2+=xb*xb; }
      const c=num/Math.sqrt(d1*d2);
      return Number.isNaN(c)?0.7:c;
    }
    function histDrawdown(ca, cb, split, lump, sip) {
      const w=split/100, w2=1-w;
      const da={}, db={};
      (NAV[String(ca)]||[]).forEach(p => da[p[0]]=p[1]);
      (NAV[String(cb)]||[]).forEach(p => db[p[0]]=p[1]);
      const dates=Object.keys(da).filter(d=>db[d]&&d>="2019-02-01").sort();
      if (dates.length<24) return null;
      let ua=lump*w/da[dates[0]], ub=lump*w2/db[dates[0]], peak=0, maxDd=0;
      dates.forEach((d,i) => {
        if (i>0) { ua+=sip*w/da[d]; ub+=sip*w2/db[d]; }
        const val=ua*da[d]+ub*db[d];
        peak=Math.max(peak,val);
        if (peak>0) maxDd=Math.max(maxDd,(peak-val)/peak);
      });
      return maxDd*100;
    }
    function pairRiskLive(fa, fb, splitPct) {
      const w=splitPct/100, w2=1-w;
      const od=overlapDetail(fa.code, fb.code);
      const ov=od?od.ov:null;
      const corr=corrFromNav(fa.code, fb.code);
      const v1=(fa.vol||15)/100, v2=(fb.vol||15)/100;
      const portVol=Math.sqrt(w*w*v1*v1+w2*w2*v2*v2+2*w*w2*v1*v2*corr)*100;
      const dd1=Math.abs(fa.dd||35), dd2=Math.abs(fb.dd||35);
      const histDd=histDrawdown(fa.code, fb.code, splitPct, +$("lump").value, +$("sip").value)
        || Math.min(w*dd1+w2*dd2*0.9,55);
      let score=0;
      if (fa.cat!==fb.cat) score+=25;
      if (ov!=null&&ov<25) score+=25; else if (ov!=null&&ov<35) score+=12;
      if ((fa.sh||0)>0.5&&(fb.sh||0)>0.5) score+=Math.min(((fa.sh||0)+(fb.sh||0))*10,20);
      if ((fa.yrs||0)>=10&&(fb.yrs||0)>=10) score+=15;
      let band="Moderate";
      if (fa.cat==="small_cap"||fb.cat==="small_cap"||portVol>17) band="Aggressive";
      if (portVol<14&&!["small_cap","mid_cap"].includes(fa.cat)&&!["small_cap","mid_cap"].includes(fb.cat)) band="Conservative";
      if (fa.cat===fb.cat) band="Moderate — same category";
      return { ov, od, corr, portVol, histDd, fitScore:Math.min(score,100), band };
    }
    function overlapHtml(fa, fb) {
      const od=overlapDetail(fa.code, fb.code);
      if (!od) return `<div class="ov mid"><b class="big">—</b><div>Holdings not available for overlap check.</div></div>`;
      const cls=od.ov>=40?"high":od.ov>=20?"mid":"low";
      const msg=od.ov>=40?"High overlap — many same stocks. Pairing adds little diversification."
        :od.ov>=20?"Moderate overlap — OK as satellite, not two cores."
        :"Low overlap — reasonably different stock lists.";
      const rows=od.common.slice(0,10).map(r=>
        `<tr><td>${r.n}</td><td class="num">${n(r.a,2)}%</td><td class="num">${n(r.b,2)}%</td><td class="num">${n(r.m,2)}%</td></tr>`
      ).join("");
      return `<div class="ov ${cls}"><b class="big">${n(od.ov,1)}%</b>
        <div>${od.common.length} common stocks (of ${od.na} and ${od.nb} holdings)</div>
        <div style="margin-top:6px">${msg}</div></div>
        ${od.common.length?`<table><thead><tr><th>Common stock</th><th class="num">${fa.name.slice(0,24)}</th><th class="num">${fb.name.slice(0,24)}</th><th class="num">Overlap</th></tr></thead><tbody>${rows}</tbody></table>`:""}`;
    }
    function catBox(cat) {
      const g=CATG[cat]||{}, s=CSTATS[cat]||{};
      return `<div class="catbox"><b>${g.label||CAT[cat]||cat}</b>
        <div>${g.sebi||""}</div>
        <div class="muted" style="margin-top:6px"><b>Risk:</b> ${g.risk||""}</div>
        <div class="muted"><b>Role:</b> ${g.role||""}</div>
        ${s.n?`<div class="muted" style="margin-top:6px">Median in list: 3Y ${n(s.r3)}% · vol ${n(s.vol)}% · DD ${n(s.dd)}%</div>`:""}
      </div>`;
    }
    function fundCard(f, pct, side) {
      const th=THEMES[String(f.code)]||{};
      const themeTags=["ai","ev","digital","oil"].filter(t=>(th[t]||0)>3)
        .map(t=>`<span>${t.toUpperCase()} ${n(th[t],1)}%</span>`).join("");
      return `<div class="fcard"><b>${f.name}</b>
        <div class="muted">${f.house} · ${CAT[f.cat]} · ${side} ${pct}%</div>
        <div class="kpi">
          <span>3Y ${n(f.r3||f.y3)}%</span><span>5Y ${n(f.y5)}%</span><span>10Y ${n(f.y10)}%</span>
          <span>Vol ${n(f.vol)}%</span><span>Max DD ${n(f.dd)}%</span><span>Sharpe ${n(f.sh,2)}</span>
          ${themeTags}
        </div></div>`;
    }
    function yearlyProj(cagr, lump, sip, years, y0) {
      const rm = mRate(cagr);
      let val = lump, inv = lump, rows = [], sipYr = 0;
      for (let m = 1; m <= years*12; m++) {
        if (m > 1) { val = val*(1+rm)+sip; inv += sip; sipYr += sip; }
        if (m % 12 === 0) {
          rows.push({ y: y0 + m/12 - 1, added: rows.length ? sipYr : lump, invested: inv, value: val, profit: val-inv, ret: (val-inv)/inv*100 });
          sipYr = 0;
        }
      }
      return rows.map(r => ({ ...r, added: Math.round(r.added), invested: Math.round(r.invested), value: Math.round(r.value), profit: Math.round(r.profit), ret: +r.ret.toFixed(1) }));
    }
    function mRate(cagr) { return Math.pow(1+cagr, 1/12)-1; }
    function yearlyHist(ca, cb, split, lump, sip, startYear) {
      const start = startYear === "2019" ? "2019-02-01" : startYear + "-01-01";
      const da = {}, db = {};
      (NAV[String(ca)]||[]).forEach(p => { if (p[0]>=start) da[p[0]]=p[1]; });
      (NAV[String(cb)]||[]).forEach(p => { if (p[0]>=start) db[p[0]]=p[1]; });
      const dates = Object.keys(da).filter(d => db[d]).sort();
      if (dates.length < 6) return [];
      const w1 = split/100, w2 = 1-w1;
      let ua = lump*w1/da[dates[0]], ub = lump*w2/db[dates[0]], inv = lump, rows = [], sipYr = 0;
      dates.forEach((d,i) => {
        if (i > 0) { ua += sip*w1/da[d]; ub += sip*w2/db[d]; inv += sip; sipYr += sip; }
        const val = ua*da[d]+ub*db[d];
        const nxt = dates[i+1];
        if (!nxt || nxt.slice(0,4) !== d.slice(0,4)) {
          rows.push({ y:+d.slice(0,4), added: rows.length?Math.round(sipYr):lump, invested: Math.round(inv), value: Math.round(val), profit: Math.round(val-inv), ret: +((val-inv)/inv*100).toFixed(1) });
          sipYr = 0;
        }
      });
      return rows;
    }
    function scaleRows(rows, lump0, sip0, lump, sip) {
      if (!rows.length || (lump0===lump && sip0===sip)) return rows;
      const ratio = (lump/lump0 + sip/sip0) / 2;
      return rows.map(r => ({ ...r, added: Math.round(r.added * (r.added>lump0? sip/sip0 : lump/lump0)), invested: Math.round(r.invested * ((r.invested/lump0)/2 + (r.invested/(sip0*12))/2)), value: Math.round(r.value * ratio), profit: 0, ret: r.ret }));
    }
    function fundsInCat(cat) {
      return FUNDS.filter(f => f.cat === cat).sort((a,b) => (b.y5||0)-(a.y5||0));
    }
    function fillCatSelect(sel, selected) {
      sel.innerHTML = CAT_ORDER.filter(c => CATG[c] || FUNDS.some(f => f.cat===c))
        .map(c => `<option value="${c}">${CAT[c]||c}</option>`).join("");
      if (selected) sel.value = selected;
    }
    function fillFundSelect(sel, cat, selected) {
      const list = fundsInCat(cat);
      sel.innerHTML = list.map(f => `<option value="${f.code}">${f.name} (5Y ${n(f.y5)}%)</option>`).join("");
      if (selected && list.some(f => f.code===Number(selected))) sel.value = selected;
      else if (list[0]) sel.value = list[0].code;
    }
    function applyPreset(id) {
      const p = PRESETS.find(x => x.id === id);
      if (!p) return;
      activePreset = id;
      $("bcatA").value = p.catA;
      $("bcatB").value = p.catB;
      $("bsplit").value = p.split;
      fillFundSelect($("ba"), p.catA, p.defaultA);
      fillFundSelect($("bb"), p.catB, p.defaultB);
      $("presetHint").textContent = p.hint || "";
      document.querySelectorAll(".preset").forEach(el => el.classList.toggle("on", el.dataset.id === id));
      renderBuilder();
    }
    function loadExpert(i) {
      const p = PAIRS[i];
      if (!p) return;
      activePreset = "";
      document.querySelectorAll(".preset").forEach(el => el.classList.remove("on"));
      $("bcatA").value = p.ac;
      $("bcatB").value = p.bc;
      $("bsplit").value = p.split;
      fillFundSelect($("ba"), p.ac, p.a);
      fillFundSelect($("bb"), p.bc, p.b);
      $("presetHint").textContent = p.why || "";
      builderTab = "base";
      document.querySelectorAll("#builderTabs .tab").forEach(t => t.classList.toggle("on", t.dataset.bsc === "base"));
      renderBuilder();
      $("builder").scrollIntoView({ behavior: "smooth" });
    }
    function renderPresets() {
      $("presets").innerHTML = PRESETS.map(p =>
        `<button type="button" class="preset${p.id===activePreset?" on":""}" data-id="${p.id}">${p.label}</button>`
      ).join("");
      $("presets").onclick = e => {
        const b = e.target.closest(".preset");
        if (b) applyPreset(b.dataset.id);
      };
      const qs = $("quickPreset");
      if (qs) {
        qs.innerHTML = `<option value="">— pick combo —</option>` + PRESETS.map(p =>
          `<option value="${p.id}">${p.label}</option>`).join("");
        qs.onchange = () => { if (qs.value) { applyPreset(qs.value); qs.value=""; $("builder").scrollIntoView({behavior:"smooth"}); } };
      }
    }
    function renderBuilder() {
      const lump=+$("lump").value, sip=+$("sip").value, years=+$("years").value;
      const y0 = DATA.plan.start_forecast_year || 2027;
      const split=+$("bsplit").value;
      const fa=fund($("ba").value), fb=fund($("bb").value);
      if (!fa||!fb) { $("builderDetail").innerHTML = "<p class='muted'>Pick two funds.</p>"; return; }
      const base=blendCagr(fa,fb,split);
      const sc=scenarioCagrs(base);
      const rk=pairRiskLive(fa,fb,split);
      const bearFc=forecastEnd(sc.bear,lump,sip,years);
      const baseFc=forecastEnd(sc.base,lump,sip,years);
      const bullFc=forecastEnd(sc.bull,lump,sip,years);
      const ovCls=rk.ov>=40?"bad":rk.ov>=20?"warn":"ok";
      const sameCat=fa.cat===fb.cat;
      $("builderDetail").innerHTML = `
        <div class="highlight"><b>${fa.name}</b> (${CAT[fa.cat]}) · ${split}% + <b>${fb.name}</b> (${CAT[fb.cat]}) · ${100-split}%
        ${sameCat?` · <span class="tag warn">Same category — overlap often high</span>`:""}</div>
        <div class="catgrid">${catBox(fa.cat)}${catBox(fb.cat)}</div>
        <div class="fcards">${fundCard(fa,split,"Core")}${fundCard(fb,100-split,"Satellite")}</div>
        <div style="margin:8px 0">
          <span class="tag ${ovCls}">Overlap ${rk.ov==null?"n/a":n(rk.ov,1)+"%"}</span>
          <span class="tag">Fit score ~${n(rk.fitScore,0)}/100</span>
          <span class="tag">Correlation ${n(rk.corr,2)}</span>
          <span class="tag">Portfolio vol ~${n(rk.portVol,1)}%</span>
          <span class="tag warn">Worst DD since 2019 ~${n(rk.histDd,0)}%</span>
          <span class="tag ${rk.band.startsWith("Agg")?"bad":rk.band.startsWith("Cons")?"ok":"warn"}">${rk.band}</span>
        </div>
        ${overlapHtml(fa,fb)}
        <p class="muted">Total invested over ${years} years: <b>${inr(baseFc.invested)}</b> (${inr(lump)} lumpsum + ${inr(sip)}/month)</p>
        <div class="scenarios">
          <div class="scenario bear"><b>${inr(bearFc.value)}</b><span>Bear · ${n(sc.bear*100,1)}% CAGR · profit ${inr(bearFc.gain)}</span></div>
          <div class="scenario"><b>${inr(baseFc.value)}</b><span>Base · ${n(sc.base*100,1)}% CAGR · profit ${inr(baseFc.gain)}</span></div>
          <div class="scenario bull"><b>${inr(bullFc.value)}</b><span>Bull · ${n(sc.bull*100,1)}% CAGR · profit ${inr(bullFc.gain)}</span></div>
        </div>`;
      let rows, title;
      if (builderTab === "hist") {
        const hy = $("bhistStart").value;
        rows = yearlyHist(fa.code, fb.code, split, lump, sip, hy);
        title = `Actual history from ${hy} · real NAV (not forecast)`;
      } else {
        let cagr = sc[builderTab];
        rows = yearlyProj(cagr, lump, sip, years, y0);
        title = `${builderTab.charAt(0).toUpperCase()+builderTab.slice(1)} forecast (~${n(cagr*100,1)}% CAGR)`;
      }
      $("builderTable").innerHTML = tableHtml(rows, title);
    }
    function tableHtml(rows, title) {
      if (!rows.length) return "<p class='muted'>Not enough NAV history.</p>";
      const maxV = Math.max(...rows.map(r => r.value));
      const bars = rows.map(r => {
        const h = Math.max(4, r.value/maxV*100);
        const hp = Math.max(2, r.profit/maxV*100);
        return `<div class="bar" style="height:${h}px" title="${r.y}: ${inr(r.value)}"><span>${String(r.y).slice(2)}</span></div>`;
      }).join("");
      const trs = rows.map(r => `<tr><td>${r.y}</td><td class="num">${inr(r.added)}</td><td class="num">${inr(r.invested)}</td><td class="num">${inr(r.value)}</td><td class="num">${inr(r.profit)}</td><td class="num">${r.ret}%</td></tr>`).join("");
      return `<h3>${title}</h3><div class="chart">${bars}</div><div style="overflow:auto"><table>
        <thead><tr><th>Year</th><th class="num">Added this year</th><th class="num">Total invested</th><th class="num">Portfolio value</th><th class="num">Profit</th><th class="num">Return on invested</th></tr></thead>
        <tbody>${trs}</tbody></table></div>`;
    }
    function renderConcepts() {
      $("concepts").innerHTML = DATA.concepts.map(c => `
        <details class="concept"><summary>${c.term} — ${c.short}</summary>
        <div class="body">${c.detail}</div></details>`).join("");
    }
    function renderPairs() {
      const lump = +$("lump").value, sip = +$("sip").value, years = +$("years").value;
      const y0 = DATA.plan.start_forecast_year || 2027;
      $("pairlist").innerHTML = PAIRS.map((p,i) => {
        const rk = p.risk;
        return `<div class="pair" data-i="${i}">
          <div class="pair-h"><div>
            <div class="muted">#${i+1} · fit ${rk.fit_score}/100 · ${p.split}/${100-p.split} · overlap ${rk.ov}%</div>
            <b>${p.title}</b><div class="sub" style="margin-top:4px">${p.an} + ${p.bn}</div>
          </div><span><button class="btn-link" data-use="${i}">Edit in builder</button> · <span class="tag">▼ expand</span></span></div>
          <div class="pair-b">
            <p>${p.why}</p>
            <div class="highlight">Base ${p.cagr.base}% → <b>${inr(p.yearly.base[p.yearly.base.length-1]?.value)}</b> after ${years}Y · Bear ${p.cagr.bear}% · Bull ${p.cagr.bull}%</div>
            <div class="tabs" data-pair="${i}">
              <button class="tab on" data-sc="base">Base forecast</button>
              <button class="tab" data-sc="bear">Bear forecast</button>
              <button class="tab" data-sc="bull">Bull forecast</button>
              <button class="tab" data-sc="hist2016">History from 2016</button>
              <button class="tab" data-sc="hist2019">History from 2019</button>
              <button class="tab" data-sc="hist2021">History from 2021</button>
            </div>
            <div class="pair-table" id="pt-${i}"></div>
          </div></div>`;
      }).join("");
      document.querySelectorAll(".pair-h").forEach(h => h.onclick = e => {
        if (e.target.closest(".btn-link")) return;
        const p = h.closest(".pair");
        p.classList.toggle("open");
        if (p.classList.contains("open")) showPairTab(+p.dataset.i, "base");
      });
      document.querySelectorAll("[data-use]").forEach(b => b.onclick = e => {
        e.stopPropagation();
        loadExpert(+b.dataset.use);
      });
      document.querySelectorAll(".tabs[data-pair]").forEach(t => t.onclick = e => {
        const b = e.target.closest(".tab");
        if (!b) return;
        t.querySelectorAll(".tab").forEach(x => x.classList.remove("on"));
        b.classList.add("on");
        showPairTab(+t.dataset.pair, b.dataset.sc);
      });
    }
    function showPairTab(i, sc) {
      const p = PAIRS[i], lump = +$("lump").value, sip = +$("sip").value, years = +$("years").value;
      const y0 = DATA.plan.start_forecast_year || 2027;
      let rows, title;
      const fa = fund(p.a), fb = fund(p.b);
      const blend = p.split/100 * cagrDec(fa) + (1-p.split/100)*cagrDec(fb);
      if (sc === "base") { rows = yearlyProj(blend, lump, sip, years, y0); title = `Base forecast (~${p.cagr.base}% CAGR)`; }
      else if (sc === "bear") { rows = yearlyProj(Math.max(blend-0.04,0.06), lump, sip, years, y0); title = `Bear forecast (~${p.cagr.bear}% CAGR)`; }
      else if (sc === "bull") { rows = yearlyProj(Math.min(blend+0.02,0.22), lump, sip, years, y0); title = `Bull forecast (~${p.cagr.bull}% CAGR)`; }
      else {
        const hy = sc.replace("hist","");
        rows = p.history[hy] || yearlyHist(p.a, p.b, p.split, lump, sip, hy);
        title = `Actual history from ${hy} (real NAV)`;
      }
      $("pt-"+i).innerHTML = tableHtml(rows, title);
    }
    fillCatSelect($("bcatA"));
    fillCatSelect($("bcatB"));
    renderPresets();
    const PK = { lump:"lump", sip:"sip", years:"years", bcatA:"bcatA", bcatB:"bcatB", ba:"ba", bb:"bb", bsplit:"bsplit", bhistStart:"bhistStart" };
    MFDesk.absorbHash(); MFDesk.syncNav();
    MFDesk.restore(PK);
    fillFundSelect($("ba"), $("bcatA").value, $("ba").value);
    fillFundSelect($("bb"), $("bcatB").value, $("bb").value);
    if (!$("ba").value && PRESETS[0]) applyPreset(PRESETS[0].id);
    $("bcatA").onchange = () => { fillFundSelect($("ba"), $("bcatA").value); activePreset=""; document.querySelectorAll(".preset").forEach(el=>el.classList.remove("on")); renderBuilder(); };
    $("bcatB").onchange = () => { fillFundSelect($("bb"), $("bcatB").value); activePreset=""; document.querySelectorAll(".preset").forEach(el=>el.classList.remove("on")); renderBuilder(); };
    ["ba","bb","bsplit","bhistStart"].forEach(id => {
      $(id).addEventListener("change", () => { activePreset=""; document.querySelectorAll(".preset").forEach(el=>el.classList.remove("on")); renderBuilder(); });
      $(id).addEventListener("input", renderBuilder);
    });
    function bindBuilderTabs() {
      const tabs = $("builderTabs");
      if (!tabs) return;
      tabs.onclick = e => {
        const b = e.target.closest(".tab");
        if (!b || !b.dataset.bsc) return;
        e.preventDefault();
        e.stopPropagation();
        builderTab = b.dataset.bsc;
        tabs.querySelectorAll(".tab").forEach(t => t.classList.toggle("on", t === b));
        renderBuilder();
      };
    }
    bindBuilderTabs();
    function refresh() {
      MFDesk.save({ lump:$("lump").value, sip:$("sip").value, years:$("years").value,
        bcatA:$("bcatA").value, bcatB:$("bcatB").value, ba:$("ba").value, bb:$("bb").value,
        bsplit:$("bsplit").value, bhistStart:$("bhistStart").value });
      renderPairs(); renderBuilder();
    }
    ["lump","sip","years"].forEach(id => {
      $(id).addEventListener("input", refresh);
      $(id).addEventListener("change", refresh);
    });
    renderConcepts(); refresh();
    MFDesk.bindScroll("plan");
  </script>
</body>
</html>
"""


def main() -> None:
    html = BODY.replace("__CSS__", CSS).replace("__NAV__", NAV)
    html = html.replace("__DATA__", json.dumps(DATA, ensure_ascii=False, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")
    print("wrote", OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
