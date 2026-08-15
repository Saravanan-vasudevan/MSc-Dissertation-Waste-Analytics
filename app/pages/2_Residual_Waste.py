# Residual Waste page — Dataset 3
# Merthyr vs Wales trend, all-council bar chart, heatmap over time.

import streamlit as st
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, RED, AMB, BLUE, SLATE, GREY, BORD,
    CHART_CFG, axis_style,
)

st.set_page_config(page_title="Residual Waste — Waste Analytics", layout="wide")
d = init()
page_header("Residual Waste")

st.markdown(f'<p style="font-size:0.78rem;color:{GREY}">{badge("Dataset 3")} &nbsp; Annual residual household waste per person (kg) — 22 Welsh Councils, 2012–2024</p>', unsafe_allow_html=True)

hh_data = d['hh_data']
wales_hh = d['wales_hh']
yr_keys = d['yr_keys']
merthyr_hh_2024 = d['merthyr_hh_2024']
merthyr_hh_2012 = d['merthyr_hh_2012']
wales_hh_2024 = d['wales_hh_2024']
COUNCILS = d['COUNCILS']

if not hh_data:
    st.error("household_waste_data.csv not found. Place it in data/raw/.")
else:
    c1,c2,c3,c4 = st.columns(4)
    kpi(c1, f"{int(merthyr_hh_2012)} kg" if merthyr_hh_2012 else "—",
            "Residual per Person 2012-13", "Merthyr starting point", SLATE)
    kpi(c2, f"{int(merthyr_hh_2024)} kg" if merthyr_hh_2024 else "—",
            "Residual per Person 2023-24", "Merthyr current",        GM)
    kpi(c3, f"-{int(merthyr_hh_2012 - merthyr_hh_2024)} kg" if (merthyr_hh_2012 and merthyr_hh_2024) else "—",
            "Reduction per Person",         "over 12 years",          GD)
    kpi(c4, f"{int(wales_hh_2024)} kg" if wales_hh_2024 else "—",
            "Wales Average 2023-24",        "Merthyr is below this",  BLUE)

    tab1, tab2, tab3 = st.tabs(["MERTHYR TREND vs WALES", "ALL 22 COUNCILS (2023-24)", "HEATMAP — ALL COUNCILS"])

    with tab1:
        sec("Residual Waste per Person — Merthyr vs Wales Average (2012–2024)")
        merthyr_hh_series = [hh_data["Merthyr Tydfil"].get(y) for y in yr_keys]
        wales_hh_series   = [wales_hh.get(y) for y in yr_keys]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=yr_keys, y=merthyr_hh_series, mode="lines+markers",
            name="Merthyr Tydfil",
            line=dict(color=GM, width=3),
            marker=dict(size=8, color=GD, line=dict(width=2, color="white")),
            hovertemplate="<b>Merthyr</b><br>%{x}: %{y:.0f} kg/person<extra></extra>"))
        fig.add_trace(go.Scatter(x=yr_keys, y=wales_hh_series, mode="lines+markers",
            name="Wales Average",
            line=dict(color=AMB, width=2.2, dash="dot"),
            marker=dict(size=6, color=AMB),
            hovertemplate="<b>Wales avg</b><br>%{x}: %{y:.0f} kg/person<extra></extra>"))

        for i, (m, w) in enumerate(zip(merthyr_hh_series, wales_hh_series)):
            if m and w and m < w:
                fig.add_vline(x=yr_keys[i], line_dash="dot", line_color=BLUE, line_width=1.2)
                fig.add_annotation(x=yr_keys[i], y=max(merthyr_hh_series[i], wales_hh_series[i])+10,
                    text="Merthyr drops<br>below Wales avg",
                    showarrow=False, font=dict(size=10, color=BLUE),
                    bgcolor="white", bordercolor=BLUE, borderwidth=1, borderpad=5)
                break

        fig.update_layout(height=380,
            yaxis=dict(title="Residual Waste (kg/person)", **axis_style()),
            xaxis=dict(tickangle=-40, **axis_style()),
            legend=dict(orientation="h", y=-0.18, font_size=11), **CHART_CFG)
        st.plotly_chart(fig, use_container_width=True)
        alert(f"<b>Key finding (D3):</b> Merthyr reduced residual waste from {int(merthyr_hh_2012)} kg/person (2012-13) to {int(merthyr_hh_2024)} kg/person (2023-24) — a reduction of {int(merthyr_hh_2012-merthyr_hh_2024)} kg. Merthyr is now <b>below the Wales average of {int(wales_hh_2024)} kg/person</b>. This is a genuine success on volume reduction.",
              BLUE, "#EFF6FF")

    with tab2:
        sec("All 22 Welsh Councils — Residual Waste per Person (2023-24)")
        council_vals = [(c, hh_data[c]["2023-24"]) for c in COUNCILS if c in hh_data]
        council_vals.sort(key=lambda x: x[1])
        c_names = [x[0] for x in council_vals]
        c_vals  = [x[1] for x in council_vals]
        bar_clrs = [RED if c=="Merthyr Tydfil" else (GD if v<=150 else GL) for c,v in council_vals]

        fig2 = go.Figure(go.Bar(
            x=c_vals, y=c_names, orientation="h",
            marker_color=bar_clrs, marker_line_width=0,
            text=[f"{int(v)} kg" for v in c_vals], textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:.0f} kg/person<extra></extra>"))
        if wales_hh_2024:
            fig2.add_vline(x=wales_hh_2024, line_dash="dash", line_color=BLUE, line_width=1.5,
                annotation_text=f"Wales avg {int(wales_hh_2024)} kg",
                annotation_position="top", annotation_font_color=BLUE, annotation_font_size=10)
        fig2.update_layout(height=620,
            xaxis=dict(range=[80,280], title="Residual Waste (kg/person)", **axis_style()),
            yaxis=dict(**axis_style()), showlegend=False, **CHART_CFG)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(f'<div style="font-size:0.78rem;color:{GREY};text-align:center;margin-top:-0.5rem;">Dark green = 150 kg or less (best performers) &nbsp;|&nbsp; Red = Merthyr Tydfil &nbsp;|&nbsp; Blue dashed = Wales average</div>', unsafe_allow_html=True)

    with tab3:
        sec("Residual Waste per Person — All Councils Over Time (Heatmap)")
        hh_pivot_data = {}
        for c in COUNCILS:
            if c in hh_data:
                hh_pivot_data[c] = [hh_data[c].get(y, None) for y in yr_keys]

        sorted_councils = sorted(hh_pivot_data.keys(), key=lambda c: hh_data[c].get("2023-24", 999))
        z_vals = [hh_pivot_data[c] for c in sorted_councils]

        fig3 = go.Figure(go.Heatmap(
            z=z_vals, x=yr_keys, y=sorted_councils,
            colorscale=[[0,"#1B4332"],[0.4,"#74C69D"],[0.7,"#FFF8E7"],[1,"#C0392B"]],
            reversescale=False,
            text=[[f"{int(v)}" if v else "" for v in row] for row in z_vals],
            texttemplate="%{text}", textfont=dict(size=8),
            zmin=90, zmax=280,
            hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f} kg/person<extra></extra>",
            colorbar=dict(title="kg/person", thickness=12, len=0.8)))
        fig3.update_layout(height=640,
            xaxis=dict(tickangle=-40, **axis_style()),
            yaxis=dict(**axis_style()), **CHART_CFG)
        st.plotly_chart(fig3, use_container_width=True)
