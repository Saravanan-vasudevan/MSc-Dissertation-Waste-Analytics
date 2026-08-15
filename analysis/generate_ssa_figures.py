# SSA diagnostic figures for the dissertation: eigenvalue scree, trend
# reconstruction with residual panel, w-correlation heatmap, and the
# forecast-to-2040 plot.
#
# This script duplicates the YEAR_FILES dict and its own CSV reader instead
# of importing from src/data_loader because it also needs the years list
# and the load_merthyr_rates function here does the same thing slightly
# differently (it exits on error instead of raising). Not ideal, but the
# alternative was making data_loader return a dict of year->rate pairs
# which would break the analysis scripts that expect a plain array.
# TODO: clean this up if there's ever a v2.

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from scipy.linalg import svd

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")

YEAR_FILES = {
    "2012-13": "recycling_2012-13.csv",
    "2013-14": "recycling_2013-14.csv",
    "2014-15": "recycling_2014-15.csv",
    "2015-16": "recycling_2015-16.csv",
    "2016-17": "recycling_2016-17.csv",
    "2017-18": "recycling_2017-18.csv",
    "2018-19": "recycling_2018-19.csv",
    "2019-20": "recycling_2019-20.csv",
    "2020-21": "recycling_2020-21.csv",
    "2021-22": "recycling_2021-22.csv",
    "2022-23": "recycling_2022-23.csv",
    "2023-24": "recycling_2023-24.csv",
}

TARGET_COUNCIL = "Merthyr Tydfil"

def load_merthyr_rates():
    """Grab the recycling rate from each annual CSV.
    Same matching logic as data_loader — look for the council name in quotes,
    take the last numeric field. Dies hard if a file is missing because
    there's no point generating half a figure."""
    rates, years = [], []
    for year, fname in YEAR_FILES.items():
        path = os.path.join(BASE, fname)
        if not os.path.exists(path):
            print(f"  [ERROR] Missing file: {fname}")
            print("          Expected it under data/raw/ - check the repo layout.")
            sys.exit(1)
        found = False
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if f'"{TARGET_COUNCIL} "' in line or f'"{TARGET_COUNCIL}"' in line:
                    parts = line.strip().split(",")
                    try:
                        rate = float(parts[-1].strip().strip('"'))
                        rates.append(rate)
                        years.append(year)
                        found = True
                        break
                    except ValueError:
                        pass
        if not found:
            print(f"  [ERROR] Could not find '{TARGET_COUNCIL}' in {fname}")
            sys.exit(1)
    return years, np.array(rates)

print("Loading CSV data...")
years_hist, Y = load_merthyr_rates()
print(f"  Loaded {len(Y)} observations for {TARGET_COUNCIL}")
for yr, val in zip(years_hist, Y):
    print(f"    {yr}: {val:.4f}%")

N = len(Y)           # 12
L = N // 2           # window = 6 (standard RSSA recommendation for short series)
K = N - L + 1        # 7 lagged vectors

print(f"\nSSA parameters: N={N}, L={L}, K={K}")


def build_trajectory(series, window):
    n = len(series)
    k = n - window + 1
    X = np.zeros((window, k))
    for i in range(k):
        X[:, i] = series[i: i + window]
    return X

def diagonal_average(matrix):
    """Anti-diagonal averaging — the bit that turns a matrix back into a
    time series. Called "Hankelisation" in the SSA literature."""
    L_, K_ = matrix.shape
    N_out = L_ + K_ - 1
    series = np.zeros(N_out)
    counts = np.zeros(N_out)
    for i in range(L_):
        for j in range(K_):
            series[i + j] += matrix[i, j]
            counts[i + j] += 1
    return series / counts

def reconstruct_component(U, sigma, Vt, indices):
    mat = sum(sigma[i] * np.outer(U[:, i], Vt[i, :]) for i in indices)
    return diagonal_average(mat)

def w_weights(N_, L_):
    """Golyandina et al. 2001, Section 1.5"""
    K_ = N_ - L_ + 1
    w = np.zeros(N_)
    for i in range(N_):
        w[i] = min(i + 1, L_, K_, N_ - i)
    return w

def w_correlation_matrix(components, w):
    n = len(components)
    W = np.zeros((n, n))
    norms = [np.sqrt(np.dot(w * c, c)) for c in components]
    for i in range(n):
        for j in range(n):
            W[i, j] = abs(np.dot(w * components[i], components[j])
                          / (norms[i] * norms[j]))
    return W

def ssa_forecast(series, window, n_components, n_ahead):
    """LRR forecast — Golyandina et al. (2018), Chapter 2."""
    traj = build_trajectory(series, window)
    U_, sigma_, Vt_ = svd(traj, full_matrices=False)
    U_r = U_[:, :n_components]
    pi  = U_r[-1, :]
    nu2 = float(np.dot(pi, pi))
    R   = (U_r[:-1, :] @ pi) / (1.0 - nu2)
    extended = list(series.copy())
    for _ in range(n_ahead):
        extended.append(float(R @ extended[-(window - 1):]))
    return np.array(extended[len(series):])


# Run the decomposition
traj_matrix = build_trajectory(Y, L)
U, sigma, Vt = svd(traj_matrix, full_matrices=False)

lambdas = sigma ** 2
pct_var = 100.0 * lambdas / lambdas.sum()

trend_rc = reconstruct_component(U, sigma, Vt, [0])
residual  = Y - trend_rc

n_comp = min(L, K)  # 6
components = [reconstruct_component(U, sigma, Vt, [i]) for i in range(n_comp)]

w = w_weights(N, L)
W_corr = w_correlation_matrix(components, w)

# Forecast 17 years ahead (to 2040-41)
n_forecast = 17
Y_fc = ssa_forecast(Y, L, n_components=1, n_ahead=n_forecast)

years_fc = [f"{2024+i}-{str(2025+i)[-2:]}" for i in range(n_forecast)]
x_hist   = np.arange(N)
x_fc     = np.arange(N, N + n_forecast)

print("\n=== SSA Diagnostics ===")
print(f"Eigenvalues (top 6): {np.round(lambdas, 2)}")
print(f"% Variance explained: {np.round(pct_var, 4)}")
print(f"\nC1 captures {pct_var[0]:.4f}% of variance")
print(f"\nW-correlation matrix (6x6):\n{np.round(W_corr, 4)}")
print(f"\nW-corr(C1, C2) = {W_corr[0,1]:.4f}")
print(f"W-corr(C1, C3) = {W_corr[0,2]:.4f}")
print(f"W-corr(C1, C4) = {W_corr[0,3]:.4f}")
print(f"\nKey forecast values:")
for label, idx in [("2025-26", 1), ("2027-28", 3), ("2030-31", 6)]:
    print(f"  {label}: {Y_fc[idx]:.2f}%")

# Colours — went with Cardiff's brand navy for the SSA-specific plots
# because the dissertation is submitted to Cardiff and it looked right.
CARDIFF_BLUE  = "#003B6F"
CARDIFF_RED   = "#CF142B"
DARK_GREY     = "#444444"
MID_GREY      = "#888888"
LIGHT_GREY    = "#E8E8E8"
AMBER         = "#E8A020"
TARGET_LINE   = "#B22222"

plt.rcParams.update({
    "font.family":        "serif",
    "font.size":          10,
    "axes.titlesize":     11,
    "axes.labelsize":     10,
    "xtick.labelsize":    9,
    "ytick.labelsize":    9,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.dpi":         150,
    "savefig.dpi":        300,
    "savefig.bbox":       "tight",
})

# ── Figure A — eigenvalue scree ──────────────────────────────────────────────
print("\nGenerating Figure A: Eigenvalue scree plot...")
fig_a, ax = plt.subplots(figsize=(6, 4))

comp_labels = [f"C{i+1}" for i in range(n_comp)]
bar_colors  = [CARDIFF_BLUE if i == 0 else MID_GREY for i in range(n_comp)]

bars = ax.bar(comp_labels, pct_var, color=bar_colors, edgecolor="white",
              linewidth=0.8, width=0.6, zorder=3)

for bar, pv in zip(bars, pct_var):
    offset = 0.3 if pv < 1 else -0.4
    va     = "bottom" if pv < 1 else "top"
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + offset,
            f"{pv:.2f}%", ha="center", va=va, fontsize=8, color=DARK_GREY)

ax2 = ax.twinx()
ax2.plot(comp_labels, np.cumsum(pct_var), color=CARDIFF_RED,
         marker="o", markersize=5, linewidth=1.5, linestyle="--", zorder=4)
ax2.set_ylabel("Cumulative variance explained (%)", color=CARDIFF_RED, fontsize=9)
ax2.tick_params(axis="y", labelcolor=CARDIFF_RED, labelsize=8)
ax2.set_ylim(0, 105)
ax2.spines["right"].set_visible(True)
ax2.spines["top"].set_visible(False)

ax.set_xlabel("Elementary component", labelpad=6)
ax.set_ylabel("Variance explained (%)", labelpad=6)
ax.set_title(
    "Eigenvalue spectrum — SSA decomposition\n"
    f"Merthyr Tydfil recycling rate  (N = {N},  L = {L})",
    pad=10
)
ax.set_ylim(0, max(pct_var) * 1.20)
ax.yaxis.grid(True, linestyle=":", color=LIGHT_GREY, zorder=0)
ax.set_axisbelow(True)

ax.annotate(
    f"C1: {pct_var[0]:.2f}%\n(trend component)",
    xy=(0, pct_var[0]),
    xytext=(1.2, pct_var[0] * 0.82),
    arrowprops=dict(arrowstyle="->", color=CARDIFF_BLUE, lw=1.0),
    fontsize=8.5, color=CARDIFF_BLUE, ha="left",
)

fig_a.tight_layout()
out_a = os.path.join(BASE, "ssa_fig_A_eigenvalue_scree.png")
fig_a.savefig(out_a)
plt.close(fig_a)
print(f"  Saved: {out_a}")

# ── Figure B — trend reconstruction + residual ───────────────────────────────
print("Generating Figure B: Trend reconstruction...")
fig_b, (ax_main, ax_res) = plt.subplots(
    2, 1, figsize=(8, 6),
    sharex=True,
    gridspec_kw={"height_ratios": [3, 1], "hspace": 0.06},
)

ax_main.plot(x_hist, Y, color=MID_GREY, linewidth=1.4, marker="o",
             markersize=5, label="Original series", zorder=2)
ax_main.plot(x_hist, trend_rc, color=CARDIFF_BLUE, linewidth=2.2,
             label="Reconstructed trend (C1)", zorder=3)
ax_main.axhline(70, color=TARGET_LINE, linewidth=1.2, linestyle="--",
                label="70% target", zorder=1)
ax_main.fill_between(x_hist, Y, trend_rc, alpha=0.13, color=CARDIFF_BLUE,
                     label="Noise (C2–C6)")

ax_main.axvspan(-0.5, 5.5, alpha=0.05, color="green")
ax_main.axvspan( 5.5, N - 0.5, alpha=0.05, color=CARDIFF_RED)

y_lo = Y.min() - 2
ax_main.text(2.5, y_lo + 0.5, "Growth phase", ha="center",
             fontsize=8, color="darkgreen", style="italic")
ax_main.text(9.0, y_lo + 0.5, "Plateau phase", ha="center",
             fontsize=8, color=CARDIFF_RED, style="italic")

ax_main.set_ylabel("Recycling rate (%)")
ax_main.set_title(
    "SSA reconstruction — trend component (C1)\n"
    f"Merthyr Tydfil recycling rate 2012–13 to 2023–24  (L = {L})",
    pad=10,
)
ax_main.legend(fontsize=8.5, loc="upper left", framealpha=0.9)
y_pad = 2
ax_main.set_ylim(Y.min() - y_pad, 74)
ax_main.yaxis.grid(True, linestyle=":", color=LIGHT_GREY, zorder=0)

ax_res.bar(x_hist, residual,
           color=[CARDIFF_BLUE if r > 0 else CARDIFF_RED for r in residual],
           alpha=0.75, width=0.6)
ax_res.axhline(0, color=DARK_GREY, linewidth=0.8)
ax_res.set_ylabel("Residual\n(pp)", fontsize=8.5)
ax_res.set_ylim(-max(abs(residual)) * 1.6, max(abs(residual)) * 1.6)
ax_res.yaxis.grid(True, linestyle=":", color=LIGHT_GREY, zorder=0)

ax_res.set_xticks(x_hist)
ax_res.set_xticklabels(years_hist, rotation=45, ha="right", fontsize=8)
ax_res.set_xlabel("Financial year")

out_b = os.path.join(BASE, "ssa_fig_B_trend_reconstruction.png")
fig_b.savefig(out_b)
plt.close(fig_b)
print(f"  Saved: {out_b}")

# ── Figure C — w-correlation heatmap ─────────────────────────────────────────
print("Generating Figure C: W-correlation heatmap...")
cmap_w = LinearSegmentedColormap.from_list(
    "wcorr", ["#FFFFFF", "#C8DFF0", "#5599CC", CARDIFF_BLUE], N=256
)

fig_c, ax = plt.subplots(figsize=(5.5, 5.0))
im = ax.imshow(W_corr, cmap=cmap_w, vmin=0, vmax=1, aspect="auto")

for i in range(n_comp):
    for j in range(n_comp):
        val   = W_corr[i, j]
        color = "white" if val > 0.55 else DARK_GREY
        weight = "bold" if i == j else "normal"
        ax.text(j, i, f"{val:.3f}", ha="center", va="center",
                fontsize=8.5, color=color, fontweight=weight)

comp_ticks = [f"C{i+1}" for i in range(n_comp)]
ax.set_xticks(range(n_comp));  ax.set_xticklabels(comp_ticks)
ax.set_yticks(range(n_comp));  ax.set_yticklabels(comp_ticks)
ax.set_xlabel("Component")
ax.set_ylabel("Component")
ax.set_title(
    "W-correlation matrix\n"
    f"SSA decomposition — Merthyr Tydfil recycling rate  (L = {L})",
    pad=10,
)

cb = fig_c.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("|W-correlation|", fontsize=9)
cb.ax.tick_params(labelsize=8)

rect = Rectangle((-0.5, -0.5), 1, 1, linewidth=2,
                 edgecolor=AMBER, facecolor="none", linestyle="--")
ax.add_patch(rect)
ax.annotate(
    f"C1 (trend)\nW-corr with C2–C{n_comp}\nall < 0.05",
    xy=(0.5, 0.5), xytext=(1.8, 0.5),
    arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.1),
    fontsize=8, color=AMBER, ha="left",
    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=AMBER, lw=0.7),
)

fig_c.tight_layout()
out_c = os.path.join(BASE, "ssa_fig_C_wcorr_heatmap.png")
fig_c.savefig(out_c)
plt.close(fig_c)
print(f"  Saved: {out_c}")

# ── Figure D — forecast to 2040-41 ──────────────────────────────────────────
print("Generating Figure D: SSA forecast...")
years_all = years_hist + years_fc
x_all     = np.arange(N + n_forecast)

fig_d, ax = plt.subplots(figsize=(10, 5))

ax.plot(x_hist, Y, color=DARK_GREY, linewidth=1.4, marker="o",
        markersize=5.5, label=f"Observed series (2012–23)", zorder=3)
ax.plot(x_hist, trend_rc, color=CARDIFF_BLUE, linewidth=2.0,
        label="SSA trend (C1, in-sample)", zorder=4)
ax.plot(x_fc, Y_fc, color=CARDIFF_BLUE, linewidth=1.8, linestyle="--",
        marker="s", markersize=4,
        label="SSA forecast (2024–41, LRR from C1)", zorder=4)

ax.axhline(70, color=TARGET_LINE, linewidth=1.2, linestyle="--",
           label="70% recycling target", zorder=1)

ax.axvline(N - 0.5, color=MID_GREY, linewidth=1.0, linestyle=":")
ax.text(N - 0.2, Y.min() - 0.5, "Forecast →",
        fontsize=8, color=MID_GREY, style="italic")
ax.text(N - 0.8, Y.min() - 0.5, "← Observed",
        fontsize=8, color=MID_GREY, style="italic", ha="right")

cross = np.where(Y_fc >= 70.0)[0]
if len(cross) > 0:
    ci = cross[0]
    ax.annotate(
        f"Reaches 70%:\n{years_fc[ci]}",
        xy=(x_fc[ci], Y_fc[ci]),
        xytext=(x_fc[ci] - 4, Y_fc[ci] - 5),
        arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.2),
        fontsize=8.5, color=AMBER, ha="left",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=AMBER, lw=0.8),
    )

for label, idx in [("2025-26", 1), ("2027-28", 3), ("2030-31", 6)]:
    ax.annotate(
        f"{Y_fc[idx]:.1f}%",
        xy=(x_fc[idx], Y_fc[idx]),
        xytext=(x_fc[idx] + 0.1, Y_fc[idx] + 1.2),
        fontsize=7.5, color=CARDIFF_BLUE,
    )

ax.set_xticks(x_all[::2])
ax.set_xticklabels(years_all[::2], rotation=45, ha="right", fontsize=8)
ax.set_ylabel("Recycling rate (%)")
ax.set_xlabel("Financial year")
ax.set_title(
    "SSA forecast to 2040–41 — Merthyr Tydfil recycling rate\n"
    f"L = {L},  1 eigentriple (trend),  Linear Recurrence Relation",
    pad=10,
)
ax.legend(fontsize=8.5, loc="upper left", framealpha=0.9, ncol=2)
ax.set_ylim(Y.min() - 3, 82)
ax.yaxis.grid(True, linestyle=":", color=LIGHT_GREY, zorder=0)

fig_d.tight_layout()
out_d = os.path.join(BASE, "ssa_fig_D_forecast.png")
fig_d.savefig(out_d)
plt.close(fig_d)
print(f"  Saved: {out_d}")

print("\nAll four figures generated successfully.")
print(f"   Output folder: {BASE}")
