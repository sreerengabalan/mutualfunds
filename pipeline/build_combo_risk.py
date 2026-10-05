"""Build 2019–today pair stats and theme/risk scores for the two analysis pages."""
from __future__ import annotations

import json
import math
import re
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EQ = ROOT / "output" / "equity"
RF = 0.065
START = "2019-02-01"

THEME_PATTERNS: dict[str, list[str]] = {
    "ai": [
        r"infosys", r"tata consultancy", r"\btcs\b", r"hcl technolog", r"\bwipro\b",
        r"tech mahindra", r"persistent", r"coforge", r"l&t technology", r"ltts",
        r"mphasis", r"ltimindtree", r"mindtree", r"cyient", r"tata elxsi", r"kpit",
        r"happiest minds", r"hexaware", r"birlasoft", r"zensar", r"sonata software",
        r"eclerx", r"firstsource", r"tata technologies", r"netweb", r"dixon",
        r"kaynes", r"syrma", r"nvidia", r"microsoft", r"alphabet", r"google",
        r"facebook", r"\bmeta\b", r"amazon", r"oracle", r"salesforce", r"adobe",
        r"broadcom", r"taiwan semi", r"\btsmc\b", r"\basml\b", r"\bintel\b", r"\bamd\b",
        r"newgen", r"intellect design", r"mapmyindia", r"c\.e\. info", r"latentsight",
        r"afcons", r"larsen toubro infotech", r"\blti\b",
    ],
    "ev": [
        r"tata motors", r"mahindra mahindra", r"maruti", r"hyundai", r"bajaj auto",
        r"tvs motor", r"hero motocorp", r"eicher", r"ashok leyland", r"\bbosch\b",
        r"sona blw", r"sona comstar", r"uno minda", r"motherson", r"samvardhana",
        r"bharat forge", r"endurance", r"varroc", r"craftsman", r"exide",
        r"amara raja", r"olectra", r"jbm auto", r"cg power", r"tube investments",
        r"schaeffler", r"skf india", r"sundram fast", r"lumax", r"suprajit",
        r"rolex rings", r"happy forging", r"belrise", r"pricol", r"sjs enterprises",
        r"mahindra cie", r"cie automotive", r"uno minda", r"sundaram clayton",
        r"bharat electronics",
    ],
    "digital": [
        r"zomato", r"eternal", r"swiggy", r"fsn e commerce", r"nykaa", r"pb fintech",
        r"policybazaar", r"paytm", r"one 97", r"info edge", r"affle", r"nazara",
        r"delhivery", r"irctc", r"indian railway catering", r"bharti airtel",
        r"indus towers", r"\bjio\b", r"\bbse\b", r"central depository", r"cdsl",
        r"angel one", r"computer age", r"lenskart", r"indiamart", r"just dial",
        r"cartrade", r"interglobe", r"makemytrip", r"indian energy exchange",
        r"hdfc amc", r"nippon life india asset", r"icici prudential asset",
        r"multi commodity", r"\bmcx\b", r"cms info", r"route mobile", r"tanla",
        r"intellect", r"pb fintech", r"one97",
    ],
    "oil": [
        r"reliance industries", r"oil natural gas", r"\bongc\b", r"oil india",
        r"bharat petroleum", r"hindustan petroleum", r"indian oil", r"\bgail\b",
        r"petronet", r"indraprastha gas", r"mahanagar gas", r"gujarat gas",
        r"coal india", r"\bntpc\b", r"power grid", r"tata power", r"adani power",
        r"adani energy", r"adani green", r"aegis", r"castrol", r"mangalore refinery",
        r"chennai petroleum", r"gulf oil", r"petronet lng", r"gujarat state petronet",
        r"torrent power", r"jsw energy", r"\bnhpc\b", r"\bsjvn\b", r"oil india",
        r"hindustan oil exploration", r"reliance",
    ],
}

COMPILED = {
    k: [re.compile(p) for p in pats]
    for k, pats in THEME_PATTERNS.items()
}


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9.&]+", " ", s.lower())).strip()


def match_themes(name: str) -> list[str]:
    n = norm(name)
    hits = []
    for theme, pats in COMPILED.items():
        if any(p.search(n) for p in pats):
            hits.append(theme)
    # Reliance is oil + digital (Jio/retail), not a pure software name.
    if "reliance industries" in n:
        hits = [t for t in hits if t != "ai"]
        if "digital" not in hits:
            hits.append("digital")
        if "oil" not in hits:
            hits.append("oil")
    return hits


def theme_scores(holdings: list[dict]) -> dict:
    w = {k: 0.0 for k in THEME_PATTERNS}
    names = {k: [] for k in THEME_PATTERNS}
    for h in holdings:
        themes = match_themes(h.get("n") or h.get("k") or "")
        wt = float(h.get("w") or 0)
        for t in themes:
            w[t] += wt
            names[t].append({"n": h["n"], "w": wt})
    for t in names:
        names[t].sort(key=lambda x: -x["w"])
        names[t] = names[t][:8]
    transform = w["ai"] + w["ev"] + w["digital"]
    return {
        "ai": round(w["ai"], 2),
        "ev": round(w["ev"], 2),
        "digital": round(w["digital"], 2),
        "oil": round(w["oil"], 2),
        "transform": round(transform, 2),
        "names": names,
    }


def overlap(ha: list[dict], hb: list[dict]) -> float | None:
    if not ha or not hb:
        return None
    wa, wb = {}, {}
    for h in ha:
        wa[h["k"]] = wa.get(h["k"], 0) + h["w"]
    for h in hb:
        wb[h["k"]] = wb.get(h["k"], 0) + h["w"]
    return round(sum(min(wa[k], wb[k]) for k in wa if k in wb), 2)


def monthly_nav(codes: list[int]) -> dict[str, list]:
    hist = pd.read_csv(EQ / "nav_history.csv", parse_dates=["date"])
    hist = hist[hist["scheme_code"].isin(codes)]
    hist = hist[hist["date"] >= START]
    out: dict[str, list] = {}
    for code, g in hist.groupby("scheme_code"):
        g = g.sort_values("date").set_index("date")
        m = g["nav"].resample("ME").last().dropna()
        out[str(int(code))] = [
            [d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in m.items()
        ]
    return out


def path_stats(values: np.ndarray, invested: float, years: float) -> dict:
    if len(values) < 3 or invested <= 0 or years <= 0:
        return {}
    rets = values[1:] / values[:-1] - 1
    vol = float(np.std(rets, ddof=1) * math.sqrt(12)) if len(rets) > 1 else None
    peak = np.maximum.accumulate(values)
    dd = float((values / peak - 1).min())
    fv = float(values[-1])
    cagr = (fv / invested) ** (1 / years) - 1 if fv > 0 else None
    mean_ann = float(np.mean(rets) * 12) if len(rets) else None
    sharpe = (mean_ann - RF) / vol if vol and vol > 0 and mean_ann is not None else None
    return {
        "value": round(fv, 0),
        "invested": round(invested, 0),
        "gain": round(fv - invested, 0),
        "abs": round(fv / invested - 1, 4),
        "cagr": None if cagr is None else round(cagr, 4),
        "vol": None if vol is None else round(vol, 4),
        "dd": round(dd, 4),
        "sh": None if sharpe is None else round(sharpe, 3),
        "yrs": round(years, 2),
    }


def align(a: list, b: list) -> tuple[np.ndarray, np.ndarray, list[str]]:
    da = {d: v for d, v in a}
    db = {d: v for d, v in b}
    dates = sorted(set(da) & set(db))
    if not dates:
        return np.array([]), np.array([]), []
    return (
        np.array([da[d] for d in dates], dtype=float),
        np.array([db[d] for d in dates], dtype=float),
        dates,
    )


def sim_pair(na: list, nb: list, lump: float, sip: float, split: float) -> dict | None:
    va, vb, dates = align(na, nb)
    if len(dates) < 24:
        return None
    years = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days / 365.25
    ua = lump * split / va[0]
    ub = lump * (1 - split) / vb[0]
    invested = lump
    path = np.empty(len(dates))
    for i in range(len(dates)):
        if sip > 0:
            ua += sip * split / va[i]
            ub += sip * (1 - split) / vb[i]
            invested += sip
        path[i] = ua * va[i] + ub * vb[i]
    st = path_stats(path, invested, years)
    if not st:
        return None
    ra = va[1:] / va[:-1] - 1
    rb = vb[1:] / vb[:-1] - 1
    corr = float(np.corrcoef(ra, rb)[0, 1]) if len(ra) > 2 else None
    st["corr"] = None if corr is None or math.isnan(corr) else round(corr, 3)
    st["start"] = dates[0]
    st["end"] = dates[-1]
    return st


def sim_one(series: list, lump: float, sip: float) -> dict | None:
    if len(series) < 24:
        return None
    dates = [p[0] for p in series]
    nav = np.array([p[1] for p in series], dtype=float)
    years = (pd.Timestamp(dates[-1]) - pd.Timestamp(dates[0])).days / 365.25
    units = lump / nav[0]
    invested = lump
    path = np.empty(len(nav))
    for i in range(len(nav)):
        if sip > 0:
            units += sip / nav[i]
            invested += sip
        path[i] = units * nav[i]
    st = path_stats(path, invested, years)
    if not st:
        return None
    st["start"] = dates[0]
    st["end"] = dates[-1]
    return st


def norm_rank(vals: list[float | None], reverse: bool = False) -> list[float]:
    xs = [v for v in vals if v is not None]
    if not xs:
        return [0.0] * len(vals)
    lo, hi = min(xs), max(xs)
    span = hi - lo or 1.0
    out = []
    for v in vals:
        if v is None:
            out.append(0.0)
            continue
        s = (v - lo) / span
        out.append(1 - s if reverse else s)
    return out


def forward_scores(funds: list[dict], themes: dict, holdings: dict) -> None:
    r3 = [f.get("r3") for f in funds]
    sh = [f.get("sh") for f in funds]
    dd = [abs(f["dd"]) if f.get("dd") is not None else None for f in funds]
    ter = [f.get("ter") for f in funds]
    aum = [math.log10(max(f.get("aum") or 1, 1)) for f in funds]
    nr3, nsh, ndd, nter, naum = (
        norm_rank(r3),
        norm_rank(sh),
        norm_rank(dd, reverse=True),
        norm_rank(ter, reverse=True),
        norm_rank(aum),
    )
    cat_w = {
        "flexi_cap": 1.0,
        "multi_cap": 0.95,
        "large_mid_cap": 0.92,
        "mid_cap": 0.88,
        "large_cap": 0.82,
        "small_cap": 0.72,
    }
    for i, f in enumerate(funds):
        t = themes[str(f["code"])]
        def cap(x: float) -> float:
            return min(x / 22.0, 1.0)

        theme_fit = 0.30 * cap(t["ai"]) + 0.25 * cap(t["ev"]) + 0.25 * cap(t["digital"]) + 0.20 * cap(t["oil"])
        # Barbell: reward having both transformation and oil, not only one.
        barbell = min(cap(t["transform"]), 1.0) * 0.7 + min(cap(t["oil"]) + 0.15, 1.0) * 0.3
        quality = 0.40 * nr3[i] + 0.30 * nsh[i] + 0.20 * ndd[i] + 0.10 * nter[i]
        score = 100 * (0.34 * theme_fit + 0.16 * barbell + 0.32 * quality + 0.10 * naum[i] + 0.08 * cat_w.get(f["cat"], 0.8))
        f["theme"] = {k: t[k] for k in ("ai", "ev", "digital", "oil", "transform")}
        f["fwd"] = round(score, 1)
        f["theme_names"] = t["names"]

    ranked = sorted(funds, key=lambda x: -x["fwd"])
    picked: list[dict] = []
    per_cat: dict[str, int] = {}
    for f in ranked:
        if len(picked) >= 10:
            break
        cap = 1 if f["cat"] == "small_cap" else 2
        if per_cat.get(f["cat"], 0) >= cap:
            continue
        if (f["theme"]["transform"] + f["theme"]["oil"]) < 12:
            continue
        ha = holdings.get(str(f["code"])) or []
        too_close = False
        for p in picked:
            ov = overlap(ha, holdings.get(str(p["code"])) or [])
            if ov is not None and ov >= 38:
                too_close = True
                break
        if too_close:
            continue
        picked.append(f)
        per_cat[f["cat"]] = per_cat.get(f["cat"], 0) + 1
    # If greedy left gaps, fill by score ignoring category cap but still overlap.
    if len(picked) < 10:
        have = {p["code"] for p in picked}
        for f in ranked:
            if len(picked) >= 10:
                break
            if f["code"] in have:
                continue
            ha = holdings.get(str(f["code"])) or []
            if any((overlap(ha, holdings.get(str(p["code"])) or []) or 0) >= 42 for p in picked):
                continue
            picked.append(f)
    return [p["code"] for p in picked]


EXPERT_TEMPLATES = [
    {
        "id": "core_satellite",
        "title": "Core + satellite (most common expert split)",
        "a": 122639,
        "b": 118778,
        "split": 70,
        "why": "One flexi core (PPFAS: India + global, low turnover) plus one small-cap satellite for long-term alpha. Different cap buckets; overlap usually low.",
    },
    {
        "id": "dual_core",
        "title": "Two cores, different styles",
        "a": 122639,
        "b": 118955,
        "split": 50,
        "why": "PPFAS (quality + foreign) and HDFC Flexi (India banks/industrials). Experts use this when you want two flexi names that behave differently — but check overlap (~32% historically).",
    },
    {
        "id": "stable_growth",
        "title": "Stable + growth (lower sleep loss)",
        "a": 120586,
        "b": 118989,
        "split": 60,
        "why": "Large-cap anchor (ICICI Bluechip) + mid-cap engine (HDFC Mid). Classic 60/40 for 15 years: smoother than two aggressive funds.",
    },
    {
        "id": "transformation",
        "title": "Transformation + ballast",
        "a": 149185,
        "b": 119598,
        "split": 65,
        "why": "Kotak Multicap (flexible across caps) + SBI Large Cap (quality large names, some energy). Fits AI/EV/online theme without betting everything on small caps.",
    },
    {
        "id": "single_amc_avoid",
        "title": "Multi-cap + flexi (low overlap)",
        "a": 148990,
        "b": 118834,
        "split": 55,
        "why": "ICICI Flexicap (EV-heavy book) + Mirae Large & Mid (digital/industrial). Different categories and managers; overlap typically under 25%.",
    },
]

CAT_GUIDE = {
    "large_cap": {
        "label": "Large cap",
        "sebi": "Top 100 stocks by market cap (Nifty 100-ish universe).",
        "risk": "Lowest volatility in equity; drawdowns ~35–40% in crashes.",
        "role": "Anchor / core — use when you want smoother 15-year ride.",
    },
    "mid_cap": {
        "label": "Mid cap",
        "sebi": "101st–250th stocks (Nifty Midcap 150 band).",
        "risk": "Higher vol than large; can lag for years then catch up.",
        "role": "Growth engine — 20–40% of a long portfolio, not 100%.",
    },
    "small_cap": {
        "label": "Small cap",
        "sebi": "251st stock onward (outside top 250).",
        "risk": "Highest vol; 45–50% drawdowns are normal. Liquidity risk in stress.",
        "role": "Satellite only — 10–25% for 15+ year horizon if you can hold through pain.",
    },
    "flexi_cap": {
        "label": "Flexi cap",
        "sebi": "Fund manager chooses across large, mid, and small with no fixed band.",
        "risk": "Depends on how the manager runs it — many flexi funds are large-heavy.",
        "role": "One-stop core — good as primary fund if overlap with second fund is low.",
    },
    "multi_cap": {
        "label": "Multi cap",
        "sebi": "Must invest at least 25% each in large, mid, and small (SEBI rule).",
        "risk": "Balanced by mandate; still equity risk.",
        "role": "Structured all-cap exposure — alternative to flexi + mid/small pair.",
    },
    "large_mid_cap": {
        "label": "Large & mid cap",
        "sebi": "Large + mid only; no small-cap mandate.",
        "risk": "Between large and mid; less wild than pure mid/small.",
        "role": "Middle ground core when you do not want small-cap satellite.",
    },
}


def pair_risk(
    fa: dict,
    fb: dict,
    nav_a: list,
    nav_b: list,
    holdings: dict,
    split: float,
    lump: float,
    sip: float,
) -> dict | None:
    st = sim_pair(nav_a, nav_b, lump, sip, split)
    if not st:
        return None
    ov = overlap(holdings.get(str(fa["code"])) or [], holdings.get(str(fb["code"])) or [])
    va, vb, _ = align(nav_a, nav_b)
    if len(va) < 24:
        return None
    ra = va[1:] / va[:-1] - 1
    rb = vb[1:] / vb[:-1] - 1
    corr = float(np.corrcoef(ra, rb)[0, 1]) if len(ra) > 2 else 0.0
    if math.isnan(corr):
        corr = 0.0
    w1, w2 = split, 1 - split
    v1 = (fa.get("vol") or 15) / 100
    v2 = (fb.get("vol") or 15) / 100
    port_vol = math.sqrt(w1 * w1 * v1 * v1 + w2 * w2 * v2 * v2 + 2 * w1 * w2 * v1 * v2 * corr)
    dd1 = abs(fa.get("dd") or 35)
    dd2 = abs(fb.get("dd") or 35)
    # Combined drawdown estimate: not additive; use historical pair DD when available.
    est_dd = min(abs(st["dd"]) * 100, w1 * dd1 + w2 * dd2 * 0.85)
    score = 0.0
    if fa["cat"] != fb["cat"]:
        score += 25
    if ov is not None and ov < 25:
        score += 25
    elif ov is not None and ov < 35:
        score += 12
    if st.get("sh"):
        score += min(st["sh"] * 20, 20)
    if (fa.get("yrs") or 0) >= 10 and (fb.get("yrs") or 0) >= 10:
        score += 15
    if (fa.get("aum") or 0) > 5000 and (fb.get("aum") or 0) > 3000:
        score += 10
    return {
        **st,
        "ov": ov,
        "corr": st.get("corr"),
        "port_vol": round(port_vol * 100, 2),
        "est_dd": round(est_dd, 1),
        "hist_dd": round(abs(st["dd"]) * 100, 1),
        "fit_score": round(min(score, 100), 0),
    }


def cagr_pct(f: dict) -> float | None:
    for k in ("y10", "y5", "r3", "y3"):
        v = f.get(k)
        if v is not None and v > 0:
            return float(v) / 100
    return None


def forecast_15y(cagr: float, lump: float, sip: float, years: int = 15) -> dict:
    """Future value of lump + monthly SIP at given annual CAGR."""
    months = years * 12
    rm = cagr / 12
    fv_lump = lump * ((1 + rm) ** months) if rm else lump
    fv_sip = sip * (((1 + rm) ** months - 1) / rm) if rm > 1e-9 else sip * months
    invested = lump + sip * months
    fv = fv_lump + fv_sip
    return {
        "invested": round(invested),
        "value": round(fv),
        "gain": round(fv - invested),
        "cagr": round(cagr, 4),
    }


def pair_forecast_15y(fa: dict, fb: dict, split: float, lump: float, sip: float) -> dict:
    ca, cb = cagr_pct(fa), cagr_pct(fb)
    base = (split * (ca or 0.12) + (1 - split) * (cb or 0.12)) if (ca or cb) else 0.12
    bear = max(base - 0.04, 0.06)
    bull = min(base + 0.02, 0.22)
    return {
        "base": forecast_15y(base, lump, sip),
        "bear": forecast_15y(bear, lump, sip),
        "bull": forecast_15y(bull, lump, sip),
        "base_pct": round(base * 100, 2),
        "bear_pct": round(bear * 100, 2),
        "bull_pct": round(bull * 100, 2),
    }


def category_stats(funds: list[dict]) -> dict:
    out = {}
    for cat in CAT_GUIDE:
        rows = [f for f in funds if f.get("cat") == cat]
        if not rows:
            continue
        def med(key):
            xs = [f[key] for f in rows if f.get(key) is not None]
            return round(float(np.median(xs)), 2) if xs else None

        out[cat] = {
            "n": len(rows),
            "r3": med("r3"),
            "vol": med("vol"),
            "dd": med("dd"),
            "sh": med("sh"),
        }
    return out


def build_expert_pairs(funds: list[dict], nav: dict, holdings: dict, lump: float, sip: float) -> list[dict]:
    by_code = {f["code"]: f for f in funds}
    out = []
    for tpl in EXPERT_TEMPLATES:
        fa, fb = by_code.get(tpl["a"]), by_code.get(tpl["b"])
        if not fa or not fb:
            continue
        split = tpl["split"] / 100
        risk = pair_risk(fa, fb, nav.get(str(fa["code"]), []), nav.get(str(fb["code"]), []), holdings, split, lump, sip)
        if not risk:
            continue
        fc = pair_forecast_15y(fa, fb, split, lump, sip)
        out.append(
            {
                "id": tpl["id"],
                "title": tpl["title"],
                "why": tpl["why"],
                "a": fa["code"],
                "b": fb["code"],
                "split": tpl["split"],
                "risk": risk,
                "forecast": fc,
            }
        )
    out.sort(key=lambda x: -x["risk"].get("fit_score", 0))
    return out


def main() -> None:
    funds = json.loads((EQ / "selected_50.json").read_text(encoding="utf-8"))
    whatif = json.loads((EQ / "whatif_data.json").read_text(encoding="utf-8"))
    holdings = whatif["holdings"]
    codes = [int(f["code"]) for f in funds]
    nav = monthly_nav(codes)
    themes = {str(c): theme_scores(holdings.get(str(c)) or []) for c in codes}

    lump, sip, split = 300000.0, 15000.0, 0.6
    singles = {}
    eligible = []
    for f in funds:
        code = str(f["code"])
        series = nav.get(code) or []
        first = series[0][0] if series else None
        f["nav_from"] = first
        f["has_2019"] = bool(first and first <= "2019-03-31")
        st = sim_one(series, lump, sip) if f["has_2019"] else None
        singles[code] = st
        if f["has_2019"]:
            eligible.append(f)

    pairs = []
    for a, b in combinations(eligible, 2):
        st = sim_pair(nav[str(a["code"])], nav[str(b["code"])], lump, sip, split)
        if not st:
            continue
        ov = overlap(holdings.get(str(a["code"])) or [], holdings.get(str(b["code"])) or [])
        pairs.append(
            {
                "a": a["code"],
                "b": b["code"],
                "ov": ov,
                "cagr": st["cagr"],
                "abs": st["abs"],
                "vol": st["vol"],
                "dd": st["dd"],
                "sh": st["sh"],
                "corr": st["corr"],
                "value": st["value"],
                "invested": st["invested"],
                "gain": st["gain"],
                "start": st["start"],
                "end": st["end"],
            }
        )
    pairs.sort(key=lambda p: -(p["cagr"] or -99))

    top10 = forward_scores(funds, themes, holdings)
    expert_pairs = build_expert_pairs(funds, nav, holdings, lump, sip)
    cat_stats = category_stats(funds)

    slim_funds = []
    for f in funds:
        slim_funds.append(
            {
                "code": f["code"],
                "name": f["name"],
                "house": f["house"],
                "cat": f["cat"],
                "aum": f.get("aum"),
                "ter": f.get("ter"),
                "y3": f.get("y3"),
                "y5": f.get("y5"),
                "y10": f.get("y10"),
                "r3": f.get("r3"),
                "vol": f.get("vol"),
                "dd": f.get("dd"),
                "sh": f.get("sh"),
                "l": f.get("l"),
                "m": f.get("m"),
                "sml": f.get("sml"),
                "has_2019": f["has_2019"],
                "nav_from": f["nav_from"],
                "fwd": f["fwd"],
                "theme": f["theme"],
                "theme_names": f["theme_names"],
            }
        )

    payload = {
        "start": START,
        "end": "2026-08-11",
        "lump": lump,
        "sip": sip,
        "split": split,
        "eligible": len(eligible),
        "funds": slim_funds,
        "nav": nav,
        "singles": singles,
        "pairs": pairs,
        "top10": top10,
        "expert_pairs": expert_pairs,
        "cat_guide": CAT_GUIDE,
        "cat_stats": cat_stats,
        "plan": {"lump": lump, "sip": sip, "years": 15},
    }
    out = EQ / "combo_risk.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print("eligible", len(eligible), "pairs", len(pairs), "bytes", out.stat().st_size)
    print("best pair", pairs[0] if pairs else None)
    print("top10", top10)
    print("expert", [p["title"] for p in expert_pairs])


if __name__ == "__main__":
    main()
