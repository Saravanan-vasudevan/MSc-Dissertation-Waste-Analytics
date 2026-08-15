import os
import sys

import numpy as np
from numpy.linalg import svd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.stats.diagnostic import acorr_ljungbox
import scipy.stats as stats

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from data_loader import load_merthyr_recycling_rates

# Used to have its own rounded copy of the rates (49.1, 51.3, 53.8, ...)
# which drifted from the CSV-derived values the other scripts used.
# Now pulling from data_loader so everything stays in sync.
# If the numbers in this output don't match what's already in the
# dissertation, re-check which decimal places changed.
rates = np.array(load_merthyr_recycling_rates())
N = len(rates)

def diagonal_average(matrix):
    L, K = matrix.shape
    N_out = L + K - 1
    series, counts = np.zeros(N_out), np.zeros(N_out)
    for i in range(L):
        for j in range(K):
            series[i+j] += matrix[i, j]
            counts[i+j] += 1
    return series / counts

def reconstruct(U, sigma, VT, indices):
    result = np.zeros((U.shape[0], VT.shape[1]))
    for i in indices:
        result += sigma[i] * np.outer(U[:, i], VT[i, :])
    return diagonal_average(result)

def w_weights(N, L):
    K = N - L + 1
    w = np.zeros(N)
    for i in range(N):
        w[i] = min(i+1, L, K, N-i)
    return w

def w_corr_matrix(X, L, n_comp):
    N = len(X)
    K = N - L + 1
    traj = np.array([X[i:i+L] for i in range(K)]).T
    U, sigma, VT = svd(traj, full_matrices=False)
    w = w_weights(N, L)
    comps = [reconstruct(U, sigma, VT, [i]) for i in range(n_comp)]
    wcorr = np.zeros((n_comp, n_comp))
    for i in range(n_comp):
        for j in range(n_comp):
            wij = np.sum(w * comps[i] * comps[j])
            wii = np.sum(w * comps[i]**2)
            wjj = np.sum(w * comps[j]**2)
            wcorr[i,j] = wij / np.sqrt(wii * wjj)
    return np.abs(wcorr), comps

def ssa_insample_mae(X, L, n_components):
    """Leave-one-out style MAE: fit on X[:t], predict X[t], for t in [L+1, N).
    Only gives 5 error values with N=12/L=6, which is thin, but it's what
    we've got."""
    N = len(X)
    errors = []
    for t in range(L+1, N):
        x_train = X[:t]
        K = t - L + 1
        traj = np.array([x_train[i:i+L] for i in range(K)]).T
        U, sigma, VT = svd(traj, full_matrices=False)
        U_r = U[:, :n_components]
        pi = U_r[-1, :]
        nu2 = float(np.dot(pi, pi))
        R = (U_r[:-1, :] @ pi) / (1.0 - nu2)
        pred = float(np.dot(R, x_train[-(L-1):]))
        errors.append(abs(pred - X[t]))
    return np.mean(errors)


# ════════════════════════════════════════════
# 1. SSA MAE
# ════════════════════════════════════════════
ssa_mae = ssa_insample_mae(rates, L=6, n_components=1)
print("=" * 55)
print("1. SSA IN-SAMPLE MAE")
print("=" * 55)
print(f"   MAE = {ssa_mae:.2f} percentage points")

# ════════════════════════════════════════════
# 2. W-CORRELATION MATRIX
# ════════════════════════════════════════════
wcorr, comps = w_corr_matrix(rates, L=6, n_comp=4)
print("\n" + "=" * 55)
print("2. W-CORRELATION MATRIX (first 4 components)")
print("=" * 55)
print(np.round(wcorr, 3))
print(f"\n   Component 1 vs 2: {wcorr[0,1]:.3f}")
print(f"   Component 1 vs 3: {wcorr[0,2]:.3f}")
print(f"   Component 1 vs 4: {wcorr[0,3]:.3f}")
print("   (All near 0 = Component 1 cleanly separable as trend)")

# ════════════════════════════════════════════
# 3. HOLT'S RESIDUALS
# ════════════════════════════════════════════
holt_fit = ExponentialSmoothing(rates, trend="add", damped_trend=True).fit(optimized=True)
holt_resid = holt_fit.resid

print("\n" + "=" * 55)
print("3. HOLT'S EXPONENTIAL SMOOTHING — RESIDUAL DIAGNOSTICS")
print("=" * 55)
print(f"   Alpha (level smoothing):  {holt_fit.params['smoothing_level']:.4f}")
print(f"   Beta  (trend smoothing):  {holt_fit.params['smoothing_trend']:.4f}")
print(f"   Phi   (damping):          {holt_fit.params['damping_trend']:.4f}")
print(f"   MAE (in-sample):          {np.mean(np.abs(holt_resid)):.2f} pp")

# Ljung-Box at lag 5 — lag 5 is arbitrary but it's what the
# dissertation uses and N=12 doesn't give much room anyway
lb = acorr_ljungbox(holt_resid, lags=[5], return_df=True)
lb_stat = float(lb['lb_stat'].values[0])
lb_pval = float(lb['lb_pvalue'].values[0])
print(f"\n   Ljung-Box test (lag 5):")
print(f"   Statistic = {lb_stat:.2f},  p-value = {lb_pval:.3f}")
if lb_pval > 0.05:
    print("   -> Residuals consistent with white noise (p > 0.05)")
else:
    print("   -> Some autocorrelation detected (p < 0.05)")

sw_stat, sw_p = stats.shapiro(holt_resid)
print(f"\n   Shapiro-Wilk normality test:")
print(f"   Statistic = {sw_stat:.4f},  p-value = {sw_p:.3f}")
if sw_p > 0.05:
    print("   -> Residuals approximately normal (p > 0.05)")
else:
    print("   -> Residuals may not be normal (p < 0.05)")

print(f"\n   Mean of residuals: {np.mean(holt_resid):.4f}")
print(f"   Std of residuals:  {np.std(holt_resid):.4f}")

# ════════════════════════════════════════════
# 4. MAE COMPARISON
# ════════════════════════════════════════════
arima_fit = ARIMA(rates, order=(1,1,0)).fit()
arima_resid = arima_fit.resid[1:]   # first diff loses one obs
arima_mae = np.mean(np.abs(arima_resid))

from sklearn.linear_model import LinearRegression
X_lr = np.arange(N).reshape(-1,1)
lr_fitted = LinearRegression().fit(X_lr, rates).predict(X_lr)
lr_mae = np.mean(np.abs(rates - lr_fitted))

print("\n" + "=" * 55)
print("4. MAE COMPARISON — ALL FOUR MODELS")
print("=" * 55)
print(f"   Linear Regression:        {lr_mae:.2f} pp")
print(f"   ARIMA(1,1,0):             {arima_mae:.2f} pp")
print(f"   Holt's (damped):          {np.mean(np.abs(holt_resid)):.2f} pp")
print(f"   SSA (L=6, 1 eigentriple): {ssa_mae:.2f} pp")

print("\nDone.")
