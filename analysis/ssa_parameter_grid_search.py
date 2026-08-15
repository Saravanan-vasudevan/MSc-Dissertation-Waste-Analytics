# SSA parameter grid search — which (L, r) pair gives the best one-step-ahead
# RMSE on this 12-point series?
#
# The "fairness constraint" (MIN_PTS = 3) exists because some (L, r) combos
# only have 1-2 valid truncation points, making their RMSE misleadingly low.
# With N=12, this is already a tiny grid, so we can't afford to compare a
# cell with 4 test points against one with 1.
#
# Result: the short-horizon optimum (L=5, r=2) differs from the dissertation's
# long-horizon choice (L=6, r=1). That's expected — Al-Marhoobi & Pepelyshev
# (2023) note this for short series. We report both and explain why L=6/r=1
# was kept for the 17-year forecast.
#
# Outputs: figure_ssa_grid.png, console table.

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from data_loader import load_merthyr_recycling_rates

recycling = np.array(load_merthyr_recycling_rates())
N = len(recycling)


def ssa_r_forecast(series, L, r, h=1):
    T = len(series)
    K = T - L + 1
    if K < 2 or r < 1 or r >= L or r > K:
        return None
    X = np.column_stack([series[i:i+L] for i in range(K)])
    U, sigma, VT = np.linalg.svd(X, full_matrices=False)
    X_r = sum(sigma[i] * np.outer(U[:, i], VT[i, :]) for i in range(r))
    recon  = np.zeros(T)
    counts = np.zeros(T)
    for i in range(L):
        for j in range(K):
            recon[i+j]  += X_r[i, j]
            counts[i+j] += 1
    recon /= counts
    P  = U[:, :r]
    pi = P[-1, :]
    nu_sq = 1.0 - float(np.dot(pi, pi))
    if nu_sq < 1e-10:
        return None
    a = P[:-1, :] @ pi / nu_sq
    hist = list(recon)
    fcs  = []
    for _ in range(h):
        window = np.array(hist[-(L-1):])
        fcs.append(float(np.dot(a, window[::-1])))
        hist.append(fcs[-1])
    return np.array(fcs)


L_range   = [3, 4, 5, 6]
r_range   = [1, 2, 3, 4, 5]
T_points  = [7, 8, 9, 10]
MIN_PTS   = 3

rmse_grid  = np.full((len(L_range), len(r_range)), np.nan)
npts_grid  = np.zeros((len(L_range), len(r_range)), dtype=int)

for li, L in enumerate(L_range):
    for ri, r in enumerate(r_range):
        errors = []
        for T in T_points:
            K_T = T - L + 1
            if r >= L or r > K_T or K_T < 2:
                continue
            fc = ssa_r_forecast(recycling[:T], L, r, h=1)
            if fc is not None:
                errors.append((fc[0] - recycling[T]) ** 2)
        npts_grid[li, ri] = len(errors)
        if len(errors) >= MIN_PTS:
            rmse_grid[li, ri] = float(np.sqrt(np.mean(errors)))


SEP = "=" * 65
print(SEP)
print(f"SSA PARAMETER GRID — RMSE (1-step ahead, min {MIN_PTS} valid points)")
print(SEP)
print("         " + "".join(f"  r={r}  " for r in r_range))
for li, L in enumerate(L_range):
    row = f"  L={L}   "
    for ri in range(len(r_range)):
        v  = rmse_grid[li, ri]
        np_ = npts_grid[li, ri]
        if not np.isnan(v):
            row += f"  {v:.3f}"
        elif np_ > 0:
            row += f" <{np_}pts"
        else:
            row += "   ---"
    print(row)

valid_mask = ~np.isnan(rmse_grid)
min_idx  = np.unravel_index(np.nanargmin(rmse_grid), rmse_grid.shape)
best_L   = L_range[min_idx[0]]
best_r   = r_range[min_idx[1]]
min_rmse = rmse_grid[min_idx]

diss_li  = L_range.index(6)
diss_ri  = r_range.index(1)
rmse_61  = rmse_grid[diss_li, diss_ri]

print(f"\n  Global optimum (fair): L={best_L}, r={best_r} -> RMSE = {min_rmse:.4f} pp")
print(f"  L=6, r=1 (dissertation): RMSE = {rmse_61:.4f} pp")
if not np.isnan(rmse_61):
    eff = min_rmse / rmse_61 * 100
    print(f"  Efficiency of L=6, r=1: {eff:.1f}% of optimum")
print(SEP)


# ── Figure — heatmap ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5.5))
fig.suptitle(
    'SSA Parameter Selection — RMSE of 1-Step Ahead Retrospective Forecasts\n'
    f'Merthyr Tydfil Recycling Rate  (N=12,  truncation points T = 7–10,  min {MIN_PTS} valid points)',
    fontsize=11.5, fontweight='bold'
)

masked = np.ma.array(rmse_grid, mask=np.isnan(rmse_grid))
cmap   = plt.cm.RdYlGn_r.copy()
cmap.set_bad('#e8e8e8')
im = ax.imshow(masked, cmap=cmap, aspect='auto',
               vmin=np.nanmin(rmse_grid), vmax=np.nanmax(rmse_grid))
plt.colorbar(im, ax=ax, label='RMSE (percentage points)', shrink=0.85)

ax.set_xticks(range(len(r_range)))
ax.set_xticklabels([f'r = {r}' for r in r_range], fontsize=11)
ax.set_yticks(range(len(L_range)))
ax.set_yticklabels([f'L = {L}' for L in L_range], fontsize=11)
ax.set_xlabel('Number of eigentriples  r', fontsize=11)
ax.set_ylabel('Window length  L', fontsize=11)

for i in range(len(L_range)):
    for j in range(len(r_range)):
        v   = rmse_grid[i, j]
        np_ = npts_grid[i, j]
        is_best = (i == min_idx[0] and j == min_idx[1])
        is_diss = (i == diss_li   and j == diss_ri)

        if not np.isnan(v):
            tc = 'white' if is_best else 'black'
            fw = 'bold'  if (is_best or is_diss) else 'normal'
            ax.text(j, i, f'{v:.3f}\n(n={np_})', ha='center', va='center',
                    fontsize=9, color=tc, fontweight=fw)
            if is_best:
                ax.add_patch(plt.Rectangle(
                    (j-0.5, i-0.5), 1, 1,
                    fill=False, edgecolor='#1a5f8a', lw=3.5, zorder=5))
            if is_diss and not is_best:
                ax.add_patch(plt.Rectangle(
                    (j-0.5, i-0.5), 1, 1,
                    fill=False, edgecolor='#e67e22', lw=2.5,
                    linestyle='--', zorder=5))
            if is_diss and is_best:
                ax.add_patch(plt.Rectangle(
                    (j-0.47, i-0.47), 0.94, 0.94,
                    fill=False, edgecolor='#e67e22', lw=2,
                    linestyle='--', zorder=6))
        elif np_ > 0:
            ax.text(j, i, f'<{MIN_PTS} pts\n(n={np_})', ha='center', va='center',
                    fontsize=8, color='#888888')
        else:
            ax.text(j, i, 'N/A', ha='center', va='center',
                    fontsize=9, color='#aaaaaa')

leg_handles = [
    plt.Rectangle((0,0),1,1, fill=False, edgecolor='#1a5f8a', lw=3.5,
                  label=f'Optimum (fair): L={best_L}, r={best_r}  RMSE={min_rmse:.3f} pp'),
    plt.Rectangle((0,0),1,1, fill=False, edgecolor='#e67e22', lw=2.5,
                  linestyle='--',
                  label=f'Dissertation choice: L=6, r=1  RMSE={rmse_61:.3f} pp')
]
ax.legend(handles=leg_handles, loc='upper right', fontsize=8.5, framealpha=0.95)

plt.tight_layout()
plt.savefig('figure_ssa_grid.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved --> figure_ssa_grid.png")
