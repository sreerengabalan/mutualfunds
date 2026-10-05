"""Fetch holdings + monthly NAV (2021+) for the 50-fund HTML explorer."""
from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
EQ = ROOT / "output" / "equity"
HOLD_CACHE = EQ / "cache" / "holdings"
HOLD_CACHE.mkdir(parents=True, exist_ok=True)

GROWW = "https://groww.in/v1/api/data/mf/web/v1/scheme/search"

# Groww catalog omits most Large & Mid funds; old scheme names still work as slugs.
KNOWN_SLUGS = {
    119721: "sbi-magnum-multiplier-fund-direct-growth",
}


def session() -> requests.Session:
    s = requests.Session()
    s.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(total=3, backoff_factor=0.6, status_forcelist=(429, 502, 503, 504)),
            pool_maxsize=8,
        ),
    )
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": "https://groww.in/mutual-funds",
        }
    )
    return s


def norm_name(name: str) -> str:
    n = name.lower()
    n = re.sub(r"\b(limited|ltd|inc|corp|corporation|the)\b", "", n)
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def parse_holdings(raw) -> list[dict]:
    rows = []
    if not isinstance(raw, list):
        return rows
    for item in raw:
        if not isinstance(item, list) or len(item) < 9:
            continue
        kind = str(item[3] or "").upper()
        if kind not in {"EQUITY", "STOCK"}:
            continue
        try:
            w = float(item[8])
        except (TypeError, ValueError):
            continue
        if w <= 0:
            continue
        name = str(item[2] or "").strip()
        if not name:
            continue
        rows.append(
            {
                "n": name,
                "k": norm_name(name),
                "s": str(item[4] or ""),
                "w": round(w, 2),
            }
        )
    rows.sort(key=lambda x: -x["w"])
    return rows


def fetch_one(sess: requests.Session, code: int, search_id: str | None) -> list[dict]:
    path = HOLD_CACHE / f"{code}.json"
    if path.exists() and path.stat().st_size > 20:
        return json.loads(path.read_text(encoding="utf-8"))
    sid = search_id or KNOWN_SLUGS.get(code) or str(code)
    try:
        r = sess.get(f"{GROWW}/{sid}", timeout=20)
        data = r.json() if r.status_code == 200 else {}
    except Exception:
        data = {}
    rows = parse_holdings(data.get("holdings") if isinstance(data, dict) else None)
    path.write_text(json.dumps(rows), encoding="utf-8")
    time.sleep(0.05)
    return rows


def monthly_nav(codes: list[int]) -> dict[str, list]:
    hist = pd.read_csv(EQ / "nav_history.csv", parse_dates=["date"])
    hist = hist[hist["scheme_code"].isin(codes)]
    hist = hist[hist["date"] >= "2021-01-01"]
    out: dict[str, list] = {}
    for code, g in hist.groupby("scheme_code"):
        g = g.sort_values("date").set_index("date")
        m = g["nav"].resample("ME").last().dropna()
        out[str(int(code))] = [
            [d.strftime("%Y-%m-%d"), round(float(v), 4)] for d, v in m.items()
        ]
    return out


def main() -> None:
    funds = json.loads((EQ / "selected_50.json").read_text(encoding="utf-8"))
    catalog = json.loads((EQ / "cache" / "groww_meta" / "catalog.json").read_text(encoding="utf-8"))
    codes = [int(f["code"]) for f in funds]
    sess = session()
    holdings: dict[str, list] = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = {}
        for code in codes:
            meta = catalog.get(str(code)) or catalog.get(code) or {}
            sid = meta.get("search_id")
            futs[ex.submit(fetch_one, sess, code, sid)] = code
        for fut in as_completed(futs):
            code = futs[fut]
            try:
                rows = fut.result()
            except Exception:
                rows = []
            holdings[str(code)] = rows
            print(f"  {code} holdings {len(rows)}", flush=True)

    nav = monthly_nav(codes)
    payload = {"holdings": holdings, "nav": nav, "from": "2021-01-01"}
    (EQ / "whatif_data.json").write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    with_h = sum(1 for v in holdings.values() if v)
    with_n = sum(1 for v in nav.values() if len(v) >= 12)
    print("holdings", with_h, "/", len(codes), "nav series", with_n, "/", len(codes))
    print("bytes", (EQ / "whatif_data.json").stat().st_size)


if __name__ == "__main__":
    main()
