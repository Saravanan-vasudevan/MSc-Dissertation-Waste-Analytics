# Benchmarking page — Dataset 1
# All 22 councils ranked, improvement since 2012, heatmap.

import numpy as np
import streamlit as st
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, RED, AMB, SLATE, GREY, BORD,
    CHART_CFG, axis_style, YEAR_FILES,
)

st.set_page_config(page_title="Benchmarking — Waste Analytics", layout="wide")
d = init()
page_header("Benchmarking")

df = d['df']
bench = d['bench']

st.markdown(f'<p style="font-size:0.78rem;color:{GREY}">{badge("Dataset 1")} &nbsp; Annual recycling rates — all 22 Welsh Councils benchmarked</p>', unsafe_allow_html=True)

yr_sel = st.select_slider("Select year to benchmark",
    options=list(YEAR_FILES.keys()), value="2023-24", key="bench_year")
yr_data = df[df["Year"]==yr_sel].sort_values("RecyclingRate", ascending=False).copy()
yr_data["Rank"] = range(1, len(yr_data)+1)
m_row = yr_data[yr_data["Council"]=="Merthyr Tydfil"].iloc[0]
ab70  = (yr_data["RecyclingRate"]>=70).sum()

c1,c2,c3,c4 = st.columns(4)
kpi(c1, f"#{int(m_row['Rank'])}", "Merthyr Rank",     "of 22 councils",     AMB)
kpi(c2, f"{m_row['RecyclingRate']:.1f}%", "Rate",     yr_sel,               GM)
kpi(c3, f"{max(0,70-m_row['RecyclingRate']):.1f}pp", "Gap to 70%", "to close", RED)
kpi(c4, str(ab70), "Councils Above 70%", "have reached target", GD)

tab1, tab2, tab3 = st.tabs(["COUNCIL RANKINGS", "IMPROVEMENT SINCE 2012", "HEATMAP"])

with tab1:
    bar_clrs = [RED if c=="Merthyr Tydfil" else (GD if yr_data[yr_data["Council"]==c]["RecyclingRate"].values[0]>=70 else GL)
                for c in yr_data["Council"]]
    fig = go.Figure(go.Bar(
        x=yr_data["RecyclingRate"], y=yr_data["Council"],
        orientation="h", marker_color=bar_clrs, marker_line_width=0,
        text=[f"{v:.1f}%" for v in yr_data["RecyclingRate"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>"))
    fig.add_vline(x=70, line_dash="dash", line_color=RED, line_width=1.5,
        annotation_text="70% Target", annotation_position="top",
        annotation_font_color=RED, annotation_font_size=11)
    fig.update_layout(height=620,
        xaxis=dict(range=[0,82], title="Recycling Rate (%)", **axis_style()),
        yaxis=dict(autorange="reversed", **axis_style()), showlegend=False, **CHART_CFG)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<div style="font-size:0.78rem;color:{GREY};text-align:center;">Dark green = above 70% &nbsp;|&nbsp; Red = Merthyr Tydfil &nbsp;|&nbsp; Light green = below 70%</div>', unsafe_allow_html=True)

with tab2:
    bench_s = bench.sort_values("Improvement", ascending=False)
    fig2 = go.Figure(go.Bar(
        x=bench_s["Improvement"], y=bench_s["Council"],
        orientation="h",
        marker_color=[RED if c=="Merthyr Tydfil" else GM for c in bench_s["Council"]],
        marker_line_width=0,
        text=[f"+{v:.1f}pp" for v in bench_s["Improvement"]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>+%{x:.1f}pp since 2012<extra></extra>"))
    fig2.update_layout(height=620,
        xaxis=dict(title="Improvement (pp)", **axis_style()),
        yaxis=dict(autorange="reversed", **axis_style()), showlegend=False, **CHART_CFG)
    st.plotly_chart(fig2, use_container_width=True)
    alert("Merthyr's improvement (+15.1pp) matches top councils like Bridgend (+15.7pp). The potential exists — the post-2018 slowdown is the key problem.", GD, "#F0FDF4")

with tab3:
    pivot = df.pivot(index="Council", columns="Year", values="RecyclingRate")
    pivot = pivot.loc[bench["Council"].tolist()]
    fig3 = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#F0FDF4"],[0.45,GL],[0.75,GM],[1,GD]],
        text=np.round(pivot.values,1), texttemplate="%{text}", textfont=dict(size=9),
        zmin=40, zmax=76,
        hovertemplate="<b>%{y}</b><br>%{x}: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="Rate (%)", thickness=12, len=0.8)))
    fig3.update_layout(height=640,
        xaxis=dict(tickangle=-40, **axis_style()),
        yaxis=dict(**axis_style()), **CHART_CFG)
    st.plotly_chart(fig3, use_container_width=True)
