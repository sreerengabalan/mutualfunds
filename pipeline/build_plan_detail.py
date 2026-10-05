"""Build detailed 15-year plan data: yearly forecast, history, 10 expert pairs."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from build_combo_risk import (
    CAT_GUIDE,
    EXPERT_TEMPLATES,
    align,
    category_stats,
    cagr_pct,
    forward_scores,
    overlap,
    pair_risk,
    theme_scores,
)

ROOT = Path(__file__).resolve().parent.parent
EQ = ROOT / "output" / "equity"

LUMP = 300_000.0
SIP = 15_000.0
YEARS = 15
HIST_STARTS = ["2016-01-01", "2019-02-01", "2021-01-01"]

EXPERT_TEMPLATES_EXTRA = [
    {
        "id": "ppfas_mid",
        "title": "Flexi core + mid engine",
        "a": 122639,
        "b": 118989,
        "split": 65,
        "why": "PPFAS Flexi (quality + global) with HDFC Mid Cap. Classic 65/35: core does heavy lifting, mid adds growth without full small-cap volatility.",
    },
    {
        "id": "hdfc_combo",
        "title": "HDFC flexi + small satellite",
        "a": 118955,
        "b": 118778,
        "split": 60,
        "why": "HDFC Flexi (large-heavy India book) + Nippon Small Cap. Same AMC but different cap buckets; overlap stays moderate (~8%).",
    },
    {
        "id": "multi_small",
        "title": "Multi-cap structure + small alpha",
        "a": 149185,
        "b": 145137,
        "split": 70,
        "why": "Kotak Multicap (mandated 25/25/25 across caps) + Invesco Smallcap. Structured core with a small-cap kicker.",
    },
    {
        "id": "value_growth",
        "title": "Value flexi + large & mid",
        "a": 118275,
        "b": 118834,
        "split": 55,
        "why": "Canara Robeco Flexi + Mirae Large & Mid. Two different managers; overlap usually low; no small-cap mandate.",
    },
    {
        "id": "bluechip_mid",
        "title": "Large-cap safety + mid-cap punch",
        "a": 120586,
        "b": 127042,
        "split": 55,
        "why": "ICICI Bluechip (large anchor) + Motilal Oswal Midcap (digital/AI tilt). For investors who want large-cap sleep with mid-cap upside.",
    },
]

ALL_EXPERT = EXPERT_TEMPLATES + EXPERT_TEMPLATES_EXTRA

COMBO_PRESETS = [
    {
        "id": "flexi_mid",
        "label": "Flexi + Mid",
        "catA": "flexi_cap",
        "catB": "mid_cap",
        "split": 65,
        "hint": "Classic expert split: one flexi core (manager picks across caps) plus a mid-cap growth engine. Example: PPFAS Flexi + HDFC Mid Cap.",
    },
    {
        "id": "flexi_small",
        "label": "Flexi + Small",
        "catA": "flexi_cap",
        "catB": "small_cap",
        "split": 70,
        "hint": "Most popular 15-year pair: flexi does the heavy lifting; small cap adds alpha with 20–30% satellite weight.",
    },
    {
        "id": "flexi_lmid",
        "label": "Flexi + Large & Mid",
        "catA": "flexi_cap",
        "catB": "large_mid_cap",
        "split": 60,
        "hint": "No small-cap mandate. Flexi core + large&mid for digital/industrial tilt without full small-cap volatility.",
    },
    {
        "id": "large_mid",
        "label": "Large + Mid",
        "catA": "large_cap",
        "catB": "mid_cap",
        "split": 55,
        "hint": "Large-cap anchor for smoother ride; mid cap for growth. Good if you want less flexi-manager risk.",
    },
    {
        "id": "large_small",
        "label": "Large + Small",
        "catA": "large_cap",
        "catB": "small_cap",
        "split": 75,
        "hint": "Barbell: large-cap safety net with a small-cap kicker. Keep small at 20–25% mentally even if you type 25%.",
    },
    {
        "id": "multi_small",
        "label": "Multi + Small",
        "catA": "multi_cap",
        "catB": "small_cap",
        "split": 70,
        "hint": "Multi-cap is mandated 25/25/25 across caps; small satellite on top. Structured core + aggressive tail.",
    },
    {
        "id": "flexi_multi",
        "label": "Flexi + Multi",
        "catA": "flexi_cap",
        "catB": "multi_cap",
        "split": 55,
        "hint": "Two all-cap styles: manager-driven flexi vs SEBI-mandated multi. Check overlap — can be moderate.",
    },
    {
        "id": "lmid_mid",
        "label": "Large & Mid + Mid",
        "catA": "large_mid_cap",
        "catB": "mid_cap",
        "split": 50,
        "hint": "Both mid-heavy categories — experts rarely do this. Use only if you understand overlap will be high.",
    },
    {
        "id": "large_lmid",
        "label": "Large + Large & Mid",
        "catA": "large_cap",
        "catB": "large_mid_cap",
        "split": 50,
        "hint": "Conservative blend: pure large plus large&mid. Lower vol than flexi+small; lower upside too.",
    },
    {
        "id": "mid_small",
        "label": "Mid + Small",
        "catA": "mid_cap",
        "catB": "small_cap",
        "split": 60,
        "hint": "Aggressive all-growth pair. Only for 15+ year horizon and stomach for 45%+ drawdowns. Not a beginner combo.",
    },
]


def top_fund_by_cat(funds: list[dict]) -> dict[str, int]:
    best: dict[str, dict] = {}
    for f in funds:
        c = f["cat"]
        if c not in best or (f.get("y5") or 0) > (best[c].get("y5") or 0):
            best[c] = f
    return {c: int(f["code"]) for c, f in best.items()}


def enrich_combo_presets(funds: list[dict]) -> list[dict]:
    top = top_fund_by_cat(funds)
    out = []
    for p in COMBO_PRESETS:
        row = dict(p)
        row["defaultA"] = top.get(p["catA"])
        row["defaultB"] = top.get(p["catB"])
        out.append(row)
    return out


CONCEPTS = [
    {
        "id": "base",
        "term": "Base case",
        "short": "The middle forecast if returns stay close to the fund’s long-term track record.",
        "detail": "We blend each fund’s 10-year, 5-year, or 3-year rolling CAGR (whichever is available) using your split. This is not a promise — it is the arithmetic midpoint for planning.",
    },
    {
        "id": "bear",
        "term": "Bear case",
        "short": "A pessimistic path: base return minus 4 percentage points.",
        "detail": "Markets can deliver below-average decades (Japan 1990s, India 2008–2013 for many funds). Bear case asks: if returns are weaker than history, what do you still end up with? Use this for stress-testing, not fear.",
    },
    {
        "id": "bull",
        "term": "Bull case",
        "short": "An optimistic path: base return plus 2 percentage points.",
        "detail": "A strong equity cycle (like 2016–2021 for mid/small caps) can beat long-term averages for a while. Bull case caps at 22% so numbers stay realistic. Do not plan your life around bull alone.",
    },
    {
        "id": "cagr",
        "term": "CAGR (Compound Annual Growth Rate)",
        "short": "The smoothed yearly return that turns your starting money into the ending value.",
        "detail": "If ₹30 lakh becomes ₹1.5 crore in 15 years, CAGR is about 11.5% per year — even if some years were +40% and others −20%. SIP makes this harder to feel intuitively; that is why we show year-by-year tables.",
    },
    {
        "id": "overlap",
        "term": "Stock overlap",
        "short": "How much of fund A’s portfolio is also inside fund B.",
        "detail": "Computed as the sum of min(weight in A, weight in B) across common stocks. Two ‘different’ funds with 35% overlap are partly the same bet. Under 20% = low, 20–40% = moderate, 40%+ = high.",
    },
    {
        "id": "drawdown",
        "term": "Max drawdown",
        "short": "The worst peak-to-trough fall before recovering.",
        "detail": "If your ₹10L became ₹6L at the bottom of COVID (2020), that is a 40% drawdown. For 15-year SIPs, drawdowns on paper are normal. Selling during drawdown is what turns paper loss into real loss.",
    },
    {
        "id": "flexi",
        "term": "Flexi cap",
        "short": "Manager can invest anywhere across large, mid, and small without fixed limits.",
        "detail": "One fund can act as your core. Many flexi funds are actually large-cap heavy in practice — read the factsheet, not just the label.",
    },
    {
        "id": "direct",
        "term": "Direct vs Regular plan",
        "short": "Direct = lower expense ratio; same stocks and same tax on withdrawal.",
        "detail": "Direct saves roughly 0.5–1% per year in TER. Over 15 years that compounding matters. Tax (STCG 20%, LTCG 12.5% after ₹1.25L) is identical for Direct and Regular Growth.",
    },
    {
        "id": "sip",
        "term": "SIP (Systematic Investment Plan)",
        "short": "Fixed amount invested every month automatically.",
        "detail": "₹15,000/month for 15 years = 180 instalments = ₹27 lakh of SIP + ₹3 lakh lumpsum = ₹30 lakh total invested. Early instalments have more time to compound; recent instalments are still short-term for tax if sold.",
    },
]


def monthly_rate(cagr: float) -> float:
    return (1 + cagr) ** (1 / 12) - 1 if cagr > -0.99 else 0


def yearly_projection(cagr: float, lump: float, sip: float, years: int, start_year: int = 2027) -> list[dict]:
    rm = monthly_rate(cagr)
    value = float(lump)
    invested = float(lump)
    rows = []
    sip_in_year = 0.0
    for m in range(1, years * 12 + 1):
        added = sip if m > 1 else 0
        if m > 1:
            value = value * (1 + rm) + sip
            invested += sip
            sip_in_year += sip
        if m % 12 == 0:
            y = start_year + (m // 12) - 1
            profit = value - invested
            rows.append(
                {
                    "y": y,
                    "added": round(lump if m == 12 else sip_in_year),
                    "invested": round(invested),
                    "value": round(value),
                    "profit": round(profit),
                    "ret": round(profit / invested * 100, 1) if invested else 0,
                }
            )
            sip_in_year = 0.0
    return rows


def yearly_history_pair(
    nav_a: list, nav_b: list, split: float, lump: float, sip: float, start: str
) -> list[dict]:
    sa = [p for p in nav_a if p[0] >= start]
    da = {p[0]: p[1] for p in sa}
    db = {p[0]: p[1] for p in nav_b if p[0] >= start}
    dates = sorted(set(da) & set(db))
    if len(dates) < 6:
        return []
    w1, w2 = split, 1 - split
    ua = lump * w1 / da[dates[0]]
    ub = lump * w2 / db[dates[0]]
    invested = lump
    rows: list[dict] = []
    sip_yr = 0.0
    for i, d in enumerate(dates):
        if i > 0:
            ua += sip * w1 / da[d]
            ub += sip * w2 / db[d]
            invested += sip
            sip_yr += sip
        val = ua * da[d] + ub * db[d]
        nxt = dates[i + 1] if i + 1 < len(dates) else None
        if nxt is None or nxt[:4] != d[:4]:
            profit = val - invested
            rows.append(
                {
                    "y": int(d[:4]),
                    "added": round(lump if not rows else sip_yr),
                    "invested": round(invested),
                    "value": round(val),
                    "profit": round(profit),
                    "ret": round(profit / invested * 100, 1) if invested else 0,
                }
            )
            sip_yr = 0.0
    return rows


def nav_from_2016(codes: list[int]) -> dict[str, list]:
    hist = pd.read_csv(EQ / "nav_history.csv", parse_dates=["date"])
    hist = hist[hist["scheme_code"].isin(codes)]
    hist = hist[hist["date"] >= "2016-01-01"]
    out: dict[str, list] = {}
    for code, g in hist.groupby("scheme_code"):
        g = g.sort_values("date").set_index("date")
        m = g["nav"].resample("ME").last().dropna()
        out[str(int(code))] = [
            [d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in m.items()
        ]
    return out


def build_all_expert(funds: list[dict], nav: dict, holdings: dict) -> list[dict]:
    by_code = {f["code"]: f for f in funds}
    out = []
    for tpl in ALL_EXPERT:
        fa, fb = by_code.get(tpl["a"]), by_code.get(tpl["b"])
        if not fa or not fb:
            continue
        split = tpl["split"] / 100
        na, nb = nav.get(str(fa["code"]), []), nav.get(str(fb["code"]), [])
        risk = pair_risk(fa, fb, na, nb, holdings, split, LUMP, SIP)
        if not risk:
            continue
        ca, cb = cagr_pct(fa), cagr_pct(fb)
        base = split * (ca or 0.12) + (1 - split) * (cb or 0.12)
        bear = max(base - 0.04, 0.06)
        bull = min(base + 0.02, 0.22)
        hist = {}
        for hs in HIST_STARTS:
            hy = yearly_history_pair(na, nb, split, LUMP, SIP, hs)
            if hy:
                hist[hs[:4]] = hy
        out.append(
            {
                "id": tpl["id"],
                "title": tpl["title"],
                "why": tpl["why"],
                "a": fa["code"],
                "b": fb["code"],
                "an": fa["name"],
                "bn": fb["name"],
                "ac": fa["cat"],
                "bc": fb["cat"],
                "split": tpl["split"],
                "risk": risk,
                "cagr": {
                    "base": round(base * 100, 2),
                    "bear": round(bear * 100, 2),
                    "bull": round(bull * 100, 2),
                },
                "yearly": {
                    "base": yearly_projection(base, LUMP, SIP, YEARS),
                    "bear": yearly_projection(bear, LUMP, SIP, YEARS),
                    "bull": yearly_projection(bull, LUMP, SIP, YEARS),
                },
                "history": hist,
            }
        )
    out.sort(key=lambda x: -x["risk"].get("fit_score", 0))
    return out


def slim_funds(funds: list[dict]) -> list[dict]:
    return [
        {
            "code": f["code"],
            "name": f["name"],
            "house": f["house"],
            "cat": f["cat"],
            "y3": f.get("y3"),
            "y5": f.get("y5"),
            "y10": f.get("y10"),
            "r3": f.get("r3"),
            "vol": f.get("vol"),
            "dd": f.get("dd"),
            "sh": f.get("sh"),
            "yrs": f.get("yrs"),
        }
        for f in funds
    ]


def main() -> None:
    funds = json.loads((EQ / "selected_50.json").read_text(encoding="utf-8"))
    whatif = json.loads((EQ / "whatif_data.json").read_text(encoding="utf-8"))
    h = whatif["holdings"]
    codes = [int(f["code"]) for f in funds]
    nav = nav_from_2016(codes)
    themes = {str(c): theme_scores(h.get(str(c)) or []) for c in codes}
    forward_scores(funds, themes, h)

    expert = build_all_expert(funds, nav, h)
    theme_slim = {
        k: {t: v[t] for t in ("ai", "ev", "digital", "oil", "transform")}
        for k, v in themes.items()
    }
    payload = {
        "generated": "2026-08-12",
        "plan": {"lump": LUMP, "sip": SIP, "years": YEARS, "start_forecast_year": 2027},
        "concepts": CONCEPTS,
        "cat_guide": CAT_GUIDE,
        "cat_stats": category_stats(funds),
        "combo_presets": enrich_combo_presets(funds),
        "top_by_cat": top_fund_by_cat(funds),
        "funds": slim_funds(funds),
        "nav": nav,
        "holdings": {k: v for k, v in h.items()},
        "themes": theme_slim,
        "expert_pairs": expert,
        "hist_starts": [s[:4] for s in HIST_STARTS],
    }
    out = EQ / "plan_detail.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print("experts", len(expert), "bytes", out.stat().st_size)
    if expert:
        e = expert[0]
        print("sample", e["title"], "base end", e["yearly"]["base"][-1])


if __name__ == "__main__":
    main()
