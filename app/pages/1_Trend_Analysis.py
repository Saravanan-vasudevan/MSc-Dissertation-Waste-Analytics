# Trend Analysis page — Dataset 1
# Full time series, year-on-year change bars, and the growth/plateau
# phase comparison panel.

import streamlit as st
import plotly.graph_objects as go

from shared import (
    init, page_header, kpi, sec, alert, badge,
    GD, GM, GL, MINT, RED, AMB, GOLD, SLATE, GREY, BORD,
    FONT_MONO, CHART_CFG, axis_style,
)

st.set_page_config(page_title="Trend Analysis — Waste Analytics", layout="wide")
d = init()
page_header("Trend Analysis")

st.markdown(f'<p style="font-size:0.78rem;color:{GREY}">{badge("Dataset 1")} &nbsp; Annual recycling / reuse / composting rates — 22 Welsh Councils, 2012–2024</p>', unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
kpi(c1, "49.1%",   "Rate 2012-13",      "Starting point",     SLATE)
kpi(c2, "64.3%",   "Rate 2023-24",      "Current level",      GM)
kpi(c3, "+15.1pp", "Total Improvement", "over 12 years",      GD)
kpi(c4, "2020-21", "Peak Year",         "66.95% — best ever", GOLD)

rates = d['rates']
years = d['years']
merthyr = d['merthyr']

sec("Recycling Rate Time Series (2012–2024)")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=years+years[::-1], y=list(rates)+[44.0]*len(rates),
    fill="toself", fillcolor="rgba(45,106,79,0.06)", line=dict(width=0),
    showlegend=False, hoverinfo="skip"))
fig.add_vrect(x0="2018-19", x1="2023-24", fillcolor="#FFF8E7", opacity=0.6, line_width=0)
fig.add_trace(go.Scatter(
    x=years, y=rates, mode="lines+markers", name="Merthyr Tydfil",
    line=dict(color=GM, width=2.8),
    marker=dict(size=8, color=GD, line=dict(width=2, color="white")),
    hovertemplate="<b>%{x}</b><br>Rate: %{y:.2f}%<extra></extra>"))
fig.add_hline(y=70, line_dash="dash", line_color=RED, line_width=1.5,
    annotation_text="70% Target", annotation_position="top right",
    annotation_font_color=RED, annotation_font_size=11)
fig.add_annotation(x="2015-16", y=57.5, text="<b>GROWTH PHASE</b><br>+2.1 pp/yr avg",
    showarrow=False, font=dict(size=11, color=GM), bgcolor="white", bordercolor=GL, borderwidth=1, borderpad=6)
fig.add_annotation(x="2021-22", y=57.5, text="<b>PLATEAU PHASE</b><br>+0.5 pp/yr avg",
    showarrow=False, font=dict(size=11, color=AMB), bgcolor="white", bordercolor=AMB, borderwidth=1, borderpad=6)
fig.update_layout(height=380,
    yaxis=dict(range=[44,72], title="Recycling Rate (%)", **axis_style()),
    xaxis=dict(tickangle=-40, **axis_style()),
    legend=dict(orientation="h", y=-0.18, font_size=11), **CHART_CFG)
st.plotly_chart(fig, use_container_width=True)

# ── YoY change + phase comparison ────────────────────────────────────────────
sec("Year-on-Year Change & Phase Analysis")
col_l, col_r = st.columns([3, 2])
with col_l:
    yoy_vals = list(merthyr["YoY"].dropna())
    yoy_yrs  = list(merthyr["Year"].iloc[1:])
    fig2 = go.Figure(go.Bar(
        x=yoy_yrs, y=yoy_vals,
        marker_color=[GM if v>0 else RED for v in yoy_vals], marker_line_width=0,
        text=[f"{v:+.2f}" for v in yoy_vals], textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Change: %{y:+.2f}pp<extra></extra>"))
    fig2.add_hline(y=0, line_color=BORD, line_width=1.5)
    fig2.add_vrect(x0="2018-19", x1="2023-24", fillcolor="#FFF8E7", opacity=0.5, line_width=0,
        annotation_text="Plateau period", annotation_position="top left",
        annotation_font_size=10, annotation_font_color=AMB)
    fig2.update_layout(height=300,
        yaxis=dict(title="Change (pp)", zeroline=False, **axis_style()),
        xaxis=dict(tickangle=-40, **axis_style()), showlegend=False, **CHART_CFG)
    st.plotly_chart(fig2, use_container_width=True)

with col_r:
    pre  = merthyr[merthyr["YearOrder"]<=6]["YoY"].dropna().mean()
    post = merthyr[merthyr["YearOrder"]>6]["YoY"].dropna().mean()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""<div style="background:white;border:1px solid {BORD};border-radius:10px;padding:1.2rem;">
      <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:{GREY};margin-bottom:1rem;">Phase Comparison</div>
      <div style="display:flex;gap:1.5rem;margin-bottom:1rem;">
        <div style="flex:1;text-align:center;padding:0.8rem;background:{MINT};border-radius:8px;">
          <div style="font-size:1.6rem;font-weight:700;color:{GD};font-family:{FONT_MONO}">+{pre:.2f}</div>
          <div style="font-size:0.72rem;color:{GREY};margin-top:0.25rem">pp / year<br><b>2012–2018</b></div>
        </div>
        <div style="flex:1;text-align:center;padding:0.8rem;background:#FFF8E7;border-radius:8px;">
          <div style="font-size:1.6rem;font-weight:700;color:{AMB};font-family:{FONT_MONO}">+{post:.2f}</div>
          <div style="font-size:0.72rem;color:{GREY};margin-top:0.25rem">pp / year<br><b>2018–2024</b></div>
        </div>
      </div>
      <div style="font-size:0.8rem;color:{SLATE};border-top:1px solid {BORD};padding-top:0.75rem;line-height:1.6;">
        <b>74% slowdown</b> in annual improvement rate since 2018.<br><br>
        Possible causes:<br>
        &bull; Food waste not separated from kerbside<br>
        &bull; Kerbside contamination reducing effective tonnage<br>
        &bull; HWRC accepting limited material types<br>
        &bull; Street cleaning waste rising (+13%)
      </div>
    </div>""", unsafe_allow_html=True)
