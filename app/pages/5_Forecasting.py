# Forecasting page — Dataset 1
# Four models projected to 2040, confidence intervals, what-if slider.

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge, yr70,
    GD, GM, GL, RED, AMB, BLUE, SLATE, GREY, BORD,
    FONT_MONO, CHART_CFG, axis_style,
)

st.set_page_config(page_title="Forecasting — Waste Analytics", layout="wide")
d = init()
page_header("Forecasting")

rates = d['rates']
years = d['years']
merthyr = d['merthyr']
fut_lbl = d['fut_lbl']
lr_p = d['lr_p']; ar_p = d['ar_p']; ar_lo = d['ar_lo']; ar_hi = d['ar_hi']
ho_p = d['ho_p']; ss_p = d['ss_p']
mr = d['mr']; gap = d['gap']
merthyr_hh_2024 = d['merthyr_hh_2024']

st.markdown(f'<p style="font-size:0.78rem;color:{GREY}">{badge("Dataset 1")} &nbsp; ARIMA(1,1,0), Holt\'s Exponential Smoothing, and SSA applied to 12-year recycling rate series</p>', unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
kpi(c1, yr70(lr_p,fut_lbl), "Linear Regression",   "Optimistic — ignores plateau", GL)
kpi(c2, yr70(ar_p,fut_lbl), "ARIMA(1,1,0)",         "Captures momentum slowdown",   AMB)
kpi(c3, yr70(ho_p,fut_lbl), "Holts Exp Smoothing",  "Most realistic — damped trend",RED)
kpi(c4, yr70(ss_p,fut_lbl), "SSA (L=6)",            "Model-free trend extension",   BLUE)

sec("Recycling Rate Forecast to 2040 — Four Models")
all_yrs  = years + fut_lbl
hist_ext = list(rates) + [None]*len(fut_lbl)

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=fut_lbl+fut_lbl[::-1], y=list(ar_hi)+list(ar_lo[::-1]),
    fill="toself", fillcolor="rgba(230,126,34,0.08)", line=dict(width=0),
    name="ARIMA 95% CI", hoverinfo="skip"))
fig.add_trace(go.Scatter(
    x=all_yrs, y=hist_ext, mode="lines+markers", name="Historical",
    line=dict(color=GD, width=3),
    marker=dict(size=8,color=GD,line=dict(width=2,color="white"))))
fig.add_trace(go.Scatter(
    x=fut_lbl, y=list(lr_p), mode="lines", name="Linear Regression",
    line=dict(color=GL, width=1.8, dash="dot")))
fig.add_trace(go.Scatter(
    x=fut_lbl, y=list(ar_p), mode="lines", name="ARIMA(1,1,0)",
    line=dict(color=AMB, width=2.2, dash="dash")))
fig.add_trace(go.Scatter(
    x=fut_lbl, y=list(ho_p), mode="lines", name="Holts Smoothing",
    line=dict(color=RED, width=2.5)))
fig.add_trace(go.Scatter(
    x=fut_lbl, y=list(ss_p), mode="lines", name="SSA (L=6, 1 eigentriple)",
    line=dict(color=BLUE, width=2.2, dash="dashdot")))
fig.add_hline(y=70, line_dash="dash", line_color=RED, line_width=1.5,
    annotation_text="70% Target", annotation_position="top right",
    annotation_font_color=RED, annotation_font_size=11)
fig.add_vrect(x0="2023-24", x1=fut_lbl[-1], fillcolor="#FFFBEB", opacity=0.4, line_width=0,
    annotation_text="Forecast Zone", annotation_position="top left",
    annotation_font_size=10, annotation_font_color=AMB)
fig.update_layout(height=450,
    yaxis=dict(range=[38,95], title="Rate (%)", **axis_style()),
    xaxis=dict(tickangle=-45, nticks=18, categoryorder="array",
               categoryarray=all_yrs, **axis_style()),
    legend=dict(orientation="h", y=-0.18, font_size=11), **CHART_CFG)
st.plotly_chart(fig, use_container_width=True)

alert("<b>Central finding (D1):</b> ARIMA and Holts both account for the 2018 deceleration and agree: the 70% target is unreachable by 2040 at the current pace of +0.5pp/yr. Linear Regression ignores the plateau and is not reliable.", RED, "#FEF2F2")
alert("<b>SSA note:</b> SSA projects a more optimistic path, reaching 70% around 2028-29 (68.3% in 2025-26). SSA captures the full 12-year smooth trend and does not isolate the post-2018 plateau. ARIMA and Holts are more reliable for planning.", BLUE, "#EFF6FF")
if merthyr_hh_2024:
    alert(f"<b>Context from D3:</b> Merthyr has already reduced residual waste to {int(merthyr_hh_2024)} kg/person — below the Wales average. The challenge is converting this volume reduction into a higher recycling rate through food waste separation and contamination reduction.", BLUE, "#EFF6FF")

col_l, col_r = st.columns([3, 2])
with col_l:
    sec("Model Output Table — Next 10 Years")
    fc_tbl = pd.DataFrame({
        "Year":fut_lbl[:10],
        "Linear Reg (%)":np.round(lr_p[:10],2),
        "ARIMA(1,1,0) (%)":np.round(ar_p[:10],2),
        "Holts Smoothing (%)":np.round(ho_p[:10],2),
        "SSA L=6 (%)":np.round(ss_p[:10],2),
    })
    def style_table(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for col in ["Linear Reg (%)","ARIMA(1,1,0) (%)","Holts Smoothing (%)","SSA L=6 (%)"]:
            styles[col] = df[col].apply(lambda v: f"color:{GD};font-weight:700" if isinstance(v,float) and v>=70 else "")
        return styles
    st.dataframe(fc_tbl.style.apply(style_table,axis=None).format({c:"{:.2f}" for c in fc_tbl.columns[1:]}),
        use_container_width=True, hide_index=True, height=380)

with col_r:
    sec("What-If: Required Annual Improvement")
    tgt_yr = st.slider("Target year to reach 70%", 2026, 2040, 2030, key="forecast_target")
    yrs_nd = tgt_yr - 2024
    req_pp = (70 - mr) / yrs_nd if yrs_nd > 0 else 0
    rec3   = float(merthyr["YoY"].dropna().iloc[-3:].mean())
    mult   = req_pp / rec3 if rec3 > 0 else 99
    st.markdown("<br>", unsafe_allow_html=True)
    kpi(st, f"{req_pp:.2f} pp/yr", "Required annual rate",   f"to reach 70% by {tgt_yr}", GM)
    st.markdown("<br>", unsafe_allow_html=True)
    kpi(st, f"{mult:.1f}x",         "Multiple of current pace", f"recent avg: {rec3:.2f} pp/yr", AMB)
    st.markdown("<br>", unsafe_allow_html=True)
    kpi(st, f"{gap:.1f}pp",         "Total gap to close",   f"from {mr:.1f}% to 70%", RED)
