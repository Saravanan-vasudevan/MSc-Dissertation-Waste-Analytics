# Mann-Kendall, Spearman's rho, and ITM trend tests on the recycling
# and residual waste series.
#
# Produces two figures:
#   figure_trend_tests.png     — time series with test stats overlaid + YoY bars
#   figure_itm_diagnostic.png  — ITM scatter plots (sorted halves)
#
# The residual waste per person series is hardcoded here because it comes
# from a differently-shaped CSV (household_waste_data.csv) that data_loader
# doesn't handle yet. The values were verified against the raw file in
# scripts/explore_raw_data.py. If someone adds a new year, update both
# the recycling CSVs AND this array.

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from data_loader import load_merthyr_recycling_rates, YEAR_FILES

years_labels = list(YEAR_FILES.keys())
recycling = np.array(load_merthyr_recycling_rates())

# Hardcoded because household_waste_data.csv has a different layout
# and we'd need a separate loader. See scripts/explore_raw_data.py.
residual_pp = np.array([
    181, 150, 155, 171, 174, 177,
    180, 155, 134, 133, 120, 110
])

N = len(recycling)


def mann_kendall(x):
    n = len(x)
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            s += int(np.sign(x[j] - x[i]))
    var_s = n * (n - 1) * (2 * n + 5) / 18
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = float(2 * (1 - stats.norm.cdf(abs(z))))
    return {'S': s, 'Z': round(z, 3), 'p': round(p, 4),
            'sig': p < 0.05, 'dir': 'increasing' if z > 0 else 'decreasing'}


def spearman_rho(x):
    t = np.arange(1, len(x) + 1)
    rho, p = stats.spearmanr(t, x)
    return {'rho': round(float(rho), 4), 'p': round(float(p), 4),
            'sig': float(p) < 0.05, 'dir': 'increasing' if rho > 0 else 'decreasing'}


def itm_test(x):
    """Innovative Trend Methodology — Sen (2012).
    Split series in half, sort each half independently, scatter first vs second.
    Points above the 1:1 line = increasing trend. We bootstrap the p-value
    with 5000 permutations (seeded for reproducibility)."""
    n  = len(x)
    h  = n // 2
    x1 = np.sort(x[:h])
    x2 = np.sort(x[h:])
    s  = float((2 / n) * (np.mean(x2) - np.mean(x1)))
    rng = np.random.default_rng(42)
    boot = np.array([
        (2 / n) * (np.mean(np.sort(p[h:])) - np.mean(np.sort(p[:h])))
        for p in (rng.permutation(x) for _ in range(5000))
    ])
    pval = float(np.mean(np.abs(boot) >= abs(s)))
    return {'S_ITM': round(s, 4), 'p': round(pval, 4),
            'sig': pval < 0.05, 'dir': 'increasing' if s > 0 else 'decreasing',
            'x1': x1, 'x2': x2}


# Run everything
plateau  = recycling[6:]

mk_full  = mann_kendall(recycling);   sr_full  = spearman_rho(recycling);   itm_full  = itm_test(recycling)
mk_plat  = mann_kendall(plateau);     sr_plat  = spearman_rho(plateau);     itm_plat  = itm_test(plateau)
mk_res   = mann_kendall(residual_pp); sr_res   = spearman_rho(residual_pp); itm_res   = itm_test(residual_pp)

yoy          = np.diff(recycling)
growth_mean  = round(float(np.mean(yoy[:5])), 3)
plateau_mean = round(float(np.mean(yoy[5:])), 3)

# Print results — formatted for easy copy-paste into the dissertation
SEP = "=" * 70

def pblock(label, mk, sr, itm):
    s = lambda r: "SIGNIFICANT" if r['sig'] else "not significant"
    print(f"\n  {label}")
    print(f"    Mann-Kendall  S={mk['S']:5d}  Z={mk['Z']:7.3f}  p={mk['p']:.4f}  [{s(mk)}]")
    print(f"    Spearman rho  rho={sr['rho']:8.4f}       p={sr['p']:.4f}  [{s(sr)}]")
    print(f"    ITM           S_ITM={itm['S_ITM']:8.4f}  p={itm['p']:.4f}  [{s(itm)}]")

print(SEP)
print("TREND TEST RESULTS  -- copy numbers into dissertation")
print(SEP)
pblock("Recycling Rate -- FULL series  (N=12, 2012-24)", mk_full, sr_full, itm_full)
pblock("Recycling Rate -- PLATEAU only (N=6,  2018-24)", mk_plat, sr_plat, itm_plat)
pblock("Residual Waste per Person -- FULL series (N=12)", mk_res, sr_res, itm_res)
print(f"\n  Growth phase YoY mean  (2013-14 to 2017-18): {growth_mean:+.3f} pp/yr")
print(f"  Plateau phase YoY mean (2018-19 to 2023-24): {plateau_mean:+.3f} pp/yr")
print(SEP)


# ── Figure 1 — time series + test annotation + YoY bars ─────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.5),
                                gridspec_kw={'height_ratios': [2.2, 1]})
fig.suptitle(
    'Trend Analysis - Merthyr Tydfil Recycling Rate 2012-13 to 2023-24\n'
    'with Mann-Kendall, Spearman Rho and ITM Trend Tests',
    fontsize=13, fontweight='bold', y=0.99
)

x = np.arange(N)

ax1.plot(x, recycling, 'o-', color='#1a5f8a', lw=2.2, ms=7, zorder=5,
         label='Recycling rate (observed)')
ax1.axhline(70, color='#c0392b', ls='--', lw=1.7,
            label='70% Welsh Government target', zorder=3)
ax1.axvspan(-0.5, 5.5,  alpha=0.07, color='#2ecc71', label='Growth phase (2012-18)')
ax1.axvspan(5.5, 11.5,  alpha=0.07, color='#e67e22', label='Plateau phase (2018-24)')

for i, v in enumerate(recycling):
    ax1.annotate(f'{v:.1f}', (x[i], v),
                 textcoords='offset points', xytext=(0, 8),
                 ha='center', fontsize=7.5, color='#1a5f8a')

ax1.set_xticks(x)
ax1.set_xticklabels(years_labels, rotation=45, ha='right', fontsize=9)
ax1.set_ylabel('Recycling / reuse / composting rate (%)', fontsize=10)
ax1.set_ylim(42, 76)
ax1.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax1.grid(True, alpha=0.2, ls=':')

st = lambda r: "sig." if r['sig'] else "n.s."
box = (
    f"Full series (N=12)\n"
    f"  Mann-Kendall  S={mk_full['S']}  Z={mk_full['Z']:.2f}  p={mk_full['p']:.4f}  [{st(mk_full)}]\n"
    f"  Spearman rho  rho={sr_full['rho']:.4f}  p={sr_full['p']:.4f}  [{st(sr_full)}]\n"
    f"  ITM           S_ITM={itm_full['S_ITM']:.4f}  p={itm_full['p']:.4f}  [{st(itm_full)}]\n"
    f"\n"
    f"Plateau only (N=6)\n"
    f"  MK p={mk_plat['p']:.3f}  SR p={sr_plat['p']:.3f}  ITM p={itm_plat['p']:.3f}\n"
    f"  No significant trend in plateau phase"
)
ax1.text(0.015, 0.97, box, transform=ax1.transAxes, fontsize=8.3,
         va='top', family='monospace',
         bbox=dict(boxstyle='round,pad=0.55', fc='#fffde7', ec='#f9a825', alpha=0.93))

yoy_vals = np.diff(recycling)
bar_cols = ['#27ae60' if v >= 0 else '#c0392b' for v in yoy_vals]
ax2.bar(np.arange(len(yoy_vals)), yoy_vals,
        color=bar_cols, edgecolor='white', lw=0.5, zorder=4)
ax2.axhline(0, color='black', lw=0.8)
ax2.plot([-0.5, 4.5], [growth_mean,  growth_mean],  '--',
         color='#27ae60', lw=2, label=f'Growth mean: {growth_mean:+.2f} pp/yr')
ax2.plot([4.5, 10.5], [plateau_mean, plateau_mean], '--',
         color='#e67e22', lw=2, label=f'Plateau mean: {plateau_mean:+.2f} pp/yr')
ax2.set_xticks(np.arange(len(yoy_vals)))
ax2.set_xticklabels(years_labels[1:], rotation=45, ha='right', fontsize=9)
ax2.set_ylabel('Year-on-year\nchange (pp)', fontsize=9)
ax2.legend(fontsize=9, framealpha=0.9, loc='upper right')
ax2.grid(True, alpha=0.2, ls=':', axis='y')

plt.tight_layout()
plt.savefig('figure_trend_tests.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved --> figure_trend_tests.png")


# ── Figure 2 — ITM diagnostic scatter ───────────────────────────────────────
fig2, (axA, axB) = plt.subplots(1, 2, figsize=(12, 5))
fig2.suptitle(
    'ITM Diagnostic - Merthyr Tydfil 2012-13 to 2023-24\n'
    'Points above 1:1 line = increasing trend | below = decreasing',
    fontsize=12, fontweight='bold'
)

def itm_panel(ax, itm_r, title, col, units):
    x1, x2 = itm_r['x1'], itm_r['x2']
    lo = min(x1.min(), x2.min()) * 0.97
    hi = max(x1.max(), x2.max()) * 1.02
    ax.fill_between([lo, hi], [lo, hi], hi, alpha=0.06, color='#27ae60')
    ax.fill_between([lo, hi], lo, [lo, hi], alpha=0.06, color='#c0392b')
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1.6, label='No-trend (1:1)', zorder=2)
    ax.scatter(x1, x2, color=col, s=90, zorder=5,
               edgecolors='white', lw=0.8, label='Sorted data pairs')
    trend_word = 'Significant' if itm_r['sig'] else 'No significant'
    ax.set_title(
        f'{title}\nS_ITM = {itm_r["S_ITM"]:.4f}   p = {itm_r["p"]:.4f}'
        f'  ({trend_word} trend)',
        fontsize=10.5
    )
    ax.set_xlabel(f'First half - sorted ({units})', fontsize=10)
    ax.set_ylabel(f'Second half - sorted ({units})', fontsize=10)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.2, ls=':')
    ax.text(0.97, 0.03, '<- Decreasing', transform=ax.transAxes,
            fontsize=8, ha='right', color='#c0392b', alpha=0.75)
    ax.text(0.03, 0.97, 'Increasing ->', transform=ax.transAxes,
            fontsize=8, va='top', color='#27ae60', alpha=0.75)

itm_panel(axA, itm_full, 'Recycling Rate',            '#1a5f8a', '%')
itm_panel(axB, itm_res,  'Residual Waste per Person', '#e67e22', 'kg/person')

plt.tight_layout()
plt.savefig('figure_itm_diagnostic.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saved --> figure_itm_diagnostic.png")
print(f"\n{SEP}\nAll done. Two figures saved.\n{SEP}")
