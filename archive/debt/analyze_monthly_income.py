"""
Monthly IDCW Debt Fund Analyzer
Investment: Rs 4L | Horizon: 3-5 years | Goal: monthly payout
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

INVESTMENT = 400_000
HORIZON_YEARS = (3, 5)
BASE_URL = "https://api.mfapi.in/mf"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Debt categories suitable for 3-5 year monthly income (lower number = lower risk)
CATEGORY_RISK = {
    "liquid": 1.5,
    "overnight": 1.0,
    "ultra short": 2.0,
    "low duration": 2.5,
    "money market": 2.5,
    "short duration": 3.5,
    "banking and psu": 3.0,
    "corporate bond": 4.5,
    "medium duration": 5.5,
    "medium to long": 6.0,
    "long duration": 7.5,
    "credit risk": 8.0,
    "dynamic bond": 5.0,
    "floater": 4.0,
    "gilt": 6.5,
}

DEBT_KEYWORDS = [
    "debt", "liquid", "bond", "income", "gilt", "duration", "credit",
    "floater", "banking", "psu", "money market", "overnight", "corporate",
]

EXCLUDE_KEYWORDS = [
    "hybrid", "equity", "arbitrage", "balanced", "advantage", "multi asset",
    "fof", "fund of fund", "children", "retirement", "elss", "tax saver",
    "reinvestment", "reinvest", "bonus", "weekly", "quarterly", "annual",
    "half yearly", "semi annual", "daily idcw", "weekly idcw",
]

PREFERRED_KEYWORDS = ["monthly", "idcw", "dividend"]
PAYOUT_KEYWORDS = ["payout", "pay-out"]


def fetch_json(url: str, retries: int = 3) -> dict | list:
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    return {}


def get_all_schemes() -> list[dict]:
    data = fetch_json(BASE_URL)
    return data if isinstance(data, list) else []


def is_debt_monthly_payout(scheme_name: str, meta: dict | None = None) -> bool:
    name = scheme_name.lower()
    if not any(k in name for k in PREFERRED_KEYWORDS):
        return False
    if any(k in name for k in EXCLUDE_KEYWORDS):
        return False
    if "direct" not in name:
        return False

    category = (meta or {}).get("scheme_category", "").lower()
    scheme_type = (meta or {}).get("scheme_type", "").lower()

    debt_match = any(k in name for k in DEBT_KEYWORDS) or "debt" in category
    if not debt_match:
        return False

    # Prefer explicit payout plans; allow if no reinvestment in name
    if "reinvestment" in name or "re-investment" in name:
        return False

    return True


def category_base_risk(name: str, category: str) -> float:
    text = f"{name} {category}".lower()
    for key, score in sorted(CATEGORY_RISK.items(), key=lambda x: -len(x[0])):
        if key in text:
            return score
    if "debt" in text:
        return 4.0
    return 5.0


def detect_payouts(nav_df: pd.DataFrame) -> pd.DataFrame:
    """Detect IDCW payouts from sudden NAV drops (ex-dividend effect)."""
    df = nav_df.sort_values("date").copy()
    df["nav"] = df["nav"].astype(float)
    df["pct_change"] = df["nav"].pct_change()

    # Monthly debt IDCW typically causes 0.15%–1.2% single-day NAV drop
    payouts = df[(df["pct_change"] < -0.0015) & (df["pct_change"] > -0.025)].copy()
    payouts["payout_pct"] = -payouts["pct_change"] * 100
    payouts["payout_amount_per_unit"] = -payouts["nav"].diff().abs()
    return payouts


def analyze_scheme(scheme_code: int, scheme_name: str) -> dict | None:
    try:
        data = fetch_json(f"{BASE_URL}/{scheme_code}")
    except Exception:
        return None

    meta = data.get("meta", {})
    if not is_debt_monthly_payout(scheme_name, meta):
        return None

    records = data.get("data", [])
    if len(records) < 180:
        return None

    nav_df = pd.DataFrame(records)
    nav_df["date"] = pd.to_datetime(nav_df["date"], format="%d-%m-%Y", errors="coerce")
    nav_df = nav_df.dropna(subset=["date", "nav"])
    nav_df["nav"] = nav_df["nav"].astype(float)

    cutoff = datetime.now() - timedelta(days=365 * 2)
    nav_df = nav_df[nav_df["date"] >= cutoff]
    if len(nav_df) < 120:
        return None

    nav_df = nav_df.sort_values("date")
    daily_returns = nav_df["nav"].pct_change().dropna()

    # Exclude payout days for volatility (true accrual volatility)
    payouts = detect_payouts(nav_df)
    payout_dates = set(payouts["date"].dt.date)
    accrual_returns = daily_returns[
        ~daily_returns.index.isin(
            nav_df[nav_df["date"].dt.date.isin(payout_dates)].index
        )
    ]

    ann_vol = float(accrual_returns.std() * (252 ** 0.5) * 100) if len(accrual_returns) > 30 else 99.0

    rolling_max = nav_df["nav"].cummax()
    drawdown = (nav_df["nav"] - rolling_max) / rolling_max
    max_drawdown = float(abs(drawdown.min()) * 100)

    # Payout analysis (last 12 months)
    one_year_ago = datetime.now() - timedelta(days=365)
    recent_payouts = payouts[payouts["date"] >= one_year_ago]

    if len(recent_payouts) < 6:
        return None

    avg_monthly_payout_pct = float(recent_payouts["payout_pct"].mean())
    annual_payout_yield = avg_monthly_payout_pct * len(recent_payouts) / max(1, len(recent_payouts) / 12 * 12) * 12 / 12
    # Better: sum of monthly payout pcts annualized
    monthly_payouts = recent_payouts.set_index("date").resample("ME").last()
    months_with_payout = len(recent_payouts)
    total_payout_pct_12m = float(recent_payouts["payout_pct"].sum())
    annualized_yield = total_payout_pct_12m  # already ~12 months of payout %

    latest_nav = float(nav_df.iloc[-1]["nav"])
    avg_monthly_payout_rs = (avg_monthly_payout_pct / 100) * INVESTMENT
    annual_income_rs = avg_monthly_payout_rs * 12

    # Payout consistency: expect ~10-12 payouts per year
    expected_months = 12
    consistency = min(100, (months_with_payout / expected_months) * 100)

    category = meta.get("scheme_category", "")
    cat_risk = category_base_risk(scheme_name, category)

    # --- Risk Score (1-10, 10 = highest risk) ---
    vol_component = min(3.0, ann_vol / 0.15)          # 0.15% ann vol ~ low
    dd_component = min(2.5, max_drawdown / 0.5)         # 0.5% max DD baseline
    cat_component = cat_risk * 0.45                   # category weight
    consistency_penalty = max(0, (85 - consistency) / 20)  # missed payouts add risk

    risk_score = round(
        min(10, max(1, cat_component + vol_component + dd_component + consistency_penalty)),
        1,
    )

    # Suitability for 3-5 years: penalize very short (liquid) and very long duration
    horizon_fit = 10.0
    text = f"{scheme_name} {category}".lower()
    if "liquid" in text or "overnight" in text:
        horizon_fit -= 2.0  # ok but suboptimal for 3-5yr
    if "long duration" in text or "gilt" in text:
        horizon_fit -= 1.5
    if any(k in text for k in ["short duration", "corporate bond", "low duration", "banking"]):
        horizon_fit += 1.0

    suitability = round(min(10, max(1, horizon_fit - (risk_score - 4) * 0.3)), 1)

    return {
        "scheme_code": scheme_code,
        "scheme_name": scheme_name,
        "fund_house": meta.get("fund_house", ""),
        "category": category,
        "latest_nav": round(latest_nav, 4),
        "avg_monthly_payout_pct": round(avg_monthly_payout_pct, 3),
        "annual_payout_yield_pct": round(annualized_yield, 2),
        "avg_monthly_income_rs": round(avg_monthly_payout_rs, 0),
        "annual_income_rs": round(annual_income_rs, 0),
        "payouts_last_12m": months_with_payout,
        "payout_consistency_pct": round(consistency, 0),
        "ann_volatility_pct": round(ann_vol, 3),
        "max_drawdown_pct": round(max_drawdown, 3),
        "risk_score": risk_score,
        "suitability_3_5yr": suitability,
    }


def main():
    print("Fetching scheme list from mfapi.in...")
    schemes = get_all_schemes()
    print(f"Total schemes: {len(schemes)}")

    candidates = [
        s for s in schemes
        if is_debt_monthly_payout(s.get("schemeName", ""), None)
    ]
    print(f"Monthly IDCW debt (direct, payout) candidates: {len(candidates)}")

    results = []
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(analyze_scheme, s["schemeCode"], s["schemeName"]): s
            for s in candidates
        }
        for fut in as_completed(futures):
            done += 1
            if done % 25 == 0:
                print(f"  Analyzed {done}/{len(candidates)}...")
            result = fut.result()
            if result:
                results.append(result)

    if not results:
        print("No analyzable funds found.")
        return

    df = pd.DataFrame(results)
    df = df.sort_values(["suitability_3_5yr", "annual_payout_yield_pct"], ascending=[False, False])

    out_csv = OUTPUT_DIR / "monthly_debt_analysis.csv"
    df.to_csv(out_csv, index=False)

    # Top picks by risk tier
    low_risk = df[df["risk_score"] <= 3.5].head(5)
    moderate = df[(df["risk_score"] > 3.5) & (df["risk_score"] <= 5.5)].head(5)
    high_yield = df.nlargest(5, "annual_payout_yield_pct")

    summary = {
        "investment": INVESTMENT,
        "horizon_years": list(HORIZON_YEARS),
        "analyzed_funds": len(df),
        "highest_yield": df.nlargest(1, "annual_payout_yield_pct").iloc[0].to_dict(),
        "best_suitable": df.nlargest(1, "suitability_3_5yr").iloc[0].to_dict(),
        "low_risk_top": low_risk.to_dict(orient="records"),
        "moderate_risk_top": moderate.to_dict(orient="records"),
        "high_yield_top": high_yield.to_dict(orient="records"),
        "risk_methodology": {
            "scale": "1-10 (10 = highest risk)",
            "components": {
                "category_risk": "Base risk by fund category (Liquid=1.5, Short Duration=3.5, Corporate Bond=4.5, Medium Duration=5.5, etc.)",
                "volatility": "Annualized std dev of daily NAV returns (excluding payout days), capped contribution 0-3",
                "max_drawdown": "Worst peak-to-trough NAV fall in 2 years, capped contribution 0-2.5",
                "consistency_penalty": "Extra risk if fewer than ~10 monthly payouts in last 12 months",
            },
            "formula": "risk_score = category_component + vol_component + drawdown_component + consistency_penalty",
        },
    }

    out_json = OUTPUT_DIR / "analysis_summary.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nAnalyzed {len(df)} funds with sufficient payout history.")
    print(f"Results saved to {out_csv}")
    print(f"Summary saved to {out_json}")

    print("\n=== TOP 10 BY SUITABILITY (3-5 yr, Rs 4L) ===")
    cols = [
        "scheme_name", "annual_payout_yield_pct", "avg_monthly_income_rs",
        "risk_score", "suitability_3_5yr", "payouts_last_12m", "category",
    ]
    print(df[cols].head(10).to_string(index=False))

    print("\n=== HIGHEST YIELD (top 5) ===")
    print(df[cols].nlargest(5, "annual_payout_yield_pct").to_string(index=False))


if __name__ == "__main__":
    main()
