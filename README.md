# MF Desk

Educational tool for Indian **Direct Growth equity mutual funds**. Rank all two-fund combinations, compare full factsheets (not only stock overlap), run 15-year base / bear / bull forecasts with editable lumpsum & SIP, replay real NAV history (2016 / 2019 / 2021), and see India CPI inflation on the same screen.

> Not investment advice. Past NAV history is real; forecasts are planning models only.

---

## Features

| Area | What you get |
|------|----------------|
| **Best pairs** | All **1,225** pairs from **50** Direct Growth funds, scored on ~10Y history, overlap, fit, and 15Y base forecast |
| **Compare & plan** | Category presets (Flexi + Mid, etc.), full fund cards (returns, risk, sectors, holdings), overlap table, year-by-year tables |
| **Your amounts** | Change lumpsum, monthly SIP, and horizon — tables recalculate |
| **Inflation** | India CPI year chart + “today’s rupees” column (≈5.5% planning average) |
| **Concepts** | Base / bear / bull, CAGR, overlap, drawdown, SEBI categories |

Default plan: **₹3 lakh lumpsum + ₹15,000/month SIP · 15 years**.

---

## Quick start

**Requirements:** Node.js 18+, npm. Python 3.10+ only if you refresh data.

```bash
cd desk-app
npm install
npm run install:all
npm run dev
```

| Service | URL |
|---------|-----|
| React UI | http://localhost:5177 |
| Express API | http://localhost:4177 |

Production-style (build UI, serve from API):

```bash
cd desk-app
npm run install:all
npm run build
npm start
# open http://localhost:4177
```

---

## Repository layout

```
mf/
├── desk-app/                 # Main product (React + Node)
│   ├── client/               # Vite + React UI
│   └── server/               # Express API (reads output/equity)
├── pipeline/                 # Python: fetch NAV, build pair rankings
├── output/equity/            # Generated JSON / CSV the app uses
├── archive/
│   ├── html/                 # Older static HTML explorers
│   └── debt/                 # Separate IDCW / debt experiments
└── README.md
```

---

## App pages

| Route | Purpose |
|-------|---------|
| `/` | Best pairs — filter by category, max overlap, sort by score / history / forecast |
| `/compare` | Pick two funds, set amounts, full details + inflation + year tables |
| `/learn` | Glossary and category guide |
| `/inflation` | Redirects to `/compare#inflation` |

---

## Data pipeline (optional refresh)

From the **repo root**:

```bash
pip install -r pipeline/requirements.txt

python pipeline/equity_pipeline.py      # AMFI + mfapi.in NAV + Groww KPIs
python pipeline/select_50.py            # 50-fund shortlist
python pipeline/build_whatif_data.py    # Holdings + monthly NAV from 2021
python pipeline/build_combo_risk.py     # 2019 pairs + themes
python pipeline/build_plan_detail.py    # Expert pairs + 15Y detail JSON
python pipeline/build_all_pairs.py      # All 1,225 pairs + inflation block
```

Optional legacy HTML (writes under `archive/html/`):

```bash
python pipeline/generate_html_explorer.py
python pipeline/generate_analysis_pages.py
python pipeline/generate_plan_app.py
```

The React app needs at least:

- `output/equity/plan_detail.json`
- `output/equity/all_pairs.json`

---

## API (Node)

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Liveness |
| `GET /api/meta` | Concepts, presets, inflation, sources |
| `GET /api/funds` | Full 50-fund list |
| `GET /api/funds/:code` | One fund + holdings |
| `GET /api/pairs` | Filtered / sorted pair leaderboard |
| `GET /api/compare?a=&b=&split=&lump=&sip=&years=&histStart=` | Full compare payload |
| `GET /api/inflation` | CPI series |

---

## Data validity — where to verify

| What we show | Source | How you verify |
|--------------|--------|----------------|
| NAV history (month-end) | [mfapi.in](https://api.mfapi.in/) (AMFI daily NAV) | [AMFI NAV history](https://www.amfiindia.com/net-asset-value/nav-history) |
| Scheme codes, category, latest NAV | [AMFI NAVAll.txt](https://www.amfiindia.com/spages/NAVAll.txt) | Same file |
| Holdings / overlap / AUM / TER | Groww portfolio snapshot | AMC factsheet, Value Research, Morningstar |
| India inflation % | MoSPI CPI–style **planning averages** (~5.5% long-term) | [MoSPI](https://www.mospi.gov.in/) / [RBI](https://www.rbi.org.in/) |

**History** = real published NAVs. **Base / bear / bull** = educational projections (fund track-record CAGR ± about 2–4%), not guarantees. Holdings are a monthly snapshot and change over time.

Quick check for one scheme (example Parag Parikh Flexi Cap Direct Growth ≈ code `122639`):

`https://api.mfapi.in/mf/122639`

---

## Tech stack

- **Frontend:** React 19, React Router, Vite  
- **Backend:** Node.js, Express  
- **Data:** Python (pandas, numpy, requests), AMFI / mfapi.in / Groww  

---

## Disclaimer

For education and personal research only. Not a recommendation to buy or sell any fund. Tax, exit loads, and expense ratios affect real outcomes; verify on the AMC / AMFI before investing.
