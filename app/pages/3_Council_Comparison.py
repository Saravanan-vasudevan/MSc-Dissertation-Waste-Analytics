# Council Comparison page — Datasets 1 + 3
# Pick councils, compare recycling rates and residual waste side by side.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, MINT, RED, AMB, BLUE, SLATE, GREY, BORD,
    CHART_CFG, axis_style,
)

st.set_page_config(page_title="Council Comparison — Waste Analytics", layout="wide")
d = init()
page_header("Council Comparison")

df = d['df']
bench = d['bench']
hh_data = d['hh_data']
yr_keys = d['yr_keys']
wales_hh_2024 = d['wales_hh_2024']
merthyr_hh_2024 = d['merthyr_hh_2024']
COUNCILS = d['COUNCILS']

sec("Select Councils to Compare")
col_sel, col_info = st.columns([2, 3])
with col_sel:
    selected = st.multiselect("Add councils to compare against Merthyr Tydfil",
        options=sorted([c for c in COUNCILS if c != "Merthyr Tydfil"]),
        default=["Bridgend", "Cardiff", "Swansea"],
        key="compare_councils")
with col_info:
    if selected:
        st.markdown(f"""<div style="background:white;border:1px solid {BORD};border-radius:8px;
             padding:0.8rem 1rem;margin-top:1.6rem;">
          <span style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.06em;color:{GREY};font-weight:700;">Comparing Merthyr Tydfil against: </span>
          <span style="font-size:0.85rem;color:{GD};font-weight:600;">{', '.join(selected)}</span>
        </div>""", unsafe_allow_html=True)

if not selected:
    st.info("Select at least one council from the dropdown above to begin comparison.")
else:
    compare_list = ["Merthyr Tydfil"] + selected
    comp_df = df[df["Council"].isin(compare_list)].copy()
    palette = [GD, GM, AMB, RED, "#6366F1", "#0891B2", "#059669", "#7C3AED"]
    colors_map = {c: palette[i % len(palette)] for i, c in enumerate(compare_list)}
    colors_map["Merthyr Tydfil"] = GD

    tab_r, tab_hh = st.tabs(["RECYCLING RATE (D1)", "RESIDUAL WASTE PER PERSON (D3)"])

    with tab_r:
        sec("Recycling Rate Over Time — Direct Comparison")
        fig = go.Figure()
        for council in compare_list:
            cdf = comp_df[comp_df["Council"]==council].sort_values("YearOrder")
            is_m = council == "Merthyr Tydfil"
            fig.add_trace(go.Scatter(
                x=list(cdf["Year"]), y=list(cdf["RecyclingRate"]),
                mode="lines+markers", name=council,
                line=dict(color=colors_map[council], width=3.0 if is_m else 1.8,
                          dash="solid" if is_m else "dot"),
                marker=dict(size=9 if is_m else 6, color=colors_map[council],
                            line=dict(width=2,color="white") if is_m else dict(width=0)),
                hovertemplate=f"<b>{council}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>"))
        fig.add_hline(y=70, line_dash="dash", line_color=RED, line_width=1.5,
            annotation_text="70% Target", annotation_position="top right",
            annotation_font_color=RED, annotation_font_size=11)
        fig.update_layout(height=400,
            yaxis=dict(title="Recycling Rate (%)", range=[40,80], **axis_style()),
            xaxis=dict(tickangle=-40, **axis_style()),
            legend=dict(orientation="h", y=-0.22, font_size=11), **CHART_CFG)
        st.plotly_chart(fig, use_container_width=True)

        snap = bench[bench["Council"].isin(compare_list)].sort_values("RecyclingRate", ascending=True)
        snap_col1, snap_col2 = st.columns([2, 3])
        with snap_col1:
            fig_s = go.Figure(go.Bar(
                x=snap["RecyclingRate"], y=snap["Council"],
                orientation="h",
                marker_color=[colors_map.get(c, GM) for c in snap["Council"]],
                marker_line_width=0,
                text=[f"{v:.1f}%" for v in snap["RecyclingRate"]], textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>"))
            fig_s.add_vline(x=70, line_dash="dash", line_color=RED, line_width=1.5)
            fig_s.update_layout(height=max(200, len(compare_list)*55),
                xaxis=dict(range=[50,80], title="Rate (%)", **axis_style()),
                yaxis=dict(**axis_style()), showlegend=False, **CHART_CFG)
            st.plotly_chart(fig_s, use_container_width=True)
        with snap_col2:
            sec("Detailed Stats Table")
            stats_rows = []
            for c in compare_list:
                row = bench[bench["Council"]==c]
                if not row.empty:
                    r = row.iloc[0]
                    hh_val = hh_data.get(c, {}).get("2023-24", None)
                    stats_rows.append({
                        "Council": c,
                        "Rate 2023-24 (%)": round(r["RecyclingRate"], 2),
                        "Rate 2012-13 (%)": round(r["Rate2012"], 2),
                        "Improvement (pp)": round(r["Improvement"], 2),
                        "Rank": int(r["Rank"]),
                        "Gap to 70% (pp)": round(max(0, 70 - r["RecyclingRate"]), 2),
                        "Residual kg/person": int(hh_val) if hh_val else "—",
                    })
            stats_df = pd.DataFrame(stats_rows).sort_values("Rate 2023-24 (%)", ascending=False)
            def hl(row):
                return [f"background-color:{MINT};font-weight:600"]*len(row) if row["Council"]=="Merthyr Tydfil" else [""]*len(row)
            st.dataframe(stats_df.style.apply(hl, axis=1)
                .format({"Rate 2023-24 (%)":"{:.2f}","Rate 2012-13 (%)":"{:.2f}",
                         "Improvement (pp)":"{:.2f}","Gap to 70% (pp)":"{:.2f}"}),
                use_container_width=True, hide_index=True,
                height=min(400,(len(stats_rows)+1)*38))

    with tab_hh:
        sec("Residual Waste per Person — Direct Comparison (Dataset 3)")
        if not hh_data:
            st.error("household_waste_data.csv not found.")
        else:
            fig_hh = go.Figure()
            for council in compare_list:
                if council not in hh_data: continue
                series = [hh_data[council].get(y) for y in yr_keys]
                is_m   = council == "Merthyr Tydfil"
                fig_hh.add_trace(go.Scatter(
                    x=yr_keys, y=series,
                    mode="lines+markers", name=council,
                    line=dict(color=colors_map[council], width=3.0 if is_m else 1.8,
                              dash="solid" if is_m else "dot"),
                    marker=dict(size=9 if is_m else 6, color=colors_map[council],
                                line=dict(width=2,color="white") if is_m else dict(width=0)),
                    hovertemplate=f"<b>{council}</b><br>%{{x}}: %{{y:.0f}} kg/person<extra></extra>"))
            if wales_hh_2024:
                fig_hh.add_hline(y=wales_hh_2024, line_dash="dot", line_color=BLUE, line_width=1.2,
                    annotation_text=f"Wales avg 2023-24 ({int(wales_hh_2024)} kg)",
                    annotation_position="top right", annotation_font_color=BLUE, annotation_font_size=10)
            fig_hh.update_layout(height=400,
                yaxis=dict(title="Residual Waste (kg/person)", **axis_style()),
                xaxis=dict(tickangle=-40, **axis_style()),
                legend=dict(orientation="h", y=-0.22, font_size=11), **CHART_CFG)
            st.plotly_chart(fig_hh, use_container_width=True)
            alert(f"<b>Context (D3):</b> Lower residual kg/person = better. Merthyr ({int(merthyr_hh_2024)} kg) is now below the Wales average ({int(wales_hh_2024)} kg). However the recycling <i>rate</i> plateau shows the volume reduction hasn't translated to rate improvement — food waste separation is the missing piece.",
                  BLUE, "#EFF6FF")
