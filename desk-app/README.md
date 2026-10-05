# MF Desk (React + Node)

## Setup

```bash
npm install
npm run install:all
npm run dev
```

- UI: http://localhost:5177
- API: http://localhost:4177

## Pages

| Route | What it does |
|-------|----------------|
| `/` | Best pairs — 1,225 combos, filter and sort |
| `/compare` | Amounts + two funds + full factsheets + inflation + year tables |
| `/learn` | Base / bear / bull and category guide |

Inflation lives on **Compare & plan** (not a separate page). Change lumpsum, SIP and years there.

Data files: `../output/equity/plan_detail.json` and `all_pairs.json`. Rebuild with `python ../pipeline/build_all_pairs.py`.
