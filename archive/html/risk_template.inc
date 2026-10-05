<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>15-year plan · risk &amp; expert pairs</title>
  <style>__CSS__
    .catgrid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .catbox { border: 1px solid var(--line); padding: 10px 12px; background: var(--bg); font-size: 13px; }
    .catbox b { display: block; margin-bottom: 4px; }
    .expert { border: 1px solid var(--line); padding: 14px; margin: 12px 0; background: var(--card); }
    .expert.on { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent-soft); }
    .tag { display: inline-block; font-size: 11px; padding: 2px 8px; border-radius: 999px; background: var(--chip); margin-right: 6px; }
    .tag.ok { background: var(--ok-bg); color: var(--ok); }
    .tag.warn { background: var(--warn-bg); color: var(--warn); }
    .tag.bad { background: var(--bad-bg); color: var(--bad); }
    .scenarios { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 10px; }
    .scenario { background: var(--bg); border: 1px solid var(--line); padding: 10px; text-align: center; }
    .scenario b { display: block; font-size: 17px; }
    .scenario span { font-size: 11px; color: var(--muted); }
    .scenario.bear b { color: var(--bad); }
    .scenario.bull b { color: var(--ok); }
  </style>
</head>
<body>
  <header>
    <div class="wrap" style="padding-top:0;padding-bottom:0">
      <h1>15-year plan · risk &amp; expert pairs</h1>
      <p class="sub">₹3 lakh lumpsum + ₹15,000/month for 15 years. Pick two Direct Growth funds, see overlap, drawdown risk, and what you might have — base, bear, and bull — before tax.</p>
      __NAV__
      <div class="controls" style="margin-top:14px">
        <div>
          <label for="plump">Lumpsum (₹)</label>
          <input id="plump" type="number" min="0" step="50000" value="300000" />
        </div>
        <div>
          <label for="psip">Monthly SIP (₹)</label>
          <input id="psip" type="number" min="0" step="1000" value="15000" />
        </div>
        <div>
          <label for="pyears">Horizon (years)</label>
          <input id="pyears" type="number" min="5" max="25" step="1" value="15" />
        </div>
        <div>
          <label for="psplit">Fund A share (%)</label>
          <input id="psplit" type="number" min="20" max="80" step="5" value="65" />
        </div>
        <div>
          <label for="pa">Fund A</label>
          <select id="pa"></select>
        </div>
        <div>
          <label for="pb">Fund B</label>
          <select id="pb"></select>
        </div>
        <div>
          <label for="q">Search table</label>
          <input id="q" placeholder="e.g. PPFAS, HDFC, mid" />
        </div>
        <div>
          <label for="theme">Theme filter</label>
          <select id="theme">
            <option value="all">All</option>
            <option value="ai">AI / software</option>
            <option value="ev">EV / auto</option>
            <option value="digital">Online / platforms</option>
            <option value="oil">Oil &amp; energy</option>
          </select>
        </div>
      </div>
    </div>
  </header>
  <div class="wrap">
    <div class="warnbox">
      <b>Not financial advice.</b> Forecasts use each fund’s 10Y / 5Y / 3Y rolling return as a proxy. Bear = base minus 4%, bull = base plus 2%. Real 15-year outcomes can be worse (see max drawdown). Direct plan saves TER; tax on withdrawal is the same as Regular.
    </div>

    <div class="panel">
      <h2>What large, mid, small, flexi &amp; multi cap mean</h2>
      <p class="muted">SEBI categories tell you which slice of the market a fund must (or may) buy. For a 15-year two-fund plan, experts usually pair <b>one core</b> (flexi, large, or multi) with <b>one different bucket</b> (mid or small satellite), not two funds that own the same stocks.</p>
      <div class="catgrid" id="catguide"></div>
    </div>

    <div class="panel">
      <h2>Your two-fund plan · risk &amp; forecast</h2>
      <p class="muted">Change funds above or click an expert template below. Risk uses historical volatility, correlation, overlap, and the worst drawdown on the combined portfolio since 2019.</p>
      <div id="planner"></div>
    </div>

    <div class="panel">
      <h2>Combinations a planner would typically suggest</h2>
      <p class="muted">Sorted by fit score: different categories, low overlap, long track record, and reasonable combined Sharpe. These are templates — not buy lists.</p>
      <div id="experts"></div>
    </div>

    <div class="panel">
      <h2>Top 10 funds · theme + quality score</h2>
      <p class="muted">AI, EV, digital, oil barbell plus rolling returns and drawdown. Max two per category; skips high overlap.</p>
      <div class="cards" id="top10"></div>
    </div>

    <div class="panel">
      <h2 id="count">All 50 funds</h2>
      <div style="overflow:auto">
        <table>
          <thead>
            <tr>
              <th>Fund</th><th>Category</th><th class="num">Score</th>
              <th class="num">AI</th><th class="num">EV</th><th class="num">Digital</th><th class="num">Oil</th>
              <th class="num">3Y roll</th><th class="num">Sharpe</th><th class="num">Max DD</th><th class="num">Vol</th>
            </tr>
          </thead>
          <tbody id="tbody"></tbody>
        </table>
      </div>
    </div>
    <div class="panel" id="detail"></div>
    <p class="note">Holdings and theme tags are today’s snapshot. Overlap = sum of min(weight A, weight B) on common stocks. Portfolio vol blends fund volatilities and historical correlation. Educational only.</p>
  </div>
  <script src="desk_common.js"></script>
  <script>
    const DATA = __DATA__;
    const FUNDS = DATA.funds;
    const TOP = DATA.top10;
    const EXPERT = DATA.expert_pairs || [];
    const CATG = DATA.cat_guide || {};
    const CSTATS = DATA.cat_stats || {};
    const HOLD = DATA.holdings || {};
    const NAV = DATA.nav || {};
    const CAT = {
      large_cap: "Large cap", mid_cap: "Mid cap", small_cap: "Small cap",
      multi_cap: "Multi cap", flexi_cap: "Flexi cap", large_mid_cap: "Large & mid",
    };
    const $ = (id) => document.getElementById(id);
    const n = (v, d=1) => (v == null || Number.isNaN(v) ? "—" : Number(v).toFixed(d));
    const inr = (v) => v == null ? "—" : "₹" + Math.round(v).toLocaleString("en-IN");
    const fund = (c) => FUNDS.find(f => f.code === Number(c));
    let view = TOP[0], selExpert = EXPERT[0]?.id || "";

    function cagrDec(f) {
      if (!f) return 0.12;
      for (const k of ["y10","y5","r3","y3"]) {
        if (f[k] != null && f[k] > 0) return f[k] / 100;
      }
      return 0.12;
    }
    function forecast(cagr, lump, sip, years) {
      const m = years * 12, rm = cagr / 12;
      const fvL = lump * Math.pow(1 + rm, m);
      const fvS = rm > 1e-9 ? sip * ((Math.pow(1 + rm, m) - 1) / rm) : sip * m;
      const invested = lump + sip * m;
      return { invested, value: fvL + fvS, gain: fvL + fvS - invested, cagr };
    }
    function overlap(a, b) {
      const ha = HOLD[String(a)] || [], hb = HOLD[String(b)] || [];
      if (!ha.length || !hb.length) return null;
      const wa = {}, wb = {};
      ha.forEach(h => wa[h.k] = (wa[h.k]||0)+h.w);
      hb.forEach(h => wb[h.k] = (wb[h.k]||0)+h.w);
      let ov = 0;
      Object.keys(wa).forEach(k => { if (wb[k]!=null) ov += Math.min(wa[k], wb[k]); });
      return ov;
    }
    function corrFromNav(ca, cb) {
      const sa = NAV[String(ca)]||[], sb = NAV[String(cb)]||[];
      const da = {}, db = {};
      sa.forEach(p => da[p[0]] = p[1]);
      sb.forEach(p => db[p[0]] = p[1]);
      const dates = Object.keys(da).filter(d => db[d]!=null).sort();
      if (dates.length < 24) return 0.7;
      const ra = [], rb = [];
      for (let i = 1; i < dates.length; i++) {
        ra.push(da[dates[i]]/da[dates[i-1]]-1);
        rb.push(db[dates[i]]/db[dates[i-1]]-1);
      }
      const ma = ra.reduce((s,x)=>s+x,0)/ra.length, mb = rb.reduce((s,x)=>s+x,0)/rb.length;
      let num=0,d1=0,d2=0;
      for (let i=0;i<ra.length;i++) {
        const xa=ra[i]-ma, xb=rb[i]-mb;
        num+=xa*xb; d1+=xa*xa; d2+=xb*xb;
      }
      const c = num/Math.sqrt(d1*d2);
      return Number.isNaN(c) ? 0.7 : c;
    }
    function pairRiskLive(fa, fb, splitPct) {
      const w = splitPct/100, w2 = 1-w;
      const ov = overlap(fa.code, fb.code);
      const corr = corrFromNav(fa.code, fb.code);
      const v1 = (fa.vol||15)/100, v2 = (fb.vol||15)/100;
      const portVol = Math.sqrt(w*w*v1*v1 + w2*w2*v2*v2 + 2*w*w2*v1*v2*corr)*100;
      const dd1 = Math.abs(fa.dd||35), dd2 = Math.abs(fb.dd||35);
      const hist = EXPERT.find(e => e.a===fa.code && e.b===fb.code && e.split===splitPct)?.risk
        || EXPERT.find(e => e.a===fb.code && e.b===fa.code && e.split===100-splitPct)?.risk;
      const histDd = hist ? hist.hist_dd : Math.min(w*dd1 + w2*dd2*0.9, 55);
      let band = "Moderate";
      if (fa.cat==="small_cap" || fb.cat==="small_cap" || portVol > 17) band = "Aggressive";
      if (portVol < 14 && !["small_cap","mid_cap"].includes(fa.cat) && !["small_cap","mid_cap"].includes(fb.cat)) band = "Conservative";
      if (fa.cat === fb.cat) band = "Moderate — same category";
      return { ov, corr, portVol, histDd, band };
    }
    function renderCatGuide() {
      $("catguide").innerHTML = Object.keys(CATG).map(k => {
        const g = CATG[k], s = CSTATS[k] || {};
        return `<div class="catbox">
          <b>${g.label || CAT[k]}</b>
          <div>${g.sebi}</div>
          <div class="muted" style="margin-top:6px"><b>Risk:</b> ${g.risk}</div>
          <div class="muted"><b>Role in 15Y plan:</b> ${g.role}</div>
          ${s.n ? `<div class="muted" style="margin-top:6px">Median in this list: roll 3Y ${n(s.r3)}% · vol ${n(s.vol)}% · max DD ${n(s.dd)}%</div>` : ""}
        </div>`;
      }).join("");
    }
    function scenarioHtml(label, cls, fc, pct) {
      return `<div class="scenario ${cls}"><b>${inr(fc.value)}</b><span>${label} · ${n(pct,1)}% CAGR · profit ${inr(fc.gain)}</span></div>`;
    }
    function renderPlanner() {
      const lump = Number($("plump").value||0), sip = Number($("psip").value||0);
      const years = Number($("pyears").value||15), split = Number($("psplit").value||65);
      const fa = fund($("pa").value), fb = fund($("pb").value);
      if (!fa || !fb) return;
      const w = split/100;
      const baseC = w*cagrDec(fa) + (1-w)*cagrDec(fb);
      const bearC = Math.max(baseC-0.04, 0.06), bullC = Math.min(baseC+0.02, 0.22);
      const base = forecast(baseC, lump, sip, years);
      const bear = forecast(bearC, lump, sip, years);
      const bull = forecast(bullC, lump, sip, years);
      const rk = pairRiskLive(fa, fb, split);
      const ovCls = rk.ov>=40?"bad":rk.ov>=20?"warn":"ok";
      const sameCat = fa.cat === fb.cat;
      $("planner").innerHTML = `
        <p><b>${fa.name}</b> (${CAT[fa.cat]}) · ${split}% &nbsp;+&nbsp; <b>${fb.name}</b> (${CAT[fb.cat]}) · ${100-split}%</p>
        <div style="margin:10px 0">
          <span class="tag ${ovCls}">Overlap ${rk.ov==null?"n/a":n(rk.ov,0)+"%"}</span>
          <span class="tag">Corr ${n(rk.corr,2)}</span>
          <span class="tag">Portfolio vol ~${n(rk.portVol,1)}%</span>
          <span class="tag warn">Worst combined DD since 2019 ~${n(rk.histDd,0)}%</span>
          <span class="tag ${rk.band.startsWith("Agg")?"bad":rk.band.startsWith("Cons")?"ok":"warn"}">${rk.band}</span>
          ${sameCat ? `<span class="tag bad">Same category — experts rarely pair two ${CAT[fa.cat]} funds</span>` : ""}
        </div>
        <p class="muted">Total invested over ${years} years: <b>${inr(base.invested)}</b> (${inr(lump)} lumpsum + ${inr(sip)}/month)</p>
        <div class="scenarios">
          ${scenarioHtml("Bear case", "bear", bear, bearC*100)}
          ${scenarioHtml("Base case", "", base, baseC*100)}
          ${scenarioHtml("Bull case", "bull", bull, bullC*100)}
        </div>
        <p class="muted" style="margin-top:10px">Before tax. A 40% crash on paper means ₹${Math.round(base.invested*0.4/100000)}L+ can vanish temporarily — plan to stay invested. Recent SIP units (&lt;12 months) taxed at 20% STCG if you sell.</p>`;
    }
    function renderExperts() {
      $("experts").innerHTML = EXPERT.map(ex => {
        const fa = fund(ex.a), fb = fund(ex.b);
        const fc = ex.forecast, rk = ex.risk;
        const on = selExpert === ex.id ? " on" : "";
        const ovCls = (rk.ov||0)>=40?"bad":(rk.ov||0)>=20?"warn":"ok";
        return `<div class="expert${on}" data-ex="${ex.id}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
            <div>
              <div class="muted">Fit ${n(rk.fit_score,0)}/100 · ${ex.split}/${100-ex.split} split</div>
              <h3 style="margin:6px 0 4px">${ex.title}</h3>
              <p class="muted">${ex.why}</p>
              <p><b>${fa.name}</b> + <b>${fb.name}</b></p>
            </div>
            <button class="chip" data-use="${ex.id}" type="button">Use this pair</button>
          </div>
          <span class="tag ${ovCls}">Overlap ${n(rk.ov,0)}%</span>
          <span class="tag">Sharpe ${n(rk.sh,2)}</span>
          <span class="tag">Vol ${n(rk.port_vol||rk.portVol,1)}%</span>
          <span class="tag warn">Hist DD ${n(rk.hist_dd,0)}%</span>
          <div class="scenarios">
            ${scenarioHtml("Bear", "bear", fc.bear, fc.bear_pct)}
            ${scenarioHtml("Base", "", fc.base, fc.base_pct)}
            ${scenarioHtml("Bull", "bull", fc.bull, fc.bull_pct)}
          </div>
        </div>`;
      }).join("");
    }
    function bar(label, p, cls) {
      const w = Math.max(0, Math.min(100, p || 0));
      return `<div class="bar-row"><span>${label}</span><div class="track"><div class="fill ${cls||""}" style="width:${w}%"></div></div><span class="num">${n(p,1)}%</span></div>`;
    }
    function filtered() {
      const q = ($("q").value||"").trim().toLowerCase();
      const theme = $("theme").value;
      return FUNDS.filter(f => {
        if (theme !== "all" && (f.theme[theme]||0) < 1) return false;
        if (q && !`${f.name} ${f.house}`.toLowerCase().includes(q)) return false;
        return true;
      }).sort((a,b) => (b.fwd||0)-(a.fwd||0));
    }
    function renderTop() {
      $("top10").innerHTML = TOP.map((c,i) => {
        const f = fund(c);
        return `<div class="card"><div class="muted">#${i+1} · ${CAT[f.cat]}</div>
          <h3 style="margin:4px 0">${f.name}</h3>
          ${bar("AI", f.theme.ai)}${bar("EV", f.theme.ev,"ev")}${bar("Digital", f.theme.digital,"dig")}
          <p class="muted">Roll 3Y ${n(f.r3)}% · Sharpe ${n(f.sh,2)} · DD ${n(f.dd)}%</p></div>`;
      }).join("");
    }
    function renderTable() {
      const rows = filtered();
      $("count").textContent = rows.length + " funds";
      $("tbody").innerHTML = rows.map(f => `
        <tr class="${f.code===view?"sel":""}">
          <td><button class="link" data-view="${f.code}">${f.name}</button><div class="muted">${f.house}</div></td>
          <td>${CAT[f.cat]}</td><td class="num">${n(f.fwd,1)}</td>
          <td class="num">${n(f.theme.ai)}</td><td class="num">${n(f.theme.ev)}</td>
          <td class="num">${n(f.theme.digital)}</td><td class="num">${n(f.theme.oil)}</td>
          <td class="num">${n(f.r3)}</td><td class="num">${n(f.sh,2)}</td><td class="num">${n(f.dd)}</td><td class="num">${n(f.vol)}</td>
        </tr>`).join("");
    }
    function renderDetail() {
      const f = fund(view)||FUNDS[0];
      $("detail").innerHTML = `<h2>${f.name}</h2><p class="muted">${f.house} · ${CAT[f.cat]} · score ${n(f.fwd,1)}</p>
        <p class="muted">3Y roll ${n(f.r3)}% · 5Y ${n(f.y5)}% · 10Y ${n(f.y10)}% · Sharpe ${n(f.sh,2)} · vol ${n(f.vol)}% · max DD ${n(f.dd)}% · TER ${n(f.ter,2)}%</p>
        <p class="muted">Large/mid/small in portfolio: ${n(f.l,0)} / ${n(f.m,0)} / ${n(f.sml,0)}%</p>`;
    }
    const opts = FUNDS.map(f => `<option value="${f.code}">${f.name}</option>`).join("");
    $("pa").innerHTML = opts;
    $("pb").innerHTML = opts;
    if (EXPERT[0]) { $("pa").value = EXPERT[0].a; $("pb").value = EXPERT[0].b; $("psplit").value = EXPERT[0].split; }
    else { $("pa").value = 122639; $("pb").value = 118778; }

    const RK_MAP = {
      q:"q", "risk.theme":"theme", plump:"plump", psip:"psip", pyears:"pyears",
      psplit:"psplit", pa:"pa", pb:"pb", "risk.selExpert":"selExpert",
    };
    MFDesk.absorbHash(); MFDesk.syncNav();
    MFDesk.restore(RK_MAP);
    const st = MFDesk.load();
    if (st["risk.selExpert"]) selExpert = st["risk.selExpert"];
    if (st["explorer.view"]) view = Number(st["explorer.view"]);

    function persistRisk() {
      MFDesk.save(Object.assign(MFDesk.load(), {
        q: $("q").value, "risk.theme": $("theme").value,
        plump: $("plump").value, psip: $("psip").value, pyears: $("pyears").value,
        psplit: $("psplit").value, pa: $("pa").value, pb: $("pb").value,
        "risk.selExpert": selExpert,
        lump: $("plump").value, sip: $("psip").value,
      }));
    }
    function refresh() { renderPlanner(); renderExperts(); renderTable(); persistRisk(); }
    ["plump","psip","pyears","psplit","pa","pb","q","theme"].forEach(id => {
      $(id).addEventListener("input", refresh);
      $(id).addEventListener("change", refresh);
    });
    document.getElementById("experts").addEventListener("click", (e) => {
      const u = e.target.closest("[data-use]");
      if (!u) return;
      const ex = EXPERT.find(x => x.id === u.dataset.use);
      if (!ex) return;
      selExpert = ex.id;
      $("pa").value = ex.a; $("pb").value = ex.b; $("psplit").value = ex.split;
      refresh();
    });
    document.addEventListener("click", (e) => {
      const v = e.target.closest("[data-view]");
      if (!v) return;
      view = Number(v.dataset.view);
      MFDesk.save({ "explorer.view": view });
      renderTable(); renderDetail();
    });
    renderCatGuide(); renderTop(); refresh(); renderDetail();
    MFDesk.bindScroll("risk");
  </script>
</body>
</html>
