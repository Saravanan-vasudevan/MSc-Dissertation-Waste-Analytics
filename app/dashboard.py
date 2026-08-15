# Entry point for the Streamlit app. This file doubles as the "Overview" page.
# The other pages live in app/pages/ and Streamlit picks them up automatically.
#
# Run with:  streamlit run app/dashboard.py   (from the project root)

import streamlit as st
import plotly.graph_objects as go

# shared.py is in the same directory — Streamlit adds app/ to sys.path
# when it runs dashboard.py, so this import just works.
from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, MINT, RED, AMB, BLUE, SLATE, GREY, BORD,
    FONT_MONO, CHART_CFG, axis_style,
)

st.set_page_config(
    page_title="Merthyr Tydfil — Waste Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={},
)

d = init()
page_header("Overview")

# ── KPI row ──────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6 = st.columns(6)
kpi(c1, f"{d['mr']:.1f}%",    "Recycling Rate 2023-24", f"Rank #{d['rank']} of 22",      GM)
kpi(c2, f"{d['gap']:.1f}pp",  "Gap to 70% Target",      "Welsh Govt target",        RED)
kpi(c3, f"+{d['imp']:.1f}pp", "Recycling Improvement",  "2012 to 2024",             GD)
kpi(c4, f"#{d['rank']}",      "Welsh Council Rank",     "out of 22",                AMB)
kpi(c5, f"{int(d['merthyr_hh_2024'])} kg" if d['merthyr_hh_2024'] else "—",
        "Residual per Person",    "2023-24 Merthyr",          BLUE)
kpi(c6, ">2040",         "Forecast: Reach 70%",    "ARIMA + Holts consensus",  SLATE)

# ── 12-year trend with forecast overlay ──────────────────────────────────────
sec("12-Year Trend with Forecast  —  Dataset 1")
col_l, col_r = st.columns([3, 2])
with col_l:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d['years'], y=d['rates'], mode="lines+markers", name="Historical",
        line=dict(color=GM, width=2.5),
        marker=dict(size=7, color=GD, line=dict(width=2, color="white"))))
    fig.add_trace(go.Scatter(
        x=d['fut_lbl'], y=list(d['ho_p']), mode="lines", name="Holts Forecast",
        line=dict(color=AMB, width=2, dash="dot")))
    fig.add_trace(go.Scatter(
        x=d['fut_lbl'], y=list(d['ar_p']), mode="lines", name="ARIMA Forecast",
        line=dict(color=RED, width=1.8, dash="dash")))
    fig.add_hline(y=70, line_dash="dash", line_color=RED, line_width=1.5,
        annotation_text="70% Target", annotation_position="top right",
        annotation_font_color=RED, annotation_font_size=11)
    fig.add_vrect(x0="2023-24", x1=d['fut_lbl'][-1], fillcolor="#FFFBEB", opacity=0.5, line_width=0)
    fig.update_layout(height=300,
        yaxis=dict(range=[38,76], title="Rate (%)", **axis_style()),
        xaxis=dict(tickangle=-40, **axis_style()),
        legend=dict(orientation="h", y=-0.25, font_size=11), **CHART_CFG)
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown("<br>", unsafe_allow_html=True)
    alert("<b>Strong baseline (D1):</b> Merthyr gained +15.1pp over 12 years.", GM, "#E8F5E9")
    alert("<b>Critical slowdown (D1):</b> Pace dropped from 2.1 to 0.5 pp/yr after 2018 — 74% reduction.", AMB, "#FFF8E7")
    alert("<b>Target at risk (D1):</b> ARIMA and Holts agree 70% is unreachable by 2040 without policy action.", RED, "#FEF2F2")
    if d['merthyr_hh_2024'] and d['wales_hh_2024']:
        alert(f"<b>Residual progress (D3):</b> Merthyr reduced residual waste to {int(d['merthyr_hh_2024'])} kg/person — below Wales average of {int(d['wales_hh_2024'])} kg.", BLUE, "#EFF6FF")

# ── Roadmap cards ────────────────────────────────────────────────────────────
sec("Analysis Roadmap — 3 Datasets, 4 Steps")
steps = [
    ("01","Trend Analysis","D1: 12-year recycling rate time series + phase change",GD),
    ("02","Residual Waste","D3: Residual kg/person — Merthyr vs all 22 councils",BLUE),
    ("03","Benchmarking","D1: Rank Merthyr across all 22 Welsh councils",AMB),
    ("04","Forecasting","D1: ARIMA & Holts projection to 2040 with what-if",RED),
]
cols = st.columns(4)
for col,(num,ttl,desc,clr) in zip(cols,steps):
    col.markdown(f"""<div style="background:white;border-radius:10px;padding:1.1rem;
         border-top:3px solid {clr};border:1px solid {BORD};height:160px;">
      <div style="font-size:1.6rem;font-weight:800;color:{clr};font-family:{FONT_MONO};line-height:1">{num}</div>
      <div style="font-weight:700;font-size:0.88rem;color:{SLATE};margin:0.5rem 0 0.4rem">{ttl}</div>
      <div style="font-size:0.77rem;color:{GREY};line-height:1.4">{desc}</div>
    </div>""", unsafe_allow_html=True)
