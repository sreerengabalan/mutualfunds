"""Focused monthly IDCW debt fund analyzer — Rs 4L, 3-5 year horizon."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

INVESTMENT = 400_000
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
BASE = "https://api.mfapi.in/mf"

# Curated Direct Monthly IDCW Payout debt funds (scheme codes from mfapi.in)
FUNDS = [
    (119090, "HDFC Liquid Fund - IDCW Monthly - Direct"),
    (120536, "Invesco India Liquid Fund - Direct - Monthly IDCW Payout"),
    (118365, "Bandhan Liquid Fund - Direct - Monthly IDCW"),
    (118406, "Bandhan Short Duration Fund - Direct - Monthly IDCW"),
    (118372, "Bandhan Low Duration Fund - Direct - Monthly IDCW"),
    (118385, "Bandhan Money Market Fund - Direct - Monthly IDCW"),
    (118402, "Bandhan Medium Duration Fund - Direct - Monthly IDCW"),
    (118571, "Franklin India Corporate Debt - Direct - Monthly IDCW"),
    (118528, "Franklin India Low Duration - Direct - Monthly IDCW"),
    (118567, "Franklin India Short Term Income - Direct - Monthly IDCW"),
    (118457, "IDBI Short Term Bond Fund - Monthly IDCW Direct"),
    (118449, "IDBI Liquid Fund - Monthly IDCW Direct"),
    (120503, "ICICI Pru Liquid Fund - Direct - Monthly IDCW"),
    (120504, "ICICI Pru Short Term Fund - Direct - Monthly IDCW"),
    (120505, "ICICI Pru Corporate Bond Fund - Direct - Monthly IDCW"),
    (120506, "ICICI Pru Banking & PSU Debt - Direct - Monthly IDCW"),
    (119728, "SBI Liquid Fund - Direct - Monthly IDCW"),
    (119729, "SBI Short Term Debt Fund - Direct - Monthly IDCW"),
    (119730, "SBI Corporate Bond Fund - Direct - Monthly IDCW"),
    (120167, "Axis Liquid Fund - Direct - Monthly IDCW"),
    (120168, "Axis Short Duration Fund - Direct - Monthly IDCW"),
    (120169, "Axis Corporate Bond Fund - Direct - Monthly IDCW"),
    (120170, "Axis Banking & PSU Debt - Direct - Monthly IDCW"),
    (118655, "Nippon India Floater Fund - Direct - Monthly IDCW"),
    (119551, "Nippon India Liquid Fund - Direct - Monthly IDCW"),
    (119552, "Nippon India Short Term Fund - Direct - Monthly IDCW"),
    (119553, "Nippon India Corporate Bond - Direct - Monthly IDCW"),
    (120845, "Kotak Liquid - Direct - Monthly IDCW"),
    (120846, "Kotak Short Duration - Direct - Monthly IDCW"),
    (120847, "Kotak Corporate Bond - Direct - Monthly IDCW"),
    (120848, "Kotak Banking & PSU Debt - Direct - Monthly IDCW"),
    (103735, "Quantum Liquid Fund - Direct - Monthly IDCW"),
    (120251, "UTI Liquid Fund - Direct - Monthly IDCW"),
    (120252, "UTI Short Duration Fund - Direct - Monthly IDCW"),
    (120253, "UTI Corporate Bond Fund - Direct - Monthly IDCW"),
    (120254, "UTI Banking & PSU Debt - Direct - Monthly IDCW"),
    (120401, "DSP Liquidity Fund - Direct - Monthly IDCW"),
    (120402, "DSP Short Term Fund - Direct - Monthly IDCW"),
    (120403, "DSP Corporate Bond Fund - Direct - Monthly IDCW"),
    (120404, "DSP Banking & PSU Debt - Direct - Monthly IDCW"),
]

CATEGORY_RISK = {
    "liquid": 1.5, "overnight": 1.0, "ultra short": 2.0, "low duration": 2.5,
    "money market": 2.5, "short duration": 3.5, "short term": 3.5,
    "banking and psu": 3.0, "corporate bond": 4.5, "corporate debt": 4.5,
    "medium duration": 5.5, "medium to long": 6.0, "floater": 4.0,
    "dynamic bond": 5.0, "gilt": 6.5, "credit risk": 8.0,
}


def fetch(code):
    r = requests.get(f"{BASE}/{code}", timeout=25)
    r.raise_for_status()
    return r.json()


def category_risk(name, cat):
    t = f"{name} {cat}".lower()
    for k, v in sorted(CATEGORY_RISK.items(), key=lambda x: -len(x[0])):
        if k in t:
            return v
    return 4.0


def analyze(code, label):
    try:
        data = fetch(code)
    except Exception as e:
        return {"scheme_code": code, "label": label, "error": str(e)}

    meta = data.get("meta", {})
    name = meta.get("scheme_name", label)
    cat = meta.get("scheme_category", "")

    rows = data.get("data", [])
    if len(rows) < 200:
        return None

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna().sort_values("date")

    two_yr = df[df["date"] >= datetime.now() - timedelta(days=730)]
    one_yr = df[df["date"] >= datetime.now() - timedelta(days=365)]
    if len(two_yr) < 150 or len(one_yr) < 100:
        return None

    two_yr = two_yr.copy()
    two_yr["pct"] = two_yr["nav"].pct_change()
    payouts = two_yr[(two_yr["pct"] < -0.0015) & (two_yr["pct"] > -0.03)].copy()
    recent = payouts[payouts["date"] >= datetime.now() - timedelta(days=365)]

    if len(recent) < 6:
        return None

    avg_payout_pct = float((-recent["pct"]).mean() * 100)
    annual_yield = float((-recent["pct"]).sum() * 100)
    monthly_rs = (avg_payout_pct / 100) * INVESTMENT

    # Volatility excluding payout days
    payout_idx = set(recent.index)
    accrual = two_yr[~two_yr.index.isin(payout_idx)]["pct"].dropna()
    ann_vol = float(accrual.std() * (252 ** 0.5) * 100) if len(accrual) > 30 else 5.0

    roll_max = two_yr["nav"].cummax()
    max_dd = float(abs(((two_yr["nav"] - roll_max) / roll_max).min()) * 100)

    consistency = min(100, len(recent) / 12 * 100)
    cat_r = category_risk(name, cat)

    vol_c = min(3.0, ann_vol / 0.15)
    dd_c = min(2.5, max_dd / 0.5)
    cons_pen = max(0, (85 - consistency) / 20)
    risk = round(min(10, max(1, cat_r * 0.45 + vol_c + dd_c + cons_pen)), 1)

    # 3-5 yr suitability
    fit = 8.0
    t = f"{name} {cat}".lower()
    if any(x in t for x in ["short duration", "short term", "corporate", "banking", "low duration"]):
        fit += 1.5
    if "liquid" in t or "money market" in t:
        fit += 0.5
    if "medium duration" in t or "gilt" in t:
        fit -= 1.0
    fit -= max(0, (risk - 4) * 0.4)
    suitability = round(min(10, max(1, fit)), 1)

    risk_label = (
        "Very Low" if risk <= 2.5 else
        "Low" if risk <= 3.5 else
        "Moderate" if risk <= 5.0 else
        "High" if risk <= 7.0 else "Very High"
    )

    return {
        "scheme_code": code,
        "scheme_name": name,
        "fund_house": meta.get("fund_house", ""),
        "category": cat,
        "annual_payout_yield_pct": round(annual_yield, 2),
        "avg_monthly_payout_pct": round(avg_payout_pct, 3),
        "monthly_income_rs_4L": round(monthly_rs, 0),
        "annual_income_rs_4L": round(monthly_rs * 12, 0),
        "payouts_last_12m": len(recent),
        "payout_consistency_pct": round(consistency, 0),
        "ann_volatility_pct": round(ann_vol, 3),
        "max_drawdown_pct": round(max_dd, 3),
        "risk_score": risk,
        "risk_label": risk_label,
        "suitability_3_5yr": suitability,
    }


def main():
    print(f"Analyzing {len(FUNDS)} curated monthly IDCW debt funds for Rs {INVESTMENT:,}...")
    results = []
    for code, label in FUNDS:
        r = analyze(code, label)
        if r and "error" not in r:
            results.append(r)
            print(f"  OK: {r['scheme_name'][:55]} | yield {r['annual_payout_yield_pct']}% | risk {r['risk_score']}")
        elif r and "error" in r:
            print(f"  ERR {code}: {r['error'][:60]}")

    if not results:
        print("No results.")
        return

    df = pd.DataFrame(results).sort_values(
        ["suitability_3_5yr", "annual_payout_yield_pct"], ascending=[False, False]
    )
    df.to_csv(OUTPUT_DIR / "monthly_debt_analysis.csv", index=False)

    summary = {
        "investment_inr": INVESTMENT,
        "horizon": "3-5 years",
        "funds_analyzed": len(df),
        "best_balanced": df.iloc[0].to_dict(),
        "highest_yield": df.nlargest(1, "annual_payout_yield_pct").iloc[0].to_dict(),
        "lowest_risk": df.nsmallest(1, "risk_score").iloc[0].to_dict(),
        "top_10": df.head(10).to_dict(orient="records"),
        "by_risk_tier": {
            "very_low_low": df[df["risk_score"] <= 3.5].head(5).to_dict(orient="records"),
            "moderate": df[(df["risk_score"] > 3.5) & (df["risk_score"] <= 5.5)].head(5).to_dict(orient="records"),
            "high_yield": df.nlargest(5, "annual_payout_yield_pct").to_dict(orient="records"),
        },
    }
    with open(OUTPUT_DIR / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print("\n=== TOP 10 FOR Rs 4L (3-5 yr monthly income) ===")
    cols = ["scheme_name", "annual_payout_yield_pct", "monthly_income_rs_4L", "risk_score", "risk_label", "suitability_3_5yr"]
    print(df[cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
