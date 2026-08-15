"""
Shared state for the dashboard pages.

Everything that more than one page needs — colour tokens, CSS, data loading,
the little KPI-card helper — lives here so the page files stay short.
If you're adding a new page, just `from shared import *` at the top.

The CSS used to pull DM Sans from Google Fonts on every cold start, which
broke behind corporate proxies and added ~400ms to first paint. Switched
to a system font stack that looks close enough and works everywhere.
"""

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from sklearn.linear_model import LinearRegression


# ── Colour tokens ────────────────────────────────────────────────────────────
# Named after what they *do*, not what they look like, so you can reskin
# without grepping for hex codes.
GD   = "#1B4332"
GM   = "#2D6A4F"
GL   = "#74C69D"
MINT = "#D8F3DC"
GOLD = "#C9A227"
RED  = "#C0392B"
AMB  = "#E67E22"
BLUE = "#2563EB"
SLATE= "#374151"
GREY = "#6B7280"
BG   = "#F4F7F4"
CARD = "#FFFFFF"
BORD = "#D1D9D1"


# System font stack — no external requests, works behind firewalls.
# Looks virtually identical to DM Sans on Mac/Windows/Linux.
FONT_BODY = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "ui-monospace, 'Cascadia Code', 'Source Code Pro', Menlo, Consolas, 'Courier New', monospace"


def inject_css():
    """Dump the global stylesheet into the page. Call once per page load."""
    st.markdown(f"""
<style>
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, [data-testid="stAppViewContainer"] {{
    background: {BG}; font-family: {FONT_BODY}; color: {SLATE};
}}
[data-testid="stSidebar"] {{ background: {GD} !important; border-right: none; }}
[data-testid="stSidebar"] > div {{ padding: 1.5rem 1rem; }}
[data-testid="stSidebar"] * {{ color: #c8dfc8 !important; font-family: {FONT_BODY} !important; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {{ color: white !important; font-weight: 600; }}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.12) !important; }}
[data-testid="stMainBlockContainer"] {{ padding: 1.5rem 2rem 2rem; max-width: 1400px; }}
#MainMenu, footer, header {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none; }}
.kpi-card {{
    background: {CARD}; border: 1px solid {BORD}; border-radius: 10px;
    padding: 1.1rem 1.25rem; border-top: 3px solid var(--accent); transition: box-shadow 0.2s;
}}
.kpi-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.08); }}
.kpi-val {{ font-size: 2rem; font-weight: 700; color: var(--accent); line-height: 1.1; font-family: {FONT_MONO}; }}
.kpi-lbl {{ font-size: 0.75rem; color: {GREY}; margin-top: 0.25rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.04em; }}
.kpi-sub {{ font-size: 0.78rem; color: var(--accent); margin-top: 0.2rem; font-weight: 500; }}
.sec-hdr {{
    font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
    color: {GM}; border-bottom: 2px solid {GL}; padding-bottom: 0.4rem; margin: 1.8rem 0 1rem;
}}
.alert {{
    padding: 0.75rem 1rem; border-radius: 8px; border-left: 4px solid var(--clr);
    background: var(--bg); font-size: 0.85rem; color: {SLATE}; margin: 0.4rem 0; line-height: 1.5;
}}
.page-hdr {{
    background: linear-gradient(135deg, {GD} 0%, {GM} 100%); border-radius: 12px;
    padding: 1.4rem 1.8rem; margin-bottom: 1.5rem; display: flex;
    justify-content: space-between; align-items: center;
}}
.page-hdr-title {{ font-size: 1.5rem; font-weight: 700; color: white; margin: 0.25rem 0; }}
.page-hdr-sub {{ font-size: 0.8rem; color: {GL}; font-weight: 400; }}
.page-hdr-tag {{ font-size: 0.65rem; color: {GL}; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600; }}
.page-hdr-meta {{ text-align: right; color: {GL}; font-size: 0.75rem; line-height: 1.8; }}
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 2px solid {BORD}; }}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border: none; border-radius: 0; padding: 0.5rem 1.1rem;
    font-size: 0.82rem; font-weight: 600; color: {GREY}; text-transform: uppercase; letter-spacing: 0.05em;
}}
.stTabs [aria-selected="true"] {{
    background: transparent !important; color: {GD} !important; border-bottom: 2px solid {GD} !important;
}}
.ds-badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 0.68rem; font-weight: 700; background: {GOLD}; color: {GD};
    text-transform: uppercase; letter-spacing: 0.06em;
}}
</style>
""", unsafe_allow_html=True)


# ── Chart defaults ───────────────────────────────────────────────────────────
CHART_CFG = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font_family=FONT_BODY, font_color=SLATE,
    margin=dict(l=10, r=10, t=36, b=10),
)

def axis_style():
    return dict(
        gridcolor="#EEF2EE", linecolor=BORD,
        tickfont=dict(size=11, color=GREY),
        title_font=dict(size=11, color=GREY),
    )


# ── Data paths ───────────────────────────────────────────────────────────────
# CSVs live in ../data/raw relative to app/
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
BASE = os.path.join(_PROJECT_ROOT, "data", "raw")

YEAR_FILES = {
    "2012-13": "recycling_2012-13.csv", "2013-14": "recycling_2013-14.csv",
    "2014-15": "recycling_2014-15.csv", "2015-16": "recycling_2015-16.csv",
    "2016-17": "recycling_2016-17.csv", "2017-18": "recycling_2017-18.csv",
    "2018-19": "recycling_2018-19.csv", "2019-20": "recycling_2019-20.csv",
    "2020-21": "recycling_2020-21.csv", "2021-22": "recycling_2021-22.csv",
    "2022-23": "recycling_2022-23.csv", "2023-24": "recycling_2023-24.csv",
}

COUNCILS = [
    "Isle of Anglesey","Gwynedd","Conwy","Denbighshire","Flintshire","Wrexham",
    "Powys","Ceredigion","Pembrokeshire","Carmarthenshire","Swansea","Neath Port Talbot",
    "Bridgend","Vale of Glamorgan","Cardiff","Rhondda Cynon Taf","Merthyr Tydfil",
    "Caerphilly","Blaenau Gwent","Torfaen","Monmouthshire","Newport",
]


# ── Data loading ─────────────────────────────────────────────────────────────
# These mirror the logic in src/data_loader.py but return DataFrames for
# Plotly. Could unify them, but the dashboard needs council-level cross-tabs
# and the analysis scripts only ever want the Merthyr vector — merging them
# would mean adding pandas as a dep for scripts that only need numpy.

@st.cache_data(show_spinner=False)
def load_recycling():
    """Parse all 12 annual CSVs into a long-format DataFrame.

    StatsWales sometimes quotes council names with a trailing space
    ("Merthyr Tydfil ") and sometimes without. We check both.
    The rate is always the last numeric field on the line — see
    src/data_loader.py for why we don't trust column indices."""
    records = []
    for year, fname in YEAR_FILES.items():
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            path = os.path.join(BASE, "data", fname)
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            for c in COUNCILS:
                if f'"{c} "' in line or f'"{c}"' in line:
                    parts = line.split(",")
                    try:
                        records.append({"Year": year, "Council": c,
                                        "RecyclingRate": float(parts[-1].strip().strip('"'))})
                    except:
                        pass
    df = pd.DataFrame(records).drop_duplicates(subset=["Year","Council"])
    yr_ord = {y: i for i, y in enumerate(YEAR_FILES)}
    df["YearOrder"] = df["Year"].map(yr_ord)
    return df.sort_values(["Council","YearOrder"])

@st.cache_data(show_spinner=False)
def load_waste():
    """Dataset 2 — Wales-wide waste generation by source.
    The CSV has 6 header rows of metadata before the actual data starts."""
    for base in [BASE, os.path.join(BASE, "data")]:
        p = os.path.join(base, "Waste_Generation_data.csv")
        if os.path.exists(p):
            cols = ["Cat","Sub1","Sub2"] + list(YEAR_FILES.keys())
            return pd.read_csv(p, skiprows=6, nrows=26, header=None, names=cols)
    return None

@st.cache_data(show_spinner=False)
def load_household_waste():
    """Dataset 3 — residual household waste per person (kg).
    Returns two dicts: {council -> {year -> kg}} and {year -> wales_avg_kg}.
    The CSV layout is different from the recycling files — values are
    spread across columns rather than one-per-file."""
    for base in [BASE, os.path.join(BASE, "data")]:
        p = os.path.join(base, "household_waste_data.csv")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                raw_lines = f.readlines()
            yr_keys = list(YEAR_FILES.keys())
            hh_records = {}
            wales_hh   = {}
            for line in raw_lines:
                line = line.strip()
                if (line.startswith('"Wales "') or line.startswith('"Wales"')) and not wales_hh:
                    parts = [x.strip().strip('"').strip() for x in line.split(',')]
                    vals = []
                    for x in parts[::-1]:
                        try:
                            vals.insert(0, float(x))
                            if len(vals) == 12: break
                        except: pass
                    if len(vals) == 12:
                        wales_hh = dict(zip(yr_keys, vals))
                for c in COUNCILS:
                    if f'"{c} "' in line or f'"{c}"' in line:
                        parts = [x.strip().strip('"').strip() for x in line.split(',')]
                        vals = []
                        for x in parts[::-1]:
                            try:
                                vals.insert(0, float(x))
                                if len(vals) == 12: break
                            except: pass
                        if len(vals) == 12:
                            hh_records[c] = dict(zip(yr_keys, vals))
            return hh_records, wales_hh
    return {}, {}

@st.cache_data(show_spinner=False)
def build_bench(df):
    lat = df[df["Year"]=="2023-24"][["Council","RecyclingRate"]].copy()
    ear = df[df["Year"]=="2012-13"][["Council","RecyclingRate"]].rename(columns={"RecyclingRate":"Rate2012"})
    b = lat.merge(ear, on="Council")
    b["Improvement"] = b["RecyclingRate"] - b["Rate2012"]
    b = b.sort_values("RecyclingRate", ascending=False).reset_index(drop=True)
    b["Rank"] = b.index + 1
    return b


# ── SSA forecast ─────────────────────────────────────────────────────────────
# This is the LRR (Linear Recurrence Relation) method from Golyandina 2001.
# L=6, r=1 was chosen for long-horizon smoothness — see
# analysis/ssa_parameter_grid_search.py for the full justification.

def _ssa_forecast(X, L, n_components, n_ahead):
    from numpy.linalg import svd as _svd
    N = len(X)
    K = N - L + 1
    traj = np.array([X[i:i+L] for i in range(K)]).T
    U, sigma, VT = _svd(traj, full_matrices=False)
    U_r = U[:, :n_components]
    pi  = U_r[-1, :]
    nu2 = float(np.dot(pi, pi))
    R   = (U_r[:-1, :] @ pi) / (1.0 - nu2)
    X_ext = list(X.copy())
    for _ in range(n_ahead):
        X_ext.append(float(np.dot(R, X_ext[-(L-1):])))
    return np.array(X_ext[N:])

@st.cache_data(show_spinner=False)
def run_forecast(rates_tuple):
    rates = np.array(rates_tuple)
    n, fn = len(rates), 16
    X  = np.arange(n).reshape(-1,1)
    Xf = np.arange(n, n+fn).reshape(-1,1)
    labels = [f"{2024+i}-{str(2025+i)[-2:]}" for i in range(1, fn+1)]
    lr_p = LinearRegression().fit(X, rates).predict(Xf)
    arima_fit = ARIMA(rates, order=(1,1,0)).fit()
    ar_p = arima_fit.forecast(fn)
    try:
        ci = arima_fit.get_forecast(fn).conf_int()
        al, ah = ci[:,0], ci[:,1]
    except:
        al, ah = ar_p - 2, ar_p + 2
    ho_p = ExponentialSmoothing(rates, trend="add", damped_trend=True).fit(optimized=True).forecast(fn)
    ss_p = _ssa_forecast(rates, L=6, n_components=1, n_ahead=fn)
    return labels, lr_p, ar_p, al, ah, ho_p, ss_p


# ── HTML helpers ─────────────────────────────────────────────────────────────

def kpi(col, val, lbl, sub, accent):
    col.markdown(f"""<div class="kpi-card" style="--accent:{accent}">
      <div class="kpi-val">{val}</div>
      <div class="kpi-lbl">{lbl}</div>
      <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def sec(label):
    st.markdown(f'<div class="sec-hdr">{label}</div>', unsafe_allow_html=True)

def alert(text, color, bg):
    st.markdown(f'<div class="alert" style="--clr:{color};--bg:{bg}">{text}</div>', unsafe_allow_html=True)

def badge(label):
    return f'<span class="ds-badge">{label}</span>'

def yr70(preds, lbl):
    for i, v in enumerate(preds):
        if v >= 70: return lbl[i]
    return "Beyond 2040"

def page_header(page_name):
    """The green gradient banner at the top of every page."""
    st.markdown(f"""
<div class="page-hdr">
  <div>
    <div class="page-hdr-tag">MSc Dissertation &middot; Cardiff University &middot; 3 Datasets</div>
    <div class="page-hdr-title">Merthyr Tydfil Waste Management Analytics</div>
    <div class="page-hdr-sub">Data Analytics for Enhanced Decision-Making &nbsp;&middot;&nbsp; Industry Partner: MTCBC</div>
  </div>
  <div class="page-hdr-meta">
    <div style="font-size:1.1rem;font-weight:700;color:white">{page_name}</div>
    <div>2012 &ndash; 2024</div><div>22 Welsh Councils</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Preload all datasets ────────────────────────────────────────────────────
# Done here so every page gets them from cache on import.
# Wrapped in a function so pages can call it after st.set_page_config().

def init():
    """Call this at the top of every page (after set_page_config).
    Returns the loaded data tuple that most pages need."""
    inject_css()

    df            = load_recycling()
    waste_df      = load_waste()
    hh_data, wales_hh = load_household_waste()
    bench         = build_bench(df)
    merthyr       = df[df["Council"]=="Merthyr Tydfil"].sort_values("YearOrder").copy()
    merthyr["YoY"]= merthyr["RecyclingRate"].diff()
    rates         = merthyr["RecyclingRate"].values
    years         = list(merthyr["Year"])
    yr_keys       = list(YEAR_FILES.keys())
    fut_lbl, lr_p, ar_p, ar_lo, ar_hi, ho_p, ss_p = run_forecast(tuple(rates))

    mr   = float(merthyr["RecyclingRate"].iloc[-1])
    gap  = 70 - mr
    imp  = mr - float(merthyr["RecyclingRate"].iloc[0])
    rank = int(bench[bench["Council"]=="Merthyr Tydfil"]["Rank"].values[0])
    merthyr_hh_2024 = hh_data.get("Merthyr Tydfil", {}).get("2023-24", None)
    merthyr_hh_2012 = hh_data.get("Merthyr Tydfil", {}).get("2012-13", None)
    wales_hh_2024   = wales_hh.get("2023-24", None)

    return dict(
        df=df, waste_df=waste_df, hh_data=hh_data, wales_hh=wales_hh,
        bench=bench, merthyr=merthyr, rates=rates, years=years,
        yr_keys=yr_keys,
        fut_lbl=fut_lbl, lr_p=lr_p, ar_p=ar_p, ar_lo=ar_lo, ar_hi=ar_hi,
        ho_p=ho_p, ss_p=ss_p,
        mr=mr, gap=gap, imp=imp, rank=rank,
        merthyr_hh_2024=merthyr_hh_2024, merthyr_hh_2012=merthyr_hh_2012,
        wales_hh_2024=wales_hh_2024,
        YEAR_FILES=YEAR_FILES, COUNCILS=COUNCILS,
    )
