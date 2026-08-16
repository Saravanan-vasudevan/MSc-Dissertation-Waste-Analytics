# Merthyr Tydfil Waste Analytics

MSc dissertation project — 12 years of Welsh council waste data, a Streamlit dashboard, and the statistical scripts behind the figures in the dissertation.

Built for *Data Analytics for Enhanced Waste Management Decision Making: A Case Study of Merthyr Tydfil County Borough Council* (Cardiff University, April 2026).

---

## Dashboard Previews

### Executive Overview
![Executive Overview](assets/Screenshot%202026-08-16%20015123.png)

### Multi-Model Forecasting to 2040
![Forecasting Projections](assets/Screenshot%202026-08-16%20015254.png)

### Local Authority Benchmarking (22 Welsh Councils)
![Council Benchmarking](assets/Screenshot%202026-08-16%20015325.png)

---

## How to Run

You need Python 3.9+ and about two minutes.

**Option A — Make (recommended):**

```bash
git clone https://github.com/Saravanan-vasudevan/merthyr-waste-analytics.git
cd merthyr-waste-analytics
make setup   # creates .venv, installs deps
make run     # starts Streamlit on localhost:8501
```

**Option B — Manual:**

```bash
git clone https://github.com/Saravanan-vasudevan/merthyr-waste-analytics.git
cd merthyr-waste-analytics
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/dashboard.py
```

**Option C — Docker:**

```bash
docker compose up --build
```

Dashboard opens at `http://localhost:8501` in all cases.

No internet connection needed at runtime — fonts are system-native, all data is bundled.

## What's in the Dashboard

Six pages, split into separate files under `app/pages/` so each one stays readable:

- **Overview** — KPI cards, 12-year trend with forecast overlay
- **Trend Analysis** — full time series, YoY change bars, growth-vs-plateau phase comparison
- **Residual Waste** — per-person residual kg, Merthyr vs Wales average, all-council heatmap
- **Council Comparison** — pick any councils to benchmark side-by-side against Merthyr
- **Benchmarking** — all 22 councils ranked, improvement since 2012, year slider
- **Forecasting** — ARIMA, Holt's, SSA, and Linear Regression out to 2040, with a what-if tool

## Analysis Scripts

These produce the figures and diagnostic output used in the dissertation. Each one reads the Merthyr recycling series from `src/data_loader.py` so the numbers stay in sync. Run them individually:

```bash
python analysis/model_diagnostics.py          # SSA MAE, Holt's residuals, Ljung-Box
python analysis/generate_ssa_figures.py        # scree plot, trend reconstruction, w-corr, forecast
python analysis/generate_acf_pacf_figures.py   # ADF test, ACF/PACF panels
python analysis/trend_significance_tests.py    # Mann-Kendall, Spearman, ITM
python analysis/ssa_parameter_grid_search.py   # L x r RMSE heatmap
```

Or all at once: `make analysis`

## Data

Three StatsWales datasets under the Open Government Licence, covering all 22 Welsh local authorities from 2012-13 to 2023-24:

1. **Recycling rates** - one CSV per year in `data/raw/recycling_*.csv` (the column order isn't consistent across years - see `src/data_loader.py` for how we handle that)
2. **Waste generation by source** - `data/raw/Waste_Generation_data.csv` (Wales-wide aggregate, 6 header rows to skip)
3. **Residual household waste per person** - `data/raw/household_waste_data.csv` (different layout from the recycling files)

`data/processed/merthyr_recycling_rates.csv` is a derived file — regenerate it with `make processed` or `python -c "from src.data_loader import write_processed_csv; write_processed_csv()"`.

## Project Structure

```
├── app/
│   ├── dashboard.py          Streamlit entry point (Overview page)
│   ├── shared.py             CSS, colours, data loading, chart helpers
│   └── pages/
│       ├── 1_Trend_Analysis.py
│       ├── 2_Residual_Waste.py
│       ├── 3_Council_Comparison.py
│       ├── 4_Benchmarking.py
│       ├── 5_Forecasting.py
│       └── 6_Waste_by_Source.py
├── analysis/                 Scripts that generate dissertation figures
├── src/data_loader.py        Single source of truth for the recycling series
├── scripts/explore_raw_data.py   Dev helper for eyeballing raw CSVs
├── data/raw/                 Source CSVs from StatsWales
├── data/processed/           Derived series (generated, not hand-edited)
├── figures/                  Output PNGs from analysis scripts (gitignored)
├── Makefile
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Key Findings

The short version: Merthyr improved from 49.1% to 64.3% recycling over 12 years, but progress flatlined after 2018. ARIMA and Holt's models both say 70% is out of reach by 2040 at the current pace. The gap is 5.7 percentage points and the most likely fix is mandatory food waste separation - every Welsh council above 70% already does it.

Merthyr's residual waste per person (110 kg) is the lowest in Wales, so the problem isn't that residents are producing too much rubbish - it's that the recyclable fraction of what's left isn't being captured.

## License

MIT - see [LICENSE](LICENSE).

## Author

Saravanan Vasudevan — MSc Data Science and Analytics, Cardiff University
