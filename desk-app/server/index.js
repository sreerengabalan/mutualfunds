import cors from "cors";
import express from "express";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EQ = path.resolve(__dirname, "../../output/equity");
const PORT = process.env.PORT || 4177;
const CLIENT_DIST = path.resolve(__dirname, "../client/dist");

function loadJson(name) {
  return JSON.parse(fs.readFileSync(path.join(EQ, name), "utf8"));
}

const plan = loadJson("plan_detail.json");
const allPairs = loadJson("all_pairs.json");
const fundsByCode = Object.fromEntries(allPairs.funds.map((f) => [String(f.code), f]));

function cagrDec(f) {
  for (const k of ["y10", "y5", "r3", "y3"]) {
    if (f?.[k] > 0) return f[k] / 100;
  }
  return 0.12;
}

function withReal(rows, cpi = 5.5) {
  return rows.map((r, i) => {
    const yrs = i + 1;
    const real = r.value / Math.pow(1 + cpi / 100, yrs);
    return { ...r, real: Math.round(real), realProfit: Math.round(real - r.invested) };
  });
}

function yearlyProj(cagr, lump, sip, years, y0 = 2027, cpi = 5.5) {
  const rm = Math.pow(1 + cagr, 1 / 12) - 1;
  let val = lump;
  let inv = lump;
  let sipYr = 0;
  const rows = [];
  for (let m = 1; m <= years * 12; m++) {
    if (m > 1) {
      val = val * (1 + rm) + sip;
      inv += sip;
      sipYr += sip;
    }
    if (m % 12 === 0) {
      rows.push({
        y: y0 + m / 12 - 1,
        added: Math.round(rows.length ? sipYr : lump),
        invested: Math.round(inv),
        value: Math.round(val),
        profit: Math.round(val - inv),
        ret: +(((val - inv) / inv) * 100).toFixed(1),
      });
      sipYr = 0;
    }
  }
  return withReal(rows, cpi);
}

function yearlyHist(ca, cb, split, lump, sip, startYear) {
  const start = startYear === "2019" ? "2019-02-01" : `${startYear}-01-01`;
  const nav = plan.nav || {};
  const da = {};
  const db = {};
  (nav[String(ca)] || []).forEach((p) => {
    if (p[0] >= start) da[p[0]] = p[1];
  });
  (nav[String(cb)] || []).forEach((p) => {
    if (p[0] >= start) db[p[0]] = p[1];
  });
  const dates = Object.keys(da)
    .filter((d) => db[d] != null)
    .sort();
  if (dates.length < 6) return [];
  const w1 = split / 100;
  const w2 = 1 - w1;
  let ua = (lump * w1) / da[dates[0]];
  let ub = (lump * w2) / db[dates[0]];
  let inv = lump;
  let sipYr = 0;
  const rows = [];
  dates.forEach((d, i) => {
    if (i > 0) {
      ua += (sip * w1) / da[d];
      ub += (sip * w2) / db[d];
      inv += sip;
      sipYr += sip;
    }
    const val = ua * da[d] + ub * db[d];
    const nxt = dates[i + 1];
    if (!nxt || nxt.slice(0, 4) !== d.slice(0, 4)) {
      rows.push({
        y: +d.slice(0, 4),
        added: Math.round(rows.length ? sipYr : lump),
        invested: Math.round(inv),
        value: Math.round(val),
        profit: Math.round(val - inv),
        ret: +(((val - inv) / inv) * 100).toFixed(1),
      });
      sipYr = 0;
    }
  });
  return withReal(rows, allPairs.inflation?.long_term_avg || 5.5);
}

function overlapDetail(a, b) {
  const ha = plan.holdings?.[String(a)] || [];
  const hb = plan.holdings?.[String(b)] || [];
  if (!ha.length || !hb.length) return null;
  const wa = {};
  const wb = {};
  const names = {};
  ha.forEach((h) => {
    wa[h.k] = (wa[h.k] || 0) + h.w;
    names[h.k] = h.n;
  });
  hb.forEach((h) => {
    wb[h.k] = (wb[h.k] || 0) + h.w;
    names[h.k] = names[h.k] || h.n;
  });
  const common = [];
  let ov = 0;
  Object.keys(wa).forEach((k) => {
    if (wb[k] == null) return;
    const m = Math.min(wa[k], wb[k]);
    ov += m;
    common.push({ n: names[k], a: wa[k], b: wb[k], m });
  });
  common.sort((x, y) => y.m - x.m);
  return { ov, common, na: ha.length, nb: hb.length };
}

const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/health", (_req, res) => res.json({ ok: true }));

app.get("/api/meta", (_req, res) => {
  res.json({
    plan: allPairs.plan,
    n_funds: allPairs.n_funds,
    n_pairs: allPairs.n_pairs,
    concepts: plan.concepts,
    cat_guide: plan.cat_guide,
    cat_stats: plan.cat_stats,
    combo_presets: plan.combo_presets,
    expert_pairs: plan.expert_pairs?.map((p) => ({
      id: p.id,
      title: p.title,
      why: p.why,
      a: p.a,
      b: p.b,
      an: p.an,
      bn: p.bn,
      ac: p.ac,
      bc: p.bc,
      split: p.split,
      cagr: p.cagr,
      risk: {
        ov: p.risk?.ov,
        fit_score: p.risk?.fit_score,
        hist_dd: p.risk?.hist_dd,
        port_vol: p.risk?.port_vol,
        corr: p.risk?.corr,
      },
      forecast_end: p.yearly?.base?.[p.yearly.base.length - 1],
    })),
    inflation: allPairs.inflation,
    hist_starts: plan.hist_starts,
    sources: {
      nav: {
        name: "mfapi.in",
        url: "https://api.mfapi.in/mf/{schemeCode}",
        check: "AMFI daily NAV republished as a public JSON API. Month-end last NAV is used for history.",
      },
      universe: {
        name: "AMFI NAVAll.txt",
        url: "https://www.amfiindia.com/spages/NAVAll.txt",
        check: "Official scheme codes, latest NAV, and SEBI category.",
      },
      holdings: {
        name: "Groww scheme portfolio",
        url: "https://groww.in/mutual-funds",
        check: "Stock weights for overlap. Cross-check on AMC factsheet / Value Research / Morningstar.",
      },
      inflation: {
        name: "India CPI (planning averages)",
        url: "https://www.mospi.gov.in/",
        check: "MoSPI CPI; RBI also publishes. Our yearly % are planning averages, not official monthly prints.",
      },
      verify_nav: "https://www.amfiindia.com/net-asset-value/nav-history",
      verify_scheme: "https://www.amfiindia.com/research-information/other-data/scheme-details",
    },
  });
});

app.get("/api/funds", (_req, res) => {
  res.json(allPairs.funds);
});

app.get("/api/funds/:code", (req, res) => {
  const f = fundsByCode[String(req.params.code)];
  if (!f) return res.status(404).json({ error: "Fund not found" });
  const code = String(f.code);
  const holdings = plan.holdings?.[code] || [];
  const themes = plan.themes?.[code] || null;
  const nav = plan.nav?.[code] || [];
  const related = allPairs.pairs
    .filter((p) => String(p.a) === code || String(p.b) === code)
    .slice(0, 12)
    .map((p) => ({
      a: p.a,
      b: p.b,
      an: p.an,
      bn: p.bn,
      ac: p.ac,
      bc: p.bc,
      split: p.split,
      ov: p.ov,
      score: p.score,
      rank: p.rank,
      forecast: p.forecast?.value,
      hist_cagr: p.hist?.cagr,
    }));
  res.json({
    ...f,
    holdings,
    themes,
    nav,
    related,
    cat_guide: plan.cat_guide?.[f.cat] || null,
    sources: {
      mfapi: `https://api.mfapi.in/mf/${f.code}`,
      amfi_nav: "https://www.amfiindia.com/net-asset-value/nav-history",
    },
  });
});

app.get("/api/pairs", (req, res) => {
  const {
    catA,
    catB,
    maxOv = "35",
    minHistYrs = "5",
    differentCats = "1",
    q = "",
    limit = "80",
    sort = "score",
  } = req.query;

  let rows = allPairs.pairs;
  const ovMax = Number(maxOv);
  const minYrs = Number(minHistYrs);
  const query = String(q).toLowerCase().trim();

  if (differentCats === "1") rows = rows.filter((p) => p.ac !== p.bc);
  if (catA) rows = rows.filter((p) => p.ac === catA || p.bc === catA);
  if (catB && catA) {
    rows = rows.filter(
      (p) =>
        (p.ac === catA && p.bc === catB) || (p.ac === catB && p.bc === catA)
    );
  } else if (catB) {
    rows = rows.filter((p) => p.ac === catB || p.bc === catB);
  }
  if (!Number.isNaN(ovMax)) rows = rows.filter((p) => p.ov == null || p.ov <= ovMax);
  if (!Number.isNaN(minYrs)) rows = rows.filter((p) => (p.hist?.yrs || 0) >= minYrs);
  if (query) {
    rows = rows.filter(
      (p) =>
        p.an.toLowerCase().includes(query) ||
        p.bn.toLowerCase().includes(query) ||
        p.ah.toLowerCase().includes(query) ||
        p.bh.toLowerCase().includes(query)
    );
  }

  const sortKey = String(sort);
  rows = [...rows].sort((a, b) => {
    if (sortKey === "forecast") return (b.forecast?.value || 0) - (a.forecast?.value || 0);
    if (sortKey === "hist") return (b.hist?.cagr || 0) - (a.hist?.cagr || 0);
    if (sortKey === "ov") return (a.ov || 99) - (b.ov || 99);
    return (b.score || 0) - (a.score || 0);
  });

  const lim = Math.min(Number(limit) || 80, 300);
  res.json({ total: rows.length, pairs: rows.slice(0, lim) });
});

app.get("/api/compare", (req, res) => {
  const a = Number(req.query.a);
  const b = Number(req.query.b);
  const split = Number(req.query.split || 65);
  const lump = Number(req.query.lump || allPairs.plan.lump);
  const sip = Number(req.query.sip || allPairs.plan.sip);
  const years = Number(req.query.years || allPairs.plan.years);
  const histStart = String(req.query.histStart || "2016");

  const fa = fundsByCode[String(a)];
  const fb = fundsByCode[String(b)];
  if (!fa || !fb) return res.status(404).json({ error: "Pick two valid funds" });

  const cpi = Number(allPairs.inflation?.long_term_avg || 5.5);
  const base = (split / 100) * cagrDec(fa) + (1 - split / 100) * cagrDec(fb);
  const bear = Math.max(base - 0.04, 0.06);
  const bull = Math.min(base + 0.02, 0.22);
  const ov = overlapDetail(a, b);
  const yearly = {
    base: yearlyProj(base, lump, sip, years, 2027, cpi),
    bear: yearlyProj(bear, lump, sip, years, 2027, cpi),
    bull: yearlyProj(bull, lump, sip, years, 2027, cpi),
    history: yearlyHist(a, b, split, lump, sip, histStart),
  };

  res.json({
    a: { ...fa, holdings: plan.holdings?.[String(a)] || [], themes: plan.themes?.[String(a)] },
    b: { ...fb, holdings: plan.holdings?.[String(b)] || [], themes: plan.themes?.[String(b)] },
    split,
    amounts: { lump, sip, years, invested: Math.round(lump + sip * years * 12) },
    overlap: ov,
    cagr: {
      base: +(base * 100).toFixed(2),
      bear: +(bear * 100).toFixed(2),
      bull: +(bull * 100).toFixed(2),
      real_base: +(Math.max(base * 100 - cpi, 0)).toFixed(2),
    },
    yearly,
    inflation: allPairs.inflation,
  });
});

app.get("/api/inflation", (_req, res) => {
  res.json(allPairs.inflation);
});

if (fs.existsSync(CLIENT_DIST)) {
  app.use(express.static(CLIENT_DIST));
  app.get("*", (req, res, next) => {
    if (req.path.startsWith("/api")) return next();
    res.sendFile(path.join(CLIENT_DIST, "index.html"));
  });
}

app.listen(PORT, () => {
  console.log(`MF Desk API http://localhost:${PORT}`);
  console.log(`Funds ${allPairs.n_funds} · pairs ${allPairs.n_pairs}`);
});
