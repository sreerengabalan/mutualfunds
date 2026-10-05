"""Debt-only monthly IDCW analyzer for Rs 4L, 3-5 year horizon."""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

INVESTMENT = 400_000
BASE = "https://api.mfapi.in/mf"
OUTPUT = Path(__file__).parent / "output"
OUTPUT.mkdir(exist_ok=True)

SEARCH_TERMS = [
    "liquid monthly idcw direct",
    "short duration monthly idcw direct",
    "corporate bond monthly idcw direct",
    "banking psu monthly idcw direct",
    "low duration monthly idcw direct",
    "medium duration monthly idcw direct",
    "money market monthly idcw direct",
    "floater monthly idcw direct",
]

CAT_RISK = {
    "liquid": 1.5, "overnight": 1.0, "ultra short": 2.0, "low duration": 2.5,
    "money market": 2.5, "short duration": 3.5, "short term": 3.5,
    "banking and psu": 3.0, "corporate bond": 4.5, "corporate debt": 4.5,
    "medium duration": 5.5, "medium to long": 6.0, "floater": 4.0,
    "dynamic bond": 5.0, "gilt": 6.5, "credit risk": 8.0,
}


def discover_codes() -> list[int]:
    seen, codes = set(), []
    for q in SEARCH_TERMS:
        for s in requests.get(f"{BASE}/search", params={"q": q}, timeout=30).json():
            n = s["schemeName"].lower()
            if s["schemeCode"] in seen:
                continue
            if "direct" not in n or "monthly" not in n:
                continue
            if "idcw" not in n and "dividend" not in n:
                continue
            if any(x in n for x in [
                "reinvest", "re-invest", "hybrid", "equity", "elss", "arbitrage",
                "balanced", "advantage", "weekly", "quarterly", "annual", "bi monthly",
            ]):
                continue
            seen.add(s["schemeCode"])
            codes.append(s["schemeCode"])
    return codes


def cat_risk(name: str, cat: str) -> float:
    t = f"{name} {cat}".lower()
    for k, v in sorted(CAT_RISK.items(), key=lambda x: -len(x[0])):
        if k in t:
            return v
    return 4.0


def risk_label(score: float) -> str:
    if score <= 2.5:
        return "Very Low"
    if score <= 3.5:
        return "Low"
    if score <= 5.5:
        return "Moderate"
    if score <= 7.5:
        return "High"
    return "Very High"


def analyze(code: int) -> dict | None:
    data = requests.get(f"{BASE}/{code}", timeout=25).json()
    meta = data["meta"]
    name = meta["scheme_name"]
    cat = meta.get("scheme_category", "")

    if not any(k in cat.lower() for k in ["debt", "liquid", "income"]):
        return None

    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna().sort_values("date")

    yr = df[df["date"] >= datetime.now() - timedelta(days=365)].copy()
    if len(yr) < 100:
        return None

    yr["pct"] = yr["nav"].pct_change()
    pay = yr[(yr["pct"] < -0.0015) & (yr["pct"] > -0.025)]
    if len(pay) < 8:
        return None

    avg_pct = float((-pay["pct"]).mean() * 100)
    annual_yield = float((-pay["pct"]).sum() * 100)
    monthly_rs = avg_pct / 100 * INVESTMENT

    acc = yr[~yr.index.isin(set(pay.index))]["pct"].dropna()
    vol = float(acc.std() * (252 ** 0.5) * 100) if len(acc) > 20 else 5.0
    rm = yr["nav"].cummax()
    dd = float(abs(((yr["nav"] - rm) / rm).min()) * 100)

    consistency = min(100, len(pay) / 12 * 100)
    cr = cat_risk(name, cat)
    risk = round(min(10, max(1, cr + min(2.5, vol / 0.08) + min(2.0, dd / 0.4) + max(0, (90 - consistency) / 15))), 1)

    text = f"{name} {cat}".lower()
    fit = 7.0
    if any(x in text for x in ["short duration", "short term", "corporate", "banking", "low duration"]):
        fit += 2.0
    elif "liquid" in text or "money market" in text:
        fit += 0.5
    if any(x in text for x in ["medium duration", "gilt", "long duration"]):
        fit -= 1.5
    fit -= max(0, (risk - 3.5) * 0.5)
    suitability = round(min(10, max(1, fit)), 1)

    return {
        "scheme_code": code,
        "name": name,
        "fund_house": meta.get("fund_house", ""),
        "category": cat,
        "annual_yield_pct": round(annual_yield, 2),
        "avg_monthly_payout_pct": round(avg_pct, 3),
        "monthly_income_rs": round(monthly_rs),
        "annual_income_rs": round(monthly_rs * 12),
        "risk_score": risk,
        "risk_label": risk_label(risk),
        "suitability_3_5yr": suitability,
        "payouts_12m": len(pay),
        "consistency_pct": round(consistency),
        "volatility_pct": round(vol, 2),
        "max_drawdown_pct": round(dd, 2),
    }


def main():
    codes = discover_codes()
    print(f"Discovered {len(codes)} candidates", flush=True)

    results = []
    for i, code in enumerate(codes):
        try:
            r = analyze(code)
            if r:
                results.append(r)
                print(f"  OK {r['annual_yield_pct']}% | Rs{r['monthly_income_rs']}/mo | risk {r['risk_score']} | {r['name'][:50]}", flush=True)
        except Exception:
            pass

    df = pd.DataFrame(results).sort_values(["suitability_3_5yr", "annual_yield_pct"], ascending=[False, False])
    df.to_csv(OUTPUT / "monthly_debt_analysis.csv", index=False)

    summary = {
        "investment": INVESTMENT,
        "horizon": "3-5 years",
        "analyzed": len(df),
        "best_balanced": df.iloc[0].to_dict() if len(df) else None,
        "highest_yield": df.nlargest(1, "annual_yield_pct").iloc[0].to_dict() if len(df) else None,
        "lowest_risk": df.nsmallest(1, "risk_score").iloc[0].to_dict() if len(df) else None,
        "top_12": df.head(12).to_dict(orient="records"),
    }
    with open(OUTPUT / "analysis_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nAnalyzed {len(df)} funds\n", flush=True)
    cols = ["name", "annual_yield_pct", "monthly_income_rs", "risk_score", "risk_label", "suitability_3_5yr", "payouts_12m"]
    print("=== TOP 12 ===", flush=True)
    print(df[cols].head(12).to_string(index=False), flush=True)
    print("\n=== HIGHEST YIELD (8) ===", flush=True)
    print(df.nlargest(8, "annual_yield_pct")[cols].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
