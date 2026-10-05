"""Select 50 Direct Growth equity funds across SEBI categories."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
EQ = ROOT / "output" / "equity"

SKIP = re.compile(
    r"bonus|idcw|dividend|reinvest|fof|fund of fund|etf",
    re.I,
)

PER_CAT = {
    "large_cap": 8,
    "mid_cap": 8,
    "small_cap": 8,
    "multi_cap": 9,
    "flexi_cap": 9,
    "large_mid_cap": 8,
}


def short_name(name: str) -> str:
    n = name
    n = re.sub(r"\s*-\s*Direct Plan\s*-?\s*", " ", n, flags=re.I)
    n = re.sub(r"\s*Direct Plan\s*", " ", n, flags=re.I)
    n = re.sub(r"\s*-\s*Direct\s*-?\s*", " ", n, flags=re.I)
    n = re.sub(r"\s*Direct\s*", " ", n, flags=re.I)
    n = re.sub(r"\s*Growth Option\s*", " ", n, flags=re.I)
    n = re.sub(r"\s*-\s*Growth\s*", " ", n, flags=re.I)
    n = re.sub(r"\s+Growth\s*$", "", n, flags=re.I)
    n = re.sub(r"\s{2,}", " ", n).strip(" -")
    return n


def main() -> None:
    k = pd.read_csv(EQ / "kpis.csv")
    s = pd.read_csv(EQ / "sectors.csv")
    k["aum"] = k["aum_cr"].fillna(k["aum_cr_groww"])
    k = k[~k["name"].str.contains(SKIP, na=False)].copy()
    k = k[k["equity_pct"].notna() & (k["nav_points"] >= 250)]
    k = k[k["large_cap_pct"].notna() | (k["history_years"] >= 3)]

    picked = []
    house_count: dict[str, int] = {}
    for cat, n in PER_CAT.items():
        sub = k[k["category"] == cat].copy()
        if cat != "multi_cap":
            prefer = sub[sub["roll_3y_mean_pct"].notna()]
            if len(prefer) >= n:
                sub = prefer
        sub["score"] = (
            sub["roll_3y_mean_pct"].rank(pct=True, na_option="bottom") * 0.30
            + sub["aum"].rank(pct=True, na_option="bottom") * 0.35
            + sub["history_years"].rank(pct=True, na_option="bottom") * 0.25
            + (1 - sub["expense_ratio"].rank(pct=True, na_option="bottom")) * 0.10
        )
        sub = sub.sort_values(["score", "aum"], ascending=False)
        taken = 0
        for _, row in sub.iterrows():
            house = str(row["fund_house"] or "")
            if house_count.get(house, 0) >= 4:
                continue
            picked.append(row)
            house_count[house] = house_count.get(house, 0) + 1
            taken += 1
            if taken >= n:
                break

    sel = pd.DataFrame(picked).drop_duplicates("scheme_code")
    # pad if short
    if len(sel) < 50:
        rest = k[~k["scheme_code"].isin(sel["scheme_code"])].sort_values("aum", ascending=False)
        sel = pd.concat([sel, rest.head(50 - len(sel))], ignore_index=True)

    sel = sel.head(50).sort_values(["category", "name"]).reset_index(drop=True)

    hdfc_flexi = k[k["scheme_code"] == 118955]
    if len(hdfc_flexi) and 118955 not in set(sel["scheme_code"]):
        drop = sel[sel["category"] == "flexi_cap"].nsmallest(1, "aum")
        sel = sel[~sel["scheme_code"].isin(drop["scheme_code"])]
        sel = pd.concat([sel, hdfc_flexi], ignore_index=True)
        sel = sel.sort_values(["category", "name"]).reset_index(drop=True)

    sel.to_csv(EQ / "selected_50.csv", index=False)

    sector_map: dict[int, list] = {}
    for code, g in s[s["scheme_code"].isin(sel["scheme_code"])].groupby("scheme_code"):
        top = g.sort_values("weight_pct", ascending=False).head(6)
        sector_map[int(code)] = [
            {"s": r["sector"], "w": round(float(r["weight_pct"]), 2)}
            for _, r in top.iterrows()
            if float(r["weight_pct"]) >= 0.5
        ]

    funds = []
    for _, r in sel.iterrows():
        code = int(r["scheme_code"])
        funds.append(
            {
                "code": code,
                "name": short_name(str(r["name"])),
                "full": str(r["name"]),
                "house": str(r["fund_house"] or "").replace(" Mutual Fund", ""),
                "cat": r["category"],
                "nav": _n(r.get("latest_nav")),
                "navd": r.get("latest_nav_date") if pd.notna(r.get("latest_nav_date")) else None,
                "yrs": _n(r.get("history_years")),
                "incept": r.get("inception") if pd.notna(r.get("inception")) else None,
                "aum": _n(r.get("aum")),
                "ter": _n(r.get("expense_ratio")),
                "mgr": None if pd.isna(r.get("fund_manager")) else str(r["fund_manager"]),
                "risk": None if pd.isna(r.get("risk_label")) else str(r["risk_label"]),
                "sip": _n(r.get("min_sip")),
                "load": None if pd.isna(r.get("exit_load")) else str(r["exit_load"])[:90],
                "y1": _n(r.get("cagr_1y_pct")),
                "y3": _n(r.get("cagr_3y_pct")),
                "y5": _n(r.get("cagr_5y_pct")),
                "y10": _n(r.get("cagr_10y_pct")),
                "sip5": _n(r.get("sip_cagr_5y_pct")),
                "r3": _n(r.get("roll_3y_mean_pct")),
                "r3p": _n(r.get("roll_3y_positive_pct")),
                "r3mn": _n(r.get("roll_3y_min_pct")),
                "r5": _n(r.get("roll_5y_mean_pct")),
                "vol": _n(r.get("vol_ann_pct")),
                "dd": _n(r.get("max_drawdown_pct")),
                "ddd": r.get("max_drawdown_date") if pd.notna(r.get("max_drawdown_date")) else None,
                "sh": _n(r.get("sharpe_3y")),
                "so": _n(r.get("sortino_3y")),
                "eq": _n(r.get("equity_pct")),
                "dt": _n(r.get("debt_pct")),
                "cash": _n(r.get("cash_pct")),
                "l": _n(r.get("large_cap_pct")),
                "m": _n(r.get("mid_cap_pct")),
                "sml": _n(r.get("small_cap_pct")),
                "t5": _n(r.get("top5_pct")),
                "t10": _n(r.get("top10_pct")),
                "hold": None if pd.isna(r.get("total_holdings")) else int(r["total_holdings"]),
                "pe": _n(r.get("pe")),
                "pb": _n(r.get("pb")),
                "turn": _n(r.get("portfolio_turnover")),
                "sec": sector_map.get(code, []),
            }
        )

    (EQ / "selected_50.json").write_text(json.dumps(funds, indent=2), encoding="utf-8")
    print(sel["category"].value_counts().to_string())
    print("houses", sel["fund_house"].nunique(), "funds", len(sel))
    print(sel[["category", "name", "aum", "cagr_5y_pct", "roll_3y_mean_pct"]].to_string(index=False))


def _n(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    main()
