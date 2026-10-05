"""Rank all two-fund combinations on 10Y history + 15Y forecast."""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

from build_combo_risk import cagr_pct, forecast_15y, overlap, pair_risk
from build_plan_detail import LUMP, SIP, YEARS, nav_from_2016, slim_funds

ROOT = Path(__file__).resolve().parent.parent
EQ = ROOT / "output" / "equity"

# Prefer different categories; still score same-cat pairs lower.
DEFAULT_SPLIT = {
    ("flexi_cap", "small_cap"): 70,
    ("flexi_cap", "mid_cap"): 65,
    ("large_cap", "mid_cap"): 55,
    ("large_cap", "small_cap"): 75,
    ("multi_cap", "small_cap"): 70,
    ("flexi_cap", "large_mid_cap"): 60,
    ("flexi_cap", "multi_cap"): 55,
    ("large_cap", "large_mid_cap"): 50,
    ("large_mid_cap", "mid_cap"): 50,
    ("mid_cap", "small_cap"): 60,
}


def split_for(ca: str, cb: str) -> int:
    if (ca, cb) in DEFAULT_SPLIT:
        return DEFAULT_SPLIT[(ca, cb)]
    if (cb, ca) in DEFAULT_SPLIT:
        return 100 - DEFAULT_SPLIT[(cb, ca)]
    if ca == cb:
        return 50
    # Core-ish categories get higher weight
    core = {"large_cap", "flexi_cap", "multi_cap", "large_mid_cap"}
    if ca in core and cb not in core:
        return 65
    if cb in core and ca not in core:
        return 35
    return 50


def main() -> None:
    funds = json.loads((EQ / "selected_50.json").read_text(encoding="utf-8"))
    whatif = json.loads((EQ / "whatif_data.json").read_text(encoding="utf-8"))
    holdings = whatif["holdings"]
    codes = [int(f["code"]) for f in funds]
    nav = nav_from_2016(codes)
    by_code = {f["code"]: f for f in funds}

    pairs = []
    for a, b in combinations(funds, 2):
        fa, fb = a, b
        # Order: higher AUM / core first for consistent split
        if fa["cat"] not in {"large_cap", "flexi_cap", "multi_cap", "large_mid_cap"} and fb[
            "cat"
        ] in {"large_cap", "flexi_cap", "multi_cap", "large_mid_cap"}:
            fa, fb = fb, fa
        split_pct = split_for(fa["cat"], fb["cat"])
        split = split_pct / 100
        na = nav.get(str(fa["code"]), [])
        nb = nav.get(str(fb["code"]), [])
        risk = pair_risk(fa, fb, na, nb, holdings, split, LUMP, SIP)
        if not risk:
            continue
        ca, cb = cagr_pct(fa), cagr_pct(fb)
        base = split * (ca or 0.12) + (1 - split) * (cb or 0.12)
        bear = max(base - 0.04, 0.06)
        bull = min(base + 0.02, 0.22)
        fc = forecast_15y(base, LUMP, SIP, YEARS)
        ov = overlap(holdings.get(str(fa["code"])) or [], holdings.get(str(fb["code"])) or [])
        # Score: blend historical pair CAGR/fit with forecast value
        hist_cagr = (risk.get("cagr") or 0) * 100
        fit = risk.get("fit_score") or 0
        score = hist_cagr * 0.45 + (fc["value"] / 1e5) * 0.25 + fit * 0.3
        if fa["cat"] == fb["cat"]:
            score -= 8
        if ov is not None and ov > 40:
            score -= 12
        elif ov is not None and ov > 30:
            score -= 5
        pairs.append(
            {
                "a": fa["code"],
                "b": fb["code"],
                "an": fa["name"],
                "bn": fb["name"],
                "ac": fa["cat"],
                "bc": fb["cat"],
                "ah": fa["house"],
                "bh": fb["house"],
                "split": split_pct,
                "ov": ov,
                "hist": {
                    "cagr": round(hist_cagr, 2) if risk.get("cagr") is not None else None,
                    "value": risk.get("value"),
                    "invested": risk.get("invested"),
                    "gain": risk.get("gain"),
                    "dd": risk.get("hist_dd"),
                    "vol": risk.get("port_vol"),
                    "corr": risk.get("corr"),
                    "yrs": risk.get("yrs"),
                    "fit": risk.get("fit_score"),
                    "start": risk.get("start"),
                    "end": risk.get("end"),
                },
                "forecast": {
                    "base": round(base * 100, 2),
                    "bear": round(bear * 100, 2),
                    "bull": round(bull * 100, 2),
                    "value": fc["value"],
                    "invested": fc["invested"],
                    "gain": fc["gain"],
                },
                "score": round(score, 2),
            }
        )

    pairs.sort(key=lambda x: -x["score"])
    for i, p in enumerate(pairs):
        p["rank"] = i + 1

    # India CPI inflation (annual average YoY %). Source: MoSPI / RBI approximations for planning.
    inflation = {
        "unit": "CPI YoY annual average %",
        "note": "Approximate India retail inflation (CPI). Use ~5–6% as a long-term planning assumption. Real return ≈ equity CAGR − inflation.",
        "long_term_avg": 5.5,
        "years": [
            {"y": 2015, "cpi": 4.9},
            {"y": 2016, "cpi": 4.5},
            {"y": 2017, "cpi": 3.3},
            {"y": 2018, "cpi": 3.9},
            {"y": 2019, "cpi": 3.7},
            {"y": 2020, "cpi": 6.6},
            {"y": 2021, "cpi": 5.1},
            {"y": 2022, "cpi": 6.7},
            {"y": 2023, "cpi": 5.4},
            {"y": 2024, "cpi": 4.9},
            {"y": 2025, "cpi": 4.6},
        ],
    }

    payload = {
        "generated": "2026-08-12",
        "plan": {"lump": LUMP, "sip": SIP, "years": YEARS},
        "n_funds": len(funds),
        "n_pairs": len(pairs),
        "funds": funds,  # full fund detail for compare
        "pairs": pairs,
        "top": pairs[:50],
        "inflation": inflation,
    }
    out = EQ / "all_pairs.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print("pairs", len(pairs), "bytes", out.stat().st_size)
    if pairs:
        t = pairs[0]
        print("best", t["an"], "+", t["bn"], "score", t["score"], "fc", t["forecast"]["value"])


if __name__ == "__main__":
    main()
