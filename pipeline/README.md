# Data pipeline

Run from the **mf** folder (parent of `pipeline/`).

```bash
python pipeline/equity_pipeline.py      # AMFI + mfapi NAV + Groww KPIs
python pipeline/select_50.py            # 50-fund shortlist
python pipeline/build_whatif_data.py    # holdings + monthly NAV
python pipeline/build_combo_risk.py     # 2019 pairs + themes
python pipeline/build_plan_detail.py    # expert pairs + 15Y tables
python pipeline/build_all_pairs.py      # all 1,225 combos + inflation
python pipeline/generate_html_explorer.py
python pipeline/generate_analysis_pages.py
python pipeline/generate_plan_app.py    # writes archive/html/
```

HTML generators write into `../archive/html/`. The React app reads `../output/equity/*.json`.
