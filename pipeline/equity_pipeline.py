"""Pull free-market equity mutual fund data and compute KPIs.

Sources
-------
- AMFI NAVAll.txt     official scheme universe + latest NAV + SEBI category
- api.mfapi.in        full historical NAV (used for rolling returns / risk)
- Groww public APIs   AUM, TER, allocation %, market-cap split, sectors
- mfdata.in           optional enrichment (skipped automatically if down)

Universe: Direct Growth plans in Large Cap, Mid Cap, Small Cap,
Multi Cap, Flexi Cap, and Large & Mid Cap.
"""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "equity"
CACHE = OUT / "cache"
NAV_CACHE = CACHE / "nav"
ALLOC_CACHE = CACHE / "allocation"
GROWW_CACHE = CACHE / "groww_meta"
for p in (OUT, NAV_CACHE, ALLOC_CACHE, GROWW_CACHE):
    p.mkdir(parents=True, exist_ok=True)

AMFI_NAVALL = "https://portal.amfiindia.com/spages/NAVAll.txt"
MFAPI = "https://api.mfapi.in/mf"
GROWW = "https://groww.in"
MFDATA = "https://mfdata.in/api/v1"
RF = 0.065  # risk-free proxy for Sharpe / Sortino

CAT_MAP = {
    "large cap fund": "large_cap",
    "mid cap fund": "mid_cap",
    "small cap fund": "small_cap",
    "multi cap fund": "multi_cap",
    "flexi cap fund": "flexi_cap",
    "large & mid cap fund": "large_mid_cap",
}

GROWW_SUBCATS = [
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Multi Cap",
    "Flexi Cap",
    "Large & Mid Cap",
]


def session(name: str) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=16))
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; mf-research/1.0)",
            "Accept": "application/json,text/plain,*/*",
        }
    )
    if name == "groww":
        s.headers.update(
            {
                "Referer": "https://groww.in/mutual-funds",
                "Origin": "https://groww.in",
            }
        )
    return s


AMFI_S = session("amfi")
MFAPI_S = session("mfapi")
GROWW_S = session("groww")
MFDATA_S = session("mfdata")


def get_json(sess: requests.Session, url: str, **kwargs) -> object | None:
    kwargs.setdefault("timeout", 30)
    try:
        r = sess.get(url, **kwargs)
        if r.status_code != 200:
            return None
        if "application/json" not in (r.headers.get("content-type") or "") and r.text[:1] not in "{[":
            return None
        return r.json()
    except Exception:
        return None


def normalize_category(raw: str) -> str | None:
    t = raw.lower().replace("equity schemes -", "").replace("equity scheme -", "").strip()
    for key, slug in sorted(CAT_MAP.items(), key=lambda kv: -len(kv[0])):
        if key in t:
            return slug
    return None


def is_direct_growth(name: str) -> bool:
    n = name.lower()
    if "direct" not in n:
        return False
    if "idcw" in n or "dividend" in n:
        return False
    return "growth" in n


def fetch_amfi_universe() -> pd.DataFrame:
    r = AMFI_S.get(AMFI_NAVALL, timeout=60)
    r.raise_for_status()
    (CACHE / "NAVAll.txt").write_text(r.text, encoding="utf-8", errors="replace")
    current_cat = ""
    current_house = ""
    rows = []
    for line in r.text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"Open Ended Schemes\((.+)\)", line)
        if m:
            current_cat = m.group(1)
            continue
        if ";" not in line:
            if "Mutual Fund" in line or line.endswith("Fund"):
                current_house = line
            continue
        parts = line.split(";")
        if len(parts) < 6 or not parts[0].isdigit():
            continue
        slug = normalize_category(current_cat)
        if not slug:
            continue
        name = parts[3].strip()
        if not is_direct_growth(name):
            continue
        rows.append(
            {
                "scheme_code": int(parts[0]),
                "isin": parts[1].strip() if parts[1].strip() not in {"", "-"} else None,
                "name": name,
                "amfi_nav": pd.to_numeric(parts[4], errors="coerce"),
                "amfi_nav_date": parts[5].strip(),
                "amfi_category": current_cat,
                "category": slug,
                "fund_house": current_house,
            }
        )
    df = pd.DataFrame(rows).drop_duplicates("scheme_code")
    return df.sort_values(["category", "name"]).reset_index(drop=True)


def fetch_groww_catalog() -> dict[int, dict]:
    catalog: dict[int, dict] = {}
    for sub in GROWW_SUBCATS:
        page = 0
        while True:
            data = get_json(
                GROWW_S,
                f"{GROWW}/v1/api/search/v1/derived/scheme",
                params={
                    "doc_type": "scheme",
                    "page": page,
                    "size": 50,
                    "plan_type": "Direct",
                    "scheme_type": "Growth",
                    "sub_category": sub,
                },
                timeout=25,
            )
            if not data or not data.get("content"):
                break
            for item in data["content"]:
                try:
                    code = int(item.get("scheme_code") or 0)
                except (TypeError, ValueError):
                    continue
                if not code:
                    continue
                catalog[code] = {
                    "groww_name": item.get("scheme_name") or item.get("fund_name"),
                    "search_id": item.get("search_id") or item.get("direct_search_id"),
                    "expense_ratio": pd.to_numeric(item.get("expense_ratio"), errors="coerce"),
                    "aum_cr": pd.to_numeric(item.get("aum"), errors="coerce"),
                    "fund_manager": item.get("fund_manager"),
                    "groww_category": item.get("category"),
                    "groww_sub_category": item.get("sub_category"),
                    "risk": item.get("risk"),
                    "groww_rating": item.get("groww_rating"),
                    "min_sip": item.get("min_sip_investment"),
                    "min_lumpsum": item.get("min_investment_amount"),
                    "exit_load": item.get("exit_load"),
                    "launch_date": item.get("launch_date"),
                    "return_1y": item.get("return1y"),
                    "return_3y": item.get("return3y"),
                    "sip_return_1y": item.get("sip_return1y") or item.get("sipReturn1y"),
                    "sip_return_3y": item.get("sip_return3y"),
                }
            page += 1
            if page * 50 >= int(data.get("total_results") or 0):
                break
            if page > 20:
                break
    (GROWW_CACHE / "catalog.json").write_text(json.dumps(catalog, default=str), encoding="utf-8")
    return catalog


def fetch_nav_history(code: int) -> pd.DataFrame:
    path = NAV_CACHE / f"{code}.json"
    if path.exists() and path.stat().st_size > 50:
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = get_json(MFAPI_S, f"{MFAPI}/{code}", timeout=45)
        if not payload or payload.get("status") != "SUCCESS":
            return pd.DataFrame(columns=["date", "nav"])
        path.write_text(json.dumps(payload), encoding="utf-8")
        time.sleep(0.05)
    rows = payload.get("data") or []
    if not rows:
        return pd.DataFrame(columns=["date", "nav"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna().sort_values("date").drop_duplicates("date")
    return df


def fetch_allocation(code: int) -> dict:
    path = ALLOC_CACHE / f"{code}.json"
    if path.exists() and path.stat().st_size > 20:
        return json.loads(path.read_text(encoding="utf-8"))
    data = get_json(
        GROWW_S,
        f"{GROWW}/v1/api/data/mf/web/v1/scheme/portfolio/{code}/stats",
        timeout=20,
    )
    if not isinstance(data, dict):
        data = {}
    path.write_text(json.dumps(data, default=str), encoding="utf-8")
    time.sleep(0.04)
    return data


def cagr(start: float, end: float, years: float) -> float | None:
    if start is None or end is None or start <= 0 or years <= 0:
        return None
    return float((end / start) ** (1 / years) - 1)


def point_return(nav: pd.Series, years: float) -> float | None:
    if nav.empty:
        return None
    end = nav.iloc[-1]
    target = nav.index[-1] - pd.DateOffset(years=years)
    prior = nav[nav.index <= target]
    if prior.empty:
        return None
    return cagr(float(prior.iloc[-1]), float(end), years)


def rolling_cagr(nav: pd.Series, years: int) -> dict:
    monthly = nav.resample("ME").last().dropna()
    window = years * 12
    if len(monthly) < window + 1:
        return {}
    vals = []
    for i in range(window, len(monthly)):
        a, b = float(monthly.iloc[i - window]), float(monthly.iloc[i])
        if a > 0:
            vals.append((b / a) ** (1 / years) - 1)
    if not vals:
        return {}
    arr = np.array(vals)
    return {
        f"roll_{years}y_mean_pct": round(float(arr.mean()) * 100, 2),
        f"roll_{years}y_median_pct": round(float(np.median(arr)) * 100, 2),
        f"roll_{years}y_min_pct": round(float(arr.min()) * 100, 2),
        f"roll_{years}y_max_pct": round(float(arr.max()) * 100, 2),
        f"roll_{years}y_positive_pct": round(float((arr > 0).mean()) * 100, 1),
        f"roll_{years}y_windows": int(len(arr)),
    }


def max_drawdown(nav: pd.Series) -> tuple[float | None, str | None]:
    if nav.empty:
        return None, None
    peak = nav.cummax()
    dd = nav / peak - 1
    i = dd.idxmin()
    return float(dd.min()), i.strftime("%Y-%m-%d") if pd.notna(i) else None


def sip_cagr(nav: pd.Series, years: float) -> float | None:
    monthly = nav.resample("ME").last().dropna()
    n = int(years * 12)
    if len(monthly) < n:
        return None
    window = monthly.iloc[-n:]
    units = (1.0 / window).sum()
    invested = float(n)
    fv = float(units * window.iloc[-1])
    if invested <= 0 or fv <= 0:
        return None
    return cagr(invested, fv, years)


def compute_kpis(nav_df: pd.DataFrame) -> dict:
    if nav_df.empty or len(nav_df) < 20:
        return {"nav_points": int(len(nav_df))}
    s = nav_df.set_index("date")["nav"].sort_index()
    daily = s.pct_change().dropna()
    years = (s.index[-1] - s.index[0]).days / 365.25
    vol = float(daily.std() * np.sqrt(252)) if len(daily) > 20 else None
    downside = daily[daily < 0]
    ddev = float(downside.std() * np.sqrt(252)) if len(downside) > 10 else None
    dd, dd_date = max_drawdown(s)
    cagr_si = cagr(float(s.iloc[0]), float(s.iloc[-1]), years) if years >= 0.5 else None
    cagr_3 = point_return(s, 3)
    cagr_5 = point_return(s, 5)
    sharpe = None
    if cagr_3 is not None and vol and vol > 0:
        sharpe = (cagr_3 - RF) / vol
    sortino = None
    if cagr_3 is not None and ddev and ddev > 0:
        sortino = (cagr_3 - RF) / ddev
    calmar = None
    if cagr_5 is not None and dd and dd < 0:
        calmar = cagr_5 / abs(dd)

    cal = s.resample("YE").last().dropna()
    cal_ret = cal.pct_change().dropna()
    best_year = worst_year = None
    if not cal_ret.empty:
        best_year = round(float(cal_ret.max()) * 100, 2)
        worst_year = round(float(cal_ret.min()) * 100, 2)

    out = {
        "nav_points": int(len(s)),
        "inception": s.index[0].strftime("%Y-%m-%d"),
        "latest_nav_date": s.index[-1].strftime("%Y-%m-%d"),
        "latest_nav": round(float(s.iloc[-1]), 4),
        "history_years": round(years, 2),
        "cagr_1y_pct": _pct(point_return(s, 1)),
        "cagr_3y_pct": _pct(cagr_3),
        "cagr_5y_pct": _pct(cagr_5),
        "cagr_7y_pct": _pct(point_return(s, 7)),
        "cagr_10y_pct": _pct(point_return(s, 10)),
        "cagr_si_pct": _pct(cagr_si),
        "sip_cagr_5y_pct": _pct(sip_cagr(s, 5)),
        "sip_cagr_10y_pct": _pct(sip_cagr(s, 10)),
        "vol_ann_pct": _pct(vol),
        "downside_dev_pct": _pct(ddev),
        "max_drawdown_pct": round(dd * 100, 2) if dd is not None else None,
        "max_drawdown_date": dd_date,
        "sharpe_3y": round(sharpe, 2) if sharpe is not None else None,
        "sortino_3y": round(sortino, 2) if sortino is not None else None,
        "calmar_5y": round(calmar, 2) if calmar is not None else None,
        "best_calendar_year_pct": best_year,
        "worst_calendar_year_pct": worst_year,
    }
    for y in (1, 3, 5):
        out.update(rolling_cagr(s, y))
    return out


def _pct(x: float | None) -> float | None:
    return round(x * 100, 2) if x is not None else None


def flatten_allocation(code: int, raw: dict) -> dict:
    aa = raw.get("asset_allocation") or {}
    th = raw.get("top_holdings") or {}
    return {
        "scheme_code": code,
        "equity_pct": _num(raw.get("equity_per") or aa.get("equity")),
        "debt_pct": _num(raw.get("debt_per") or aa.get("debt")),
        "cash_pct": _num(raw.get("cash_per") or aa.get("cash")),
        "real_estate_pct": _num(aa.get("Real Estate")),
        "commodities_pct": _num(aa.get("commodities")),
        "hedged_equity_pct": _num(aa.get("Hedged Equity")),
        "large_cap_pct": _num(raw.get("large_cap")),
        "mid_cap_pct": _num(raw.get("mid_cap")),
        "small_cap_pct": _num(raw.get("small_cap")),
        "top5_pct": _num(th.get("top_five_corpus_per")),
        "top10_pct": _num(th.get("top_ten_corpus_per")),
        "top20_pct": _num(th.get("top_twenty_corpusPer")),
        "pe": _num(raw.get("pe")),
        "pb": _num(raw.get("pb")),
        "portfolio_turnover": _num(raw.get("portfolio_turnover")),
        "total_holdings": raw.get("total_holdings"),
        "aum_cr_groww": _num(raw.get("aum")),
    }


def flatten_sectors(code: int, raw: dict) -> list[dict]:
    sectors = raw.get("equity_sector_per") or {}
    rows = []
    for name, val in sectors.items():
        v = _num(val)
        if v is None or abs(v) < 0.01:
            continue
        rows.append({"scheme_code": code, "sector": name, "weight_pct": v})
    return rows


def _num(x) -> float | None:
    try:
        if x is None or x == "":
            return None
        return round(float(x), 4)
    except (TypeError, ValueError):
        return None


def process_one(row: dict) -> tuple[dict, dict, list[dict], pd.DataFrame]:
    code = row["scheme_code"]
    nav = fetch_nav_history(code)
    kpis = compute_kpis(nav)
    alloc_raw = fetch_allocation(code)
    alloc = flatten_allocation(code, alloc_raw)
    sectors = flatten_sectors(code, alloc_raw)
    nav = nav.copy()
    nav["scheme_code"] = code
    rec = {**row, **kpis, **alloc}
    rec.pop("scheme_code", None)
    rec = {"scheme_code": code, **rec}
    return rec, alloc, sectors, nav[["scheme_code", "date", "nav"]]


def mfdata_available() -> bool:
    data = get_json(MFDATA_S, f"{MFDATA}/schemes", params={"limit": 1}, timeout=12)
    return isinstance(data, dict) and data.get("status") == "success"


def write_dashboard(kpis: pd.DataFrame, alloc: pd.DataFrame) -> None:
    cats = sorted(kpis["category"].dropna().unique())
    cards = []
    for cat in cats:
        sub = kpis[kpis["category"] == cat]
        n = len(sub)
        med3 = sub["cagr_3y_pct"].median()
        med5 = sub["cagr_5y_pct"].median()
        cards.append(
            f"<div class='card'><h3>{cat.replace('_', ' ')}</h3>"
            f"<div class='n'>{n} funds</div>"
            f"<div>Median 3Y CAGR <b>{_fmt(med3)}%</b></div>"
            f"<div>Median 5Y CAGR <b>{_fmt(med5)}%</b></div></div>"
        )
    top = kpis.sort_values("roll_3y_mean_pct", ascending=False).head(15)
    rows = []
    for _, r in top.iterrows():
        rows.append(
            "<tr>"
            f"<td>{r['name'][:48]}</td><td>{r['category']}</td>"
            f"<td>{_fmt(r.get('cagr_3y_pct'))}</td>"
            f"<td>{_fmt(r.get('cagr_5y_pct'))}</td>"
            f"<td>{_fmt(r.get('roll_3y_mean_pct'))}</td>"
            f"<td>{_fmt(r.get('roll_3y_positive_pct'))}</td>"
            f"<td>{_fmt(r.get('max_drawdown_pct'))}</td>"
            f"<td>{_fmt(r.get('sharpe_3y'))}</td>"
            f"<td>{_fmt(r.get('equity_pct'))}</td>"
            f"<td>{_fmt(r.get('large_cap_pct'))}/{_fmt(r.get('mid_cap_pct'))}/{_fmt(r.get('small_cap_pct'))}</td>"
            "</tr>"
        )
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Equity fund KPIs</title>
<style>
body{{font-family:Segoe UI,sans-serif;margin:24px;background:#111;color:#eee}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}}
.card{{background:#1c1c1c;padding:12px;border:1px solid #333}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:16px}}
th,td{{border-bottom:1px solid #333;padding:6px 8px;text-align:left}}
th{{color:#9ad}}
.n{{color:#888;font-size:12px}}
</style></head><body>
<h1>Direct Growth equity funds</h1>
<p>AMFI universe + mfapi NAV history + Groww allocation. Generated {datetime.now():%Y-%m-%d %H:%M}.</p>
<div class="grid">{''.join(cards)}</div>
<h2>Highest 3-year rolling mean CAGR</h2>
<table><thead><tr>
<th>Fund</th><th>Category</th><th>3Y</th><th>5Y</th><th>Roll 3Y mean</th>
<th>Roll 3Y +ve %</th><th>Max DD</th><th>Sharpe 3Y</th><th>Equity %</th><th>L/M/S %</th>
</tr></thead><tbody>{''.join(rows)}</tbody></table>
</body></html>"""
    (OUT / "dashboard.html").write_text(html, encoding="utf-8")


def _fmt(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.2f}" if isinstance(v, float) else str(v)


def main() -> None:
    print("1/4 AMFI universe (NAVAll.txt)", flush=True)
    universe = fetch_amfi_universe()
    universe.to_csv(OUT / "universe.csv", index=False)
    limit = int(os.environ.get("EQUITY_LIMIT", "0") or 0)
    if limit > 0:
        universe = universe.groupby("category", group_keys=False).head(max(1, limit // 6)).reset_index(drop=True)
        print(f"   EQUITY_LIMIT sample -> {len(universe)} schemes", flush=True)
    print(f"   {len(universe)} Direct Growth schemes", flush=True)
    print(universe["category"].value_counts().to_string(), flush=True)

    print("2/4 Groww catalog (TER / AUM / manager)", flush=True)
    catalog = fetch_groww_catalog()
    print(f"   {len(catalog)} Groww Direct Growth rows", flush=True)
    universe["expense_ratio"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("expense_ratio"))
    universe["aum_cr"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("aum_cr"))
    universe["fund_manager"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("fund_manager"))
    universe["risk_label"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("risk"))
    universe["min_sip"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("min_sip"))
    universe["exit_load"] = universe["scheme_code"].map(lambda c: (catalog.get(c) or {}).get("exit_load"))

    print("3/4 mfdata.in probe", flush=True)
    print("   available" if mfdata_available() else "   down / skipped", flush=True)

    print("4/4 NAV history + allocation + KPIs", flush=True)
    records, allocs, sectors, navs = [], [], [], []
    rows = universe.to_dict("records")
    done = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process_one, row): row["scheme_code"] for row in rows}
        for fut in as_completed(futs):
            code = futs[fut]
            done += 1
            try:
                rec, alloc, sec, nav = fut.result()
                records.append(rec)
                allocs.append(alloc)
                sectors.extend(sec)
                if not nav.empty:
                    navs.append(nav)
                print(
                    f"   [{done}/{len(rows)}] {code}  "
                    f"pts={rec.get('nav_points')}  5y={rec.get('cagr_5y_pct')}  "
                    f"eq={rec.get('equity_pct')}",
                    flush=True,
                )
            except Exception as exc:
                print(f"   [{done}/{len(rows)}] {code} FAIL {exc}", flush=True)

    kpis = pd.DataFrame(records)
    extra = universe[
        [
            "scheme_code",
            "expense_ratio",
            "aum_cr",
            "fund_manager",
            "risk_label",
            "min_sip",
            "exit_load",
        ]
    ]
    if "expense_ratio" in kpis.columns:
        kpis = kpis.drop(columns=["expense_ratio", "aum_cr", "fund_manager", "risk_label", "min_sip", "exit_load"], errors="ignore")
    kpis = kpis.merge(extra, on="scheme_code", how="left")
    kpis.to_csv(OUT / "kpis.csv", index=False)
    pd.DataFrame(allocs).to_csv(OUT / "allocation.csv", index=False)
    pd.DataFrame(sectors).to_csv(OUT / "sectors.csv", index=False)
    if navs:
        hist = pd.concat(navs, ignore_index=True)
        hist.to_csv(OUT / "nav_history.csv", index=False)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sources": {
            "amfi": AMFI_NAVALL,
            "mfapi": MFAPI,
            "groww_search": f"{GROWW}/v1/api/search/v1/derived/scheme",
            "groww_allocation": f"{GROWW}/v1/api/data/mf/web/v1/scheme/portfolio/{{code}}/stats",
            "mfdata.in": "unavailable" if not (CACHE / "mfdata_ok").exists() else "ok",
        },
        "funds": int(len(kpis)),
        "by_category": kpis["category"].value_counts().to_dict() if len(kpis) else {},
        "with_nav_history": int((kpis["nav_points"] > 20).sum()) if len(kpis) else 0,
        "with_allocation": int(kpis["equity_pct"].notna().sum()) if len(kpis) else 0,
        "with_5y_cagr": int(kpis["cagr_5y_pct"].notna().sum()) if len(kpis) else 0,
        "with_10y_cagr": int(kpis["cagr_10y_pct"].notna().sum()) if len(kpis) else 0,
        "gaps": [
            "Stock-level holdings list is not in AMFI/mfapi; Groww stats give allocation % and sectors, not the full stock list.",
            "mfdata.in (holdings API) was down with HTTP 522 at build time.",
            "Expense ratio / AUM come from Groww and may be missing for a few AMFI codes.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    if len(kpis):
        write_dashboard(kpis, pd.DataFrame(allocs))
    print("\nDONE", json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
