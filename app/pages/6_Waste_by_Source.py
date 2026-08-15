# Waste by Source page — Dataset 2
# Wales-wide aggregate breakdown by stream and collection type.

import streamlit as st
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, RED, AMB, BLUE, SLATE, GREY, BORD,
    CHART_CFG, axis_style, YEAR_FILES,
)

st.set_page_config(page_title="Waste by Source — Waste Analytics", layout="wide")
d = init()
page_header("Waste by Source")

waste_df = d['waste_df']
merthyr_hh_2024 = d['merthyr_hh_2024']
yr_cols = list(YEAR_FILES.keys())

st.markdown(f'<p style="font-size:0.78rem;color:{GREY}">{badge("Dataset 2")} &nbsp; Annual waste generated (tonnes) by source — Wales-wide aggregate, 2012–2024</p>', unsafe_allow_html=True)

if waste_df is None:
    st.error("Waste_Generation_data.csv not found.")
else:
    st.info("This dataset covers Wales-wide aggregate totals. Council-level source breakdown is not available from StatsWales.")

    sec("Wales — Waste by Stream 2012–2024 (thousand tonnes)")
    streams = {"Total Recycled":(1,GD),"Composted":(4,GM),"Residual Household":(8,RED),"Residual Non-Household":(18,AMB)}
    fig = go.Figure()
    for lbl,(idx,clr) in streams.items():
        vals = waste_df.iloc[idx][yr_cols].astype(float)/1000
        fig.add_trace(go.Scatter(
            x=yr_cols, y=vals, mode="lines+markers", name=lbl,
            line=dict(color=clr,width=2.2), marker=dict(size=7,color=clr),
            hovertemplate=f"<b>{lbl}</b><br>%{{x}}: %{{y:.1f}}k tonnes<extra></extra>"))
    fig.update_layout(height=360,
        yaxis=dict(title="Thousand Tonnes",**axis_style()),
        xaxis=dict(tickangle=-40,**axis_style()),
        legend=dict(orientation="h",y=-0.22,font_size=11), **CHART_CFG)
    st.plotly_chart(fig, use_container_width=True)

    sec("Residual Household Waste — Breakdown by Collection Type (2023-24)")
    col_l, col_r = st.columns(2)
    breakdown_idx = {"Regular Kerbside":9,"Civic Amenity":11,"Street Cleaning":12,"Bulky Collections":10,"Other":16}
    lv = {k: float(waste_df.iloc[v]["2023-24"]) for k,v in breakdown_idx.items()}
    with col_l:
        fig_p = go.Figure(go.Bar(
            x=list(lv.values()), y=list(lv.keys()), orientation="h",
            marker_color=[RED,GM,GL,AMB,SLATE], marker_line_width=0,
            text=[f"{int(v/1000)}k t" for v in lv.values()], textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,.0f} tonnes<extra></extra>"))
        fig_p.update_layout(height=320,
            xaxis=dict(title="Tonnes", **axis_style()),
            yaxis=dict(**axis_style()), showlegend=False, **CHART_CFG)
        st.plotly_chart(fig_p, use_container_width=True)
    with col_r:
        rec_v = waste_df.iloc[1][yr_cols].astype(float)/1000
        res_v = waste_df.iloc[8][yr_cols].astype(float)/1000
        fig_b = go.Figure()
        fig_b.add_trace(go.Bar(name="Recycled/Reused", x=yr_cols, y=rec_v, marker_color=GM, marker_line_width=0))
        fig_b.add_trace(go.Bar(name="Residual Household", x=yr_cols, y=res_v, marker_color=RED, marker_line_width=0))
        fig_b.update_layout(barmode="group", height=320,
            yaxis=dict(title="Thousand Tonnes",**axis_style()),
            xaxis=dict(tickangle=-40,**axis_style()),
            legend=dict(orientation="h",y=-0.25,font_size=11), **CHART_CFG)
        st.plotly_chart(fig_b, use_container_width=True)

    alert("<b>Key insight (D2):</b> Regular kerbside collection accounts for ~70% of all residual household waste (374k tonnes in 2023-24). Diverting food waste and dry recyclables out of kerbside bins is the highest-impact lever available to Merthyr.", GD, "#F0FDF4")
    if merthyr_hh_2024:
        alert(f"<b>Link to D3:</b> Merthyr has cut residual waste to {int(merthyr_hh_2024)} kg/person — below Wales average. But the recycling rate is still plateaued because kerbside contamination means recyclable material is being rejected. Separate food waste collection is the missing piece.", BLUE, "#EFF6FF")
