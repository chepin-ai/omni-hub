#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OMNI-HUB v11.0 — Statistical Validation Framework
===================================================
严格的统计验证框架：Bootstrap重采样、Monte Carlo模拟、
交叉验证、假设检验 —— 仅使用numpy实现，零外部统计库依赖。

版本: 11.0.0
日期: 2026-09-17

统计方法:
- Bootstrap: Efron (1987), BCa区间
- Monte Carlo: Halton低差异序列 / numpy.random
- Jackknife: Quenouille (1956), Tukey (1958)
- Welch t-test: 不等方差t检验
- KS-test: Kolmogorov-Smirnov双样本检验
- Binomial test: 精确二项检验
- Power analysis: 正态近似功效分析

兼容性:
- v11_standards.py: UnifiedFieldState
- v11_consciousness_emergence_system.py: EmergenceSnapshot
"""

from __future__ import annotations

import json
import logging
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast,
)

import numpy as np
from numpy.random import Generator

# =============================================================================
# Compatibility imports from v11 standards
# =============================================================================
try:
    from v11_standards import (
        UnifiedFieldState,
        DimensionIndex,
        UNIFIED_FIELD_DIMENSIONS,
        PHI_GOLDEN,
        get_logger,
        OMNIHUBTheoreticalError,
    )
except ImportError:
    # Fallback minimal definitions for standalone testing
    UNIFIED_FIELD_DIMENSIONS = 64
    PHI_GOLDEN = 1.618033988749895

    class DimensionIndex(Enum):
        DIM_EMERGENCE = 48
        DIM_SYNERGY = 52
        DIM_SELF_ORG = 49
        DIM_COHERENCE = 1

    class UnifiedFieldState:
        def __init__(self, dimensions: int = UNIFIED_FIELD_DIMENSIONS) -> None:
            self.dimensions = dimensions
            self.vector: List[float] = [0.0] * dimensions
            self.timestamp: float = 0.0
            self.version = "11.0.0"

        def get(self, dim: DimensionIndex) -> float:
            return self.vector[dim.value]

        def set(self, dim: DimensionIndex, value: float) -> None:
            self.vector[dim.value] = float(value)

    class OMNIHUBTheoreticalError(Exception):
        pass

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger("OMNI-HUB." + name)


try:
    from v11_consciousness_emergence_system import EmergenceSnapshot
except ImportError:
    @dataclass
    class EmergenceSnapshot:  # type: ignore[no-redef]
        timestamp: float
        emergence_index: float
        state: Any = None
        components: Dict[str, float] = field(default_factory=dict)
        module_contributions: List[float] = field(default_factory=list)
        coherence_matrix: List[List[float]] = field(default_factory=list)
        metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Module logger
# =============================================================================
logger = get_logger("statistical_validation")


# =============================================================================
# Section 0: Pure-numpy statistical utility functions
# =============================================================================


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    """标准正态累积分布函数 (Abramowitz & Stegun近似)."""
    # Using the error function approximation
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = np.sign(x)
    x_abs = np.abs(x) / np.sqrt(2.0)
    t = 1.0 / (1.0 + p * x_abs)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x_abs * x_abs)
    return 0.5 * (1.0 + sign * y)


def _normal_ppf(p: np.ndarray) -> np.ndarray:
    """标准正态分位数函数 (逆CDF, Moro近似)."""
    p = np.asarray(p, dtype=float)
    result = np.empty_like(p)
    # Lower tail
    mask = p <= 0.5
    q = p[mask]
    r = np.sqrt(-2.0 * np.log(q))
    result[mask] = -r + (
        2.515517 + 0.802853 * r + 0.010328 * r ** 2
    ) / (1.0 + 1.432788 * r + 0.189269 * r ** 2 + 0.001308 * r ** 3)
    # Upper tail
    q = p[~mask]
    r = np.sqrt(-2.0 * np.log(1.0 - q))
    result[~mask] = r - (
        2.515517 + 0.802853 * r + 0.010328 * r ** 2
    ) / (1.0 + 1.432788 * r + 0.189269 * r ** 2 + 0.001308 * r ** 3)
    return result


def _beta_cdf(x: float, a: float, b: float, n_terms: int = 100) -> float:
    """正则化不完全Beta函数 I_x(a,b) —— 使用连续分数展开."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters must be positive")

    # Use symmetry relation for efficiency
    if x > (a + 1.0) / (a + b + 2.0):
        return 1.0 - _beta_cdf(1.0 - x, b, a, n_terms)

    # Log of Beta function
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    # Front factor
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b - lbeta) / a

    # Modified Lentz's method for continued fraction
    fpmin = 1e-30
    m2 = 0.0
    aa = 1.0
    c = 1.0
    d = 1.0 - (a + b) * x / (a + 1.0)
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, n_terms + 1):
        m2 = 2 * m
        # Even step
        aa = m * (b - m) * x / ((a + m2 - 1.0) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        # Odd step
        aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + m2 + 1.0))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-8:
            break
    return front * h


def _t_cdf(t: float, df: float) -> float:
    """学生t分布累积分布函数 (使用Beta函数关系)."""
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive")
    x = df / (df + t * t)
    if t >= 0:
        return 1.0 - 0.5 * _beta_cdf(x, 0.5 * df, 0.5)
    else:
        return 0.5 * _beta_cdf(x, 0.5 * df, 0.5)


def _t_sf(t: float, df: float) -> float:
    """学生t分布生存函数 (1 - CDF)."""
    return 1.0 - _t_cdf(t, df)


def _welch_t_test(
    sample1: np.ndarray,
    sample2: np.ndarray,
    alternative: str = "two-sided",
) -> Tuple[float, float]:
    """
    Welch's t-test (不等方差t检验) —— 纯numpy实现.

    Parameters
    ----------
    sample1, sample2 : array-like
        两个独立样本
    alternative : {"two-sided", "less", "greater"}
        备择假设方向

    Returns
    -------
    t_statistic : float
        t统计量
    p_value : float
        p值
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    n1, n2 = len(x1), len(x2)
    if n1 < 2 or n2 < 2:
        raise ValueError("Each sample must have at least 2 observations")

    m1, m2 = np.mean(x1), np.mean(x2)
    v1, v2 = np.var(x1, ddof=1), np.var(x2, ddof=1)

    # Welch-Satterthwaite自由度
    se1_sq = v1 / n1
    se2_sq = v2 / n2
    se = np.sqrt(se1_sq + se2_sq)
    if se == 0:
        return 0.0, 1.0

    t_stat = (m1 - m2) / se
    df = (se1_sq + se2_sq) ** 2 / (
        se1_sq ** 2 / (n1 - 1) + se2_sq ** 2 / (n2 - 1)
    )

    if alternative == "two-sided":
        p_value = 2.0 * min(_t_cdf(-abs(t_stat), df), _t_sf(-abs(t_stat), df))
    elif alternative == "greater":
        p_value = _t_sf(t_stat, df)
    elif alternative == "less":
        p_value = _t_cdf(t_stat, df)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")

    return float(t_stat), float(p_value)


def _ks_2sample_test(
    sample1: np.ndarray,
    sample2: np.ndarray,
) -> Tuple[float, float]:
    """
    双样本Kolmogorov-Smirnov检验 —— 纯numpy实现.

    H0: 两个样本来自同一分布.

    Returns
    -------
    d_statistic : float
        KS统计量 D = max|ECDF1(x) - ECDF2(x)|
    p_value : float
        近似p值 (基于Smirnov渐近公式)
    """
    x1 = np.asarray(sample1, dtype=float)
    x2 = np.asarray(sample2, dtype=float)
    n1, n2 = len(x1), len(x2)
    if n1 == 0 or n2 == 0:
        raise ValueError("Samples must not be empty")

    # Combine and sort all data points
    data = np.concatenate([x1, x2])
    data_sorted = np.sort(data)

    # Build ECDFs at all unique points
    ecdf1 = np.searchsorted(np.sort(x1), data_sorted, side="right") / n1
    ecdf2 = np.searchsorted(np.sort(x2), data_sorted, side="right") / n2

    d_stat = float(np.max(np.abs(ecdf1 - ecdf2)))

    # Smirnov渐近p值近似
    n_eff = n1 * n2 / (n1 + n2)
    lambda_val = (np.sqrt(n_eff) + 0.12 + 0.11 / np.sqrt(n_eff)) * d_stat
    # Kolmogorov分布的互补CDF: Q(lambda) = 2 * sum_{k=1}^{inf} (-1)^{k-1} exp(-2 k^2 lambda^2)
    p_value = 0.0
    for k in range(1, 101):
        term = 2.0 * ((-1) ** (k - 1)) * np.exp(-2.0 * k * k * lambda_val * lambda_val)
        p_value += term
        if abs(term) < 1e-10:
            break
    p_value = max(0.0, min(1.0, p_value))

    return d_stat, p_value


def _binom_test(k_success: int, n_trials: int, p_null: float = 0.5,
                alternative: str = "two-sided") -> float:
    """
    精确二项检验 —— 纯numpy实现.

    H0: p = p_null
    """
    if k_success < 0 or n_trials < 0 or k_success > n_trials:
        raise ValueError("Invalid k_success or n_trials")
    if not 0 < p_null < 1:
        raise ValueError("p_null must be in (0, 1)")

    if alternative == "two-sided":
        # 计算精确p值：所有概率 <= 观察概率的k之和
        probs = np.array([
            math.comb(n_trials, k) * (p_null ** k) * ((1 - p_null) ** (n_trials - k))
            for k in range(n_trials + 1)
        ])
        obs_prob = probs[k_success]
        p_value = float(np.sum(probs[probs <= obs_prob + 1e-15]))
        return min(1.0, p_value)
    elif alternative == "greater":
        p_value = 0.0
        for k in range(k_success, n_trials + 1):
            p_value += math.comb(n_trials, k) * (p_null ** k) * ((1 - p_null) ** (n_trials - k))
        return p_value
    elif alternative == "less":
        p_value = 0.0
        for k in range(0, k_success + 1):
            p_value += math.comb(n_trials, k) * (p_null ** k) * ((1 - p_null) ** (n_trials - k))
        return p_value
    else:
        raise ValueError(f"Unknown alternative: {alternative}")


def _power_analysis_ttest(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0,
) -> int:
    """
    两独立样本t检验的功效分析 —— 正态近似.

    Returns所需每组合计样本量（向上取整）.
    """
    if effect_size <= 0:
        raise ValueError("Effect size must be positive")
    z_alpha = float(_normal_ppf(np.array([1.0 - alpha / 2.0]))[0])
    z_beta = float(_normal_ppf(np.array([power]))[0])
    n1 = ((z_alpha + z_beta) / effect_size) ** 2 * (1.0 + 1.0 / ratio)
    return int(np.ceil(n1))


def _halton_sequence(n: int, base: int, seed: int = 42) -> np.ndarray:
    """
    生成Halton低差异序列（van der Corput序列）.

    Parameters
    ----------
    n : int
        序列长度
    base : int
        基数（必须为质数且不同于其他维度所用基数）
    seed : int
        随机偏移种子（用于scrambling）

    Returns
    -------
    sequence : ndarray, shape (n,)
        [0, 1)区间的低差异序列
    """
    seq = np.zeros(n, dtype=float)
    rng = np.random.default_rng(seed)
    for i in range(n):
        f = 1.0
        r = 0.0
        idx = i + 1  # Start from 1
        while idx > 0:
            f /= base
            r += f * (idx % base)
            idx //= base
        seq[i] = r
    # Digital scrambling for better uniformity
    perm = rng.permutation(n)
    seq = (seq + perm / n) % 1.0
    return seq


def _sobol_sequence(n: int, dim: int, seed: int = 42) -> np.ndarray:
    """
    简化的Sobol-like序列生成器（numpy无原生Sobol，使用Halton回退）.

    生成n×dim的准随机序列.
    """
    # First few primes for Halton bases
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
    result = np.zeros((n, dim), dtype=float)
    for d in range(min(dim, len(primes))):
        result[:, d] = _halton_sequence(n, primes[d], seed=seed + d)
    # For dimensions beyond available primes, use random
    if dim > len(primes):
        rng = np.random.default_rng(seed)
        result[:, len(primes):] = rng.random((n, dim - len(primes)))
    return result


# =============================================================================
# Section 1: BootstrapValidator
# =============================================================================


@dataclass
class BootstrapResult:
    """Bootstrap验证结果容器"""
    point_estimate: float
    ci_percentile: Tuple[float, float]
    ci_bca: Tuple[float, float]
    standard_error: float
    bias: float
    n_bootstrap: int
    bootstrap_distribution: np.ndarray
    acceleration: float
    bias_correction: float
    alpha: float
    metric_name: str = "emergence_index"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "point_estimate": float(self.point_estimate),
            "ci_percentile": [float(self.ci_percentile[0]), float(self.ci_percentile[1])],
            "ci_bca": [float(self.ci_bca[0]), float(self.ci_bca[1])],
            "standard_error": float(self.standard_error),
            "bias": float(self.bias),
            "n_bootstrap": self.n_bootstrap,
            "acceleration": float(self.acceleration),
            "bias_correction": float(self.bias_correction),
            "alpha": self.alpha,
        }


class BootstrapValidator:
    """
    涌现指数E的Bootstrap验证器.

    实现Efron (1987)的百分位数Bootstrap和BCa (bias-corrected
    and accelerated)置信区间。

    输入为N×N耦合矩阵，通过对矩阵元素重采样估计E的
    统计不确定性。
    """

    def __init__(
        self,
        n_bootstrap: int = 1000,
        confidence_level: float = 0.95,
        rng: Optional[Generator] = None,
    ) -> None:
        self.n_bootstrap = n_bootstrap
        self.confidence_level = confidence_level
        self.alpha = 1.0 - confidence_level
        self.rng = rng or np.random.default_rng()
        logger.info(
            "BootstrapValidator initialized: n=%d, alpha=%.3f",
            n_bootstrap, self.alpha,
        )

    def compute_emergence_from_coupling(
        self,
        coupling_matrix: np.ndarray,
    ) -> float:
        """
        从耦合矩阵计算涌现指数E.

        E = trace(C^T C) / N^2 + lambda * |det(C)|^(1/N)

        其中C为耦合矩阵，lambda为涌现放大系数。
        """
        C = np.asarray(coupling_matrix, dtype=float)
        if C.ndim != 2 or C.shape[0] != C.shape[1]:
            raise OMNIHUBTheoreticalError(
                f"Coupling matrix must be square N×N, got shape {C.shape}",
                error_code="OMNI-STAT-001",
            )
        N = C.shape[0]
        if N == 0:
            return 0.0

        # Frobenius范数归一化
        frob_norm = np.trace(C.T @ C) / (N * N)
        # 行列式贡献（正则化避免奇异）
        det_C = np.linalg.det(C + np.eye(N) * 1e-6)
        det_contrib = np.abs(det_C) ** (1.0 / N) if N > 0 else 0.0
        # 综合涌现指数
        lambda_amp = PHI_GOLDEN * 0.1  # 涌现放大系数
        E = frob_norm + lambda_amp * det_contrib
        return float(E)

    def _jackknife_acceleration(
        self,
        coupling_matrix: np.ndarray,
    ) -> float:
        """
        使用Jackknife估计acceleration系数a (BCa方法).

        a = sum((theta_(-i) - theta_(.))^3) / (6 * [sum((theta_(-i) - theta_(.))^2)]^(3/2))
        """
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        if N < 3:
            return 0.0

        theta_full = self.compute_emergence_from_coupling(C)
        # Leave-one-out estimates: remove each row/column pair
        thetas = np.zeros(N)
        for i in range(N):
            mask = np.arange(N) != i
            C_loo = C[np.ix_(mask, mask)]
            thetas[i] = self.compute_emergence_from_coupling(C_loo)

        theta_mean = np.mean(thetas)
        deviations = thetas - theta_mean
        numerator = np.sum(deviations ** 3)
        denominator = 6.0 * (np.sum(deviations ** 2) ** 1.5)
        if denominator < 1e-15:
            return 0.0
        return float(numerator / denominator)

    def _jackknife_estimate(
        self,
        coupling_matrix: np.ndarray,
    ) -> Tuple[float, float, np.ndarray]:
        """
        Jackknife点估计和方差估计.

        Returns
        -------
        jackknife_estimate : float
            伪值估计
        jackknife_variance : float
            Jackknife方差
        leave_one_out_estimates : ndarray
            所有LOO估计值
        """
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        thetas = np.zeros(N)
        for i in range(N):
            mask = np.arange(N) != i
            C_loo = C[np.ix_(mask, mask)]
            thetas[i] = self.compute_emergence_from_coupling(C_loo)

        theta_full = self.compute_emergence_from_coupling(C)
        # Pseudo-values
        pseudovalues = N * theta_full - (N - 1) * thetas
        jack_estimate = float(np.mean(pseudovalues))
        jack_variance = float(np.var(pseudovalues, ddof=1) / N)
        return jack_estimate, jack_variance, thetas

    def validate(
        self,
        coupling_matrix: np.ndarray,
        metric_name: str = "emergence_index",
    ) -> BootstrapResult:
        """
        对耦合矩阵进行Bootstrap验证.

        使用参数Bootstrap法（Parametric Bootstrap）：保持原始矩阵结构，
        对非零耦合值施加小的随机扰动（高斯噪声），模拟测量不确定性。
        扰动幅度与元素值成比例（相对噪声），确保bootstrap分布
        围绕原始估计值对称波动。

        1. 计算原始点估计 theta_hat
        2. 施加n_bootstrap次参数化扰动
        3. 计算百分位数置信区间
        4. 计算BCa区间 (Efron 1987, BCa)
        """
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        theta_hat = self.compute_emergence_from_coupling(C)

        # Parametric bootstrap: add small Gaussian noise to non-zero elements
        # Noise level scaled by element magnitude (heteroscedastic)
        nz_mask = np.abs(C) > 1e-12
        bootstrap_estimates = np.zeros(self.n_bootstrap)
        for b in range(self.n_bootstrap):
            C_b = C.copy()
            # Relative noise: std = 0.05 * |value| for non-zero elements
            noise = np.zeros_like(C)
            noise[nz_mask] = self.rng.normal(
                loc=0.0,
                scale=0.05 * np.abs(C[nz_mask]),
                size=np.count_nonzero(nz_mask),
            )
            C_b = C_b + noise
            # Ensure symmetry
            C_b = (C_b + C_b.T) / 2.0
            # Clip to physical bounds
            C_b = np.clip(C_b, 0.0, 1.0)
            bootstrap_estimates[b] = self.compute_emergence_from_coupling(C_b)

        # Percentile CI
        lower_p = np.percentile(bootstrap_estimates, 100.0 * self.alpha / 2.0)
        upper_p = np.percentile(bootstrap_estimates, 100.0 * (1.0 - self.alpha / 2.0))

        # BCa interval (Efron 1987)
        # Step 1: Bias correction z0
        prop_below = np.mean(bootstrap_estimates < theta_hat)
        prop_below = max(1e-10, min(1.0 - 1e-10, prop_below))
        z0 = float(_normal_ppf(np.array([prop_below]))[0])

        # Step 2: Acceleration a (jackknife LOO influence)
        a = self._jackknife_acceleration(C)

        # Step 3: Adjusted percentiles
        z_alpha_lo = float(_normal_ppf(np.array([self.alpha / 2.0]))[0])
        z_alpha_hi = float(_normal_ppf(np.array([1.0 - self.alpha / 2.0]))[0])

        # BCa adjusted alpha levels
        denom1 = 1.0 - a * (z0 + z_alpha_lo)
        denom2 = 1.0 - a * (z0 + z_alpha_hi)
        # Guard against division by zero
        if abs(denom1) < 1e-10:
            denom1 = 1e-10 if denom1 >= 0 else -1e-10
        if abs(denom2) < 1e-10:
            denom2 = 1e-10 if denom2 >= 0 else -1e-10

        alpha1 = _normal_cdf(z0 + (z0 + z_alpha_lo) / denom1)
        alpha2 = _normal_cdf(z0 + (z0 + z_alpha_hi) / denom2)

        # Clamp to valid percentile range
        alpha1 = max(0.001, min(0.999, alpha1))
        alpha2 = max(0.001, min(0.999, alpha2))

        lower_bca = float(np.percentile(bootstrap_estimates, 100.0 * alpha1))
        upper_bca = float(np.percentile(bootstrap_estimates, 100.0 * alpha2))

        se = float(np.std(bootstrap_estimates, ddof=1))
        bias = float(np.mean(bootstrap_estimates) - theta_hat)

        result = BootstrapResult(
            point_estimate=theta_hat,
            ci_percentile=(lower_p, upper_p),
            ci_bca=(lower_bca, upper_bca),
            standard_error=se,
            bias=bias,
            n_bootstrap=self.n_bootstrap,
            bootstrap_distribution=bootstrap_estimates,
            acceleration=a,
            bias_correction=z0,
            alpha=self.alpha,
            metric_name=metric_name,
        )

        logger.info(
            "Bootstrap %s: E=%.4f, BCa-CI=[%.4f, %.4f], SE=%.4f, bias=%.4f, a=%.4f",
            metric_name, theta_hat, lower_bca, upper_bca, se, bias, a,
        )
        return result


# =============================================================================
# Section 2: MonteCarloStability
# =============================================================================


@dataclass
class MonteCarloResult:
    """蒙特卡洛稳定性测试结果容器"""
    noise_level: float
    mean_E: float
    std_E: float
    cv_E: float  # coefficient of variation
    min_E: float
    max_E: float
    n_trials: int
    is_stable: bool
    cv_threshold: float
    E_distribution: np.ndarray

    def to_dict(self) -> Dict[str, Any]:
        return {
            "noise_level": float(self.noise_level),
            "mean_E": float(self.mean_E),
            "std_E": float(self.std_E),
            "cv_E": float(self.cv_E),
            "min_E": float(self.min_E),
            "max_E": float(self.max_E),
            "n_trials": self.n_trials,
            "is_stable": bool(self.is_stable),
            "cv_threshold": float(self.cv_threshold),
        }


@dataclass
class MonteCarloStabilityReport:
    """蒙特卡洛综合报告"""
    results: List[MonteCarloResult]
    overall_stable: bool
    critical_noise_level: Optional[float]
    correlation_with_noise: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": [r.to_dict() for r in self.results],
            "overall_stable": self.overall_stable,
            "critical_noise_level": self.critical_noise_level,
            "correlation_with_noise": float(self.correlation_with_noise),
        }


class MonteCarloStability:
    """
    蒙特卡洛稳定性测试.

    对耦合矩阵施加不同水平的高斯扰动，通过Halton序列或
    随机采样生成扰动矩阵，重新计算涌现指数E，评估E对
    噪声的敏感度。
    """

    def __init__(
        self,
        n_trials: int = 1000,
        noise_levels: List[float] = None,
        cv_threshold: float = 0.05,
        use_halton: bool = True,
        rng: Optional[Generator] = None,
    ) -> None:
        self.n_trials = n_trials
        self.noise_levels = noise_levels or [0.01, 0.05, 0.1, 0.2]
        self.cv_threshold = cv_threshold
        self.use_halton = use_halton
        self.rng = rng or np.random.default_rng()
        logger.info(
            "MonteCarloStability initialized: n_trials=%d, noise_levels=%s, cv_threshold=%.1f%%",
            n_trials, self.noise_levels, cv_threshold * 100,
        )

    def compute_emergence_from_coupling(
        self,
        coupling_matrix: np.ndarray,
    ) -> float:
        """共享的涌现指数计算（与BootstrapValidator一致）."""
        C = np.asarray(coupling_matrix, dtype=float)
        if C.ndim != 2 or C.shape[0] != C.shape[1]:
            raise OMNIHUBTheoreticalError(
                f"Coupling matrix must be square N×N, got {C.shape}",
                error_code="OMNI-STAT-002",
            )
        N = C.shape[0]
        if N == 0:
            return 0.0
        frob_norm = np.trace(C.T @ C) / (N * N)
        det_C = np.linalg.det(C + np.eye(N) * 1e-6)
        det_contrib = np.abs(det_C) ** (1.0 / N) if N > 0 else 0.0
        lambda_amp = PHI_GOLDEN * 0.1
        E = frob_norm + lambda_amp * det_contrib
        return float(E)

    def _generate_perturbation(
        self,
        shape: Tuple[int, ...],
        noise_level: float,
        trial_idx: int,
    ) -> np.ndarray:
        """
        生成扰动矩阵.

        使用Halton序列或高斯随机生成扰动.
        """
        total_elements = int(np.prod(shape))
        if self.use_halton:
            # Use Halton sequence for quasi-random perturbation
            halton = _halton_sequence(total_elements, base=2, seed=42 + trial_idx)
            # Transform uniform [0,1) to Gaussian via Box-Muller
            u1 = halton[:total_elements // 2 + 1]
            u2 = _halton_sequence(len(u1), base=3, seed=43 + trial_idx)
            z1 = np.sqrt(-2.0 * np.log(u1 + 1e-10)) * np.cos(2.0 * np.pi * u2)
            z2 = np.sqrt(-2.0 * np.log(u1 + 1e-10)) * np.sin(2.0 * np.pi * u2)
            gaussian = np.concatenate([z1, z2])[:total_elements]
        else:
            gaussian = self.rng.standard_normal(total_elements)

        perturbation = noise_level * gaussian.reshape(shape)
        return perturbation

    def test_stability(
        self,
        coupling_matrix: np.ndarray,
    ) -> MonteCarloStabilityReport:
        """
        执行蒙特卡洛稳定性测试.

        对每个噪声水平，施加n_trials次扰动，计算E的分布.
        """
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        base_E = self.compute_emergence_from_coupling(C)
        results: List[MonteCarloResult] = []

        for noise_level in self.noise_levels:
            E_trials = np.zeros(self.n_trials)
            for trial in range(self.n_trials):
                perturbation = self._generate_perturbation(
                    (N, N), noise_level, trial,
                )
                C_perturbed = C + perturbation
                # Ensure symmetry preservation for undirected coupling
                C_perturbed = (C_perturbed + C_perturbed.T) / 2.0
                # Clip to reasonable bounds
                C_perturbed = np.clip(C_perturbed, 0.0, 1.0)
                E_trials[trial] = self.compute_emergence_from_coupling(C_perturbed)

            mean_E = float(np.mean(E_trials))
            std_E = float(np.std(E_trials, ddof=1))
            cv_E = std_E / mean_E if mean_E != 0 else float("inf")
            is_stable = cv_E < self.cv_threshold

            result = MonteCarloResult(
                noise_level=noise_level,
                mean_E=mean_E,
                std_E=std_E,
                cv_E=cv_E,
                min_E=float(np.min(E_trials)),
                max_E=float(np.max(E_trials)),
                n_trials=self.n_trials,
                is_stable=is_stable,
                cv_threshold=self.cv_threshold,
                E_distribution=E_trials,
            )
            results.append(result)

            logger.info(
                "MC noise=%.2f: mean_E=%.4f, std=%.4f, CV=%.2f%%, stable=%s",
                noise_level, mean_E, std_E, cv_E * 100, is_stable,
            )

        # Overall stability: stable at lowest noise level
        overall_stable = results[0].is_stable if results else False

        # Find critical noise level (first unstable)
        critical_noise = None
        for r in results:
            if not r.is_stable:
                critical_noise = r.noise_level
                break

        # Correlation between noise level and CV
        noise_arr = np.array([r.noise_level for r in results])
        cv_arr = np.array([r.cv_E for r in results])
        if len(noise_arr) > 1:
            corr = float(np.corrcoef(noise_arr, cv_arr)[0, 1])
        else:
            corr = 0.0

        return MonteCarloStabilityReport(
            results=results,
            overall_stable=overall_stable,
            critical_noise_level=critical_noise,
            correlation_with_noise=corr,
        )


# =============================================================================
# Section 3: CrossValidationIndex
# =============================================================================


@dataclass
class JackknifeResult:
    """Jackknife交叉验证结果"""
    metric_name: str
    full_estimate: float
    jackknife_estimate: float
    jackknife_variance: float
    jackknife_se: float
    ci_normal: Tuple[float, float]
    leave_one_out_estimates: np.ndarray
    influence_scores: np.ndarray
    most_influential_item: int
    least_influential_item: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "full_estimate": float(self.full_estimate),
            "jackknife_estimate": float(self.jackknife_estimate),
            "jackknife_variance": float(self.jackknife_variance),
            "jackknife_se": float(self.jackknife_se),
            "ci_normal": [float(self.ci_normal[0]), float(self.ci_normal[1])],
            "most_influential_item": int(self.most_influential_item),
            "least_influential_item": int(self.least_influential_item),
        }


@dataclass
class CrossValidationReport:
    """交叉验证综合报告"""
    jackknife_results: List[JackknifeResult]
    stability_score: float  # Average relative CI width
    dependency_rating: str  # "low" / "moderate" / "high"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jackknife_results": [r.to_dict() for r in self.jackknife_results],
            "stability_score": float(self.stability_score),
            "dependency_rating": self.dependency_rating,
        }


class CrossValidationIndex:
    """
    留一项目交叉验证（Jackknife方法）.

    Quenouille (1956) 提出，Tukey (1958) 发展的偏差减少和
    方差估计技术。每次移除一个模块（项目），重新计算所有
    指标，评估指标对单个项目的依赖程度。
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
    ) -> None:
        self.confidence_level = confidence_level
        self.alpha = 1.0 - confidence_level
        logger.info("CrossValidationIndex initialized: alpha=%.3f", self.alpha)

    def _compute_metric(
        self,
        coupling_matrix: np.ndarray,
        metric: str,
    ) -> float:
        """计算指定指标."""
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        if N == 0:
            return 0.0

        if metric == "emergence_index":
            frob_norm = np.trace(C.T @ C) / (N * N)
            det_C = np.linalg.det(C + np.eye(N) * 1e-6)
            det_contrib = np.abs(det_C) ** (1.0 / N) if N > 0 else 0.0
            return float(frob_norm + PHI_GOLDEN * 0.1 * det_contrib)

        elif metric == "coherence":
            # Average absolute coupling strength
            return float(np.mean(np.abs(C)))

        elif metric == "spectral_radius":
            eigenvalues = np.linalg.eigvals(C)
            return float(np.max(np.abs(eigenvalues)))

        elif metric == "trace_normalized":
            return float(np.trace(C) / N)

        elif metric == "network_density":
            nonzero = np.count_nonzero(np.abs(C) > 1e-6)
            return float(nonzero / (N * N))

        elif metric == "clustering_coefficient":
            # Approximate clustering for weighted directed graph
            C_sym = (C + C.T) / 2.0
            triads = 0.0
            count = 0
            for i in range(N):
                for j in range(i + 1, N):
                    for k in range(j + 1, N):
                        triads += (C_sym[i, j] * C_sym[j, k] * C_sym[k, i]) ** (1.0 / 3.0)
                        count += 1
            return float(triads / count) if count > 0 else 0.0

        else:
            raise ValueError(f"Unknown metric: {metric}")

    def validate_metric(
        self,
        coupling_matrix: np.ndarray,
        metric: str,
    ) -> JackknifeResult:
        """
        对单个指标进行Jackknife交叉验证.

        每次移除一个模块（行和列），重新计算指标.
        """
        C = np.asarray(coupling_matrix, dtype=float)
        N = C.shape[0]
        theta_full = self._compute_metric(C, metric)

        # Leave-one-out estimates
        thetas = np.zeros(N)
        for i in range(N):
            mask = np.arange(N) != i
            C_loo = C[np.ix_(mask, mask)]
            thetas[i] = self._compute_metric(C_loo, metric)

        # Pseudo-values (Quenouille 1956)
        pseudovalues = N * theta_full - (N - 1) * thetas
        jack_estimate = float(np.mean(pseudovalues))
        jack_variance = float(np.var(pseudovalues, ddof=1) / N)
        jack_se = math.sqrt(jack_variance)

        # Normal approximation CI
        z = float(_normal_ppf(np.array([1.0 - self.alpha / 2.0]))[0])
        ci_lo = jack_estimate - z * jack_se
        ci_hi = jack_estimate + z * jack_se

        # Influence scores: how much each item affects the estimate
        influence = np.abs(thetas - theta_full)
        most_influential = int(np.argmax(influence))
        least_influential = int(np.argmin(influence))

        result = JackknifeResult(
            metric_name=metric,
            full_estimate=theta_full,
            jackknife_estimate=jack_estimate,
            jackknife_variance=jack_variance,
            jackknife_se=jack_se,
            ci_normal=(ci_lo, ci_hi),
            leave_one_out_estimates=thetas,
            influence_scores=influence,
            most_influential_item=most_influential,
            least_influential_item=least_influential,
        )

        logger.info(
            "Jackknife %s: full=%.4f, jack=%.4f, SE=%.4f, CI=[%.4f, %.4f], "
            "most_influential=module_%d",
            metric, theta_full, jack_estimate, jack_se, ci_lo, ci_hi,
            most_influential,
        )
        return result

    def validate_all(
        self,
        coupling_matrix: np.ndarray,
        metrics: Optional[List[str]] = None,
    ) -> CrossValidationReport:
        """
        对所有指标进行交叉验证.

        Parameters
        ----------
        coupling_matrix : ndarray
            N×N耦合矩阵
        metrics : list of str, optional
            要验证的指标列表，默认所有内置指标
        """
        if metrics is None:
            metrics = [
                "emergence_index",
                "coherence",
                "spectral_radius",
                "trace_normalized",
                "network_density",
                "clustering_coefficient",
            ]

        results: List[JackknifeResult] = []
        ci_widths: List[float] = []

        for metric in metrics:
            result = self.validate_metric(coupling_matrix, metric)
            results.append(result)
            if result.jackknife_estimate != 0:
                rel_width = (result.ci_normal[1] - result.ci_normal[0]) / abs(result.jackknife_estimate)
                ci_widths.append(rel_width)

        stability = float(np.mean(ci_widths)) if ci_widths else 1.0
        if stability < 0.1:
            rating = "low"
        elif stability < 0.3:
            rating = "moderate"
        else:
            rating = "high"

        return CrossValidationReport(
            jackknife_results=results,
            stability_score=stability,
            dependency_rating=rating,
        )


# =============================================================================
# Section 4: HypothesisTestSuite
# =============================================================================


@dataclass
class TestResult:
    """假设检验结果容器"""
    test_name: str
    statistic: float
    p_value: float
    null_hypothesis: str
    alternative_hypothesis: str
    significant: bool
    alpha: float
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "test_name": self.test_name,
            "statistic": float(self.statistic),
            "p_value": float(self.p_value),
            "null_hypothesis": self.null_hypothesis,
            "alternative_hypothesis": self.alternative_hypothesis,
            "significant": bool(self.significant),
            "alpha": self.alpha,
        }
        if self.effect_size is not None:
            d["effect_size"] = float(self.effect_size)
        if self.confidence_interval is not None:
            d["confidence_interval"] = [
                float(self.confidence_interval[0]),
                float(self.confidence_interval[1]),
            ]
        d.update(self.additional_info)
        return d


@dataclass
class PowerAnalysisResult:
    """功效分析结果"""
    effect_size: float
    alpha: float
    desired_power: float
    required_sample_size: int
    actual_power: float
    method: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "effect_size": float(self.effect_size),
            "alpha": self.alpha,
            "desired_power": self.desired_power,
            "required_sample_size": self.required_sample_size,
            "actual_power": float(self.actual_power),
            "method": self.method,
        }


class HypothesisTestSuite:
    """
    假设检验套件.

    纯numpy实现：
    - Welch's t-test: 比较两个版本的指标差异
    - KS-test: 检验指标分布是否显著变化
    - Binomial test: 模块激活率是否达到阈值
    - Power analysis: 给定效应量计算所需样本量
    """

    def __init__(self, alpha: float = 0.05) -> None:
        self.alpha = alpha
        logger.info("HypothesisTestSuite initialized: alpha=%.3f", alpha)

    def welch_t_test(
        self,
        sample1: np.ndarray,
        sample2: np.ndarray,
        alternative: str = "two-sided",
        name1: str = "group_1",
        name2: str = "group_2",
    ) -> TestResult:
        """
        Welch's t-test (不等方差t检验).

        H0: mu_1 = mu_2
        """
        t_stat, p_value = _welch_t_test(sample1, sample2, alternative)

        # Cohen's d effect size (pooled standard deviation)
        x1 = np.asarray(sample1, dtype=float)
        x2 = np.asarray(sample2, dtype=float)
        pooled_std = np.sqrt((np.var(x1, ddof=1) + np.var(x2, ddof=1)) / 2.0)
        cohen_d = (np.mean(x1) - np.mean(x2)) / pooled_std if pooled_std > 0 else 0.0

        # CI for difference in means
        se_diff = np.sqrt(np.var(x1, ddof=1) / len(x1) + np.var(x2, ddof=1) / len(x2))
        df = (np.var(x1, ddof=1) / len(x1) + np.var(x2, ddof=1) / len(x2)) ** 2 / (
            (np.var(x1, ddof=1) / len(x1)) ** 2 / (len(x1) - 1)
            + (np.var(x2, ddof=1) / len(x2)) ** 2 / (len(x2) - 1)
        )
        z = float(_normal_ppf(np.array([1.0 - self.alpha / 2.0]))[0])
        diff = np.mean(x1) - np.mean(x2)
        ci = (float(diff - z * se_diff), float(diff + z * se_diff))

        return TestResult(
            test_name=f"welch_t_test({name1}_vs_{name2})",
            statistic=t_stat,
            p_value=p_value,
            null_hypothesis=f"mean({name1}) = mean({name2})",
            alternative_hypothesis=f"mean({name1}) {self._alt_symbol(alternative)} mean({name2})",
            significant=p_value < self.alpha,
            alpha=self.alpha,
            effect_size=float(cohen_d),
            confidence_interval=ci,
            additional_info={
                "mean_1": float(np.mean(x1)),
                "mean_2": float(np.mean(x2)),
                "std_1": float(np.std(x1, ddof=1)),
                "std_2": float(np.std(x2, ddof=1)),
                "n_1": len(x1),
                "n_2": len(x2),
                "df": float(df),
            },
        )

    def ks_test(
        self,
        sample1: np.ndarray,
        sample2: np.ndarray,
        name1: str = "group_1",
        name2: str = "group_2",
    ) -> TestResult:
        """
        双样本Kolmogorov-Smirnov检验.

        H0: 两个样本来自同一连续分布.
        """
        d_stat, p_value = _ks_2sample_test(sample1, sample2)

        return TestResult(
            test_name=f"ks_test({name1}_vs_{name2})",
            statistic=d_stat,
            p_value=p_value,
            null_hypothesis=f"{name1} and {name2} come from the same distribution",
            alternative_hypothesis=f"{name1} and {name2} come from different distributions",
            significant=p_value < self.alpha,
            alpha=self.alpha,
            additional_info={
                "n_1": len(sample1),
                "n_2": len(sample2),
                "kolmogorov_distance": d_stat,
            },
        )

    def binomial_test(
        self,
        k_success: int,
        n_trials: int,
        p_null: float = 0.5,
        alternative: str = "greater",
        description: str = "activation_rate",
    ) -> TestResult:
        """
        精确二项检验.

        H0: p = p_null
        """
        p_value = _binom_test(k_success, n_trials, p_null, alternative)
        obs_rate = k_success / n_trials if n_trials > 0 else 0.0

        # 95% CI for proportion (Wilson score interval)
        z = float(_normal_ppf(np.array([0.975]))[0])
        p_hat = obs_rate
        n = n_trials
        denominator = 1.0 + z * z / n
        centre = (p_hat + z * z / (2.0 * n)) / denominator
        width = z * np.sqrt((p_hat * (1.0 - p_hat) + z * z / (4.0 * n)) / n) / denominator
        ci = (float(max(0.0, centre - width)), float(min(1.0, centre + width)))

        return TestResult(
            test_name=f"binomial_test({description})",
            statistic=obs_rate,
            p_value=p_value,
            null_hypothesis=f"p = {p_null}",
            alternative_hypothesis=f"p {self._alt_symbol(alternative)} {p_null}",
            significant=p_value < self.alpha,
            alpha=self.alpha,
            effect_size=obs_rate - p_null,
            confidence_interval=ci,
            additional_info={
                "k_success": k_success,
                "n_trials": n_trials,
                "observed_rate": obs_rate,
                "expected_rate": p_null,
            },
        )

    def power_analysis(
        self,
        effect_size: float,
        alpha: float = 0.05,
        power: float = 0.80,
        ratio: float = 1.0,
    ) -> PowerAnalysisResult:
        """
        功效分析：给定效应量，计算两独立样本t检验所需样本量.

        使用正态近似公式:
        n = ((z_α/2 + z_β) / d)^2 * (1 + 1/ratio)

        其中d为Cohen's d效应量.
        """
        n1 = _power_analysis_ttest(effect_size, alpha, power, ratio)
        n2 = int(np.ceil(n1 * ratio))

        # Verify actual power with computed sample size
        z_alpha = float(_normal_ppf(np.array([1.0 - alpha / 2.0]))[0])
        z_beta = float(_normal_ppf(np.array([power]))[0])
        actual_power = float(_normal_cdf(
            np.array([z_alpha + effect_size * np.sqrt(n1 * n2 / (n1 + n2))])
        )[0])

        return PowerAnalysisResult(
            effect_size=effect_size,
            alpha=alpha,
            desired_power=power,
            required_sample_size=n1 + n2,
            actual_power=actual_power,
            method="normal_approximation_welch_ttest",
        )

    def _alt_symbol(self, alternative: str) -> str:
        mapping = {
            "two-sided": "!=",
            "less": "<",
            "greater": ">",
        }
        return mapping.get(alternative, "!=")


# =============================================================================
# Section 5: ValidationReport
# =============================================================================


@dataclass
class ValidationReport:
    """
    综合验证报告生成器.

    汇总所有验证结果，输出JSON和Markdown格式。
    """

    report_title: str = "OMNI-HUB v11 Statistical Validation Report"
    timestamp: float = field(default_factory=time.time)
    bootstrap_result: Optional[BootstrapResult] = None
    monte_carlo_report: Optional[MonteCarloStabilityReport] = None
    cross_validation_report: Optional[CrossValidationReport] = None
    hypothesis_results: List[TestResult] = field(default_factory=list)
    power_analysis_results: List[PowerAnalysisResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_title": self.report_title,
            "timestamp": self.timestamp,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp)),
            "bootstrap": self.bootstrap_result.to_dict() if self.bootstrap_result else None,
            "monte_carlo": self.monte_carlo_report.to_dict() if self.monte_carlo_report else None,
            "cross_validation": self.cross_validation_report.to_dict() if self.cross_validation_report else None,
            "hypothesis_tests": [t.to_dict() for t in self.hypothesis_results],
            "power_analysis": [p.to_dict() for p in self.power_analysis_results],
            "metadata": self.metadata,
            "summary": self._generate_summary(),
        }

    def to_json(self, indent: int = 2) -> str:
        """生成JSON格式报告."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """生成Markdown格式报告."""
        lines: List[str] = []
        lines.append(f"# {self.report_title}")
        lines.append("")
        lines.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}")
        lines.append("")

        # Summary
        summary = self._generate_summary()
        lines.append("## Summary")
        lines.append("")
        for key, value in summary.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

        # Bootstrap
        if self.bootstrap_result:
            lines.append("## 1. Bootstrap Validation (BCa)")
            lines.append("")
            r = self.bootstrap_result
            lines.append(f"- **Metric:** {r.metric_name}")
            lines.append(f"- **Point Estimate:** `{r.point_estimate:.6f}`")
            lines.append(f"- **95% Percentile CI:** `[{r.ci_percentile[0]:.6f}, {r.ci_percentile[1]:.6f}]`")
            lines.append(f"- **95% BCa CI:** `[{r.ci_bca[0]:.6f}, {r.ci_bca[1]:.6f}]`")
            lines.append(f"- **Standard Error:** `{r.standard_error:.6f}`")
            lines.append(f"- **Bias:** `{r.bias:.6f}`")
            lines.append(f"- **Acceleration (a):** `{r.acceleration:.6f}`")
            lines.append(f"- **Bias Correction (z0):** `{r.bias_correction:.6f}`")
            lines.append(f"- **Bootstrap Samples:** {r.n_bootstrap}")
            lines.append("")

        # Monte Carlo
        if self.monte_carlo_report:
            lines.append("## 2. Monte Carlo Stability Analysis")
            lines.append("")
            lines.append(f"- **Overall Stable:** {'Yes' if self.monte_carlo_report.overall_stable else 'No'}")
            if self.monte_carlo_report.critical_noise_level is not None:
                lines.append(f"- **Critical Noise Level:** `{self.monte_carlo_report.critical_noise_level:.2f}`")
            lines.append(f"- **Noise-CV Correlation:** `{self.monte_carlo_report.correlation_with_noise:.4f}`")
            lines.append("")
            lines.append("| Noise Level | Mean E | Std E | CV (%) | Stable |")
            lines.append("|------------|--------|-------|--------|--------|")
            for r in self.monte_carlo_report.results:
                lines.append(
                    f"| {r.noise_level:.2f} | {r.mean_E:.6f} | {r.std_E:.6f} | "
                    f"{r.cv_E * 100:.2f}% | {'Yes' if r.is_stable else 'No'} |"
                )
            lines.append("")

        # Cross Validation
        if self.cross_validation_report:
            lines.append("## 3. Cross-Validation (Jackknife)")
            lines.append("")
            lines.append(f"- **Stability Score:** `{self.cross_validation_report.stability_score:.4f}`")
            lines.append(f"- **Dependency Rating:** `{self.cross_validation_report.dependency_rating}`")
            lines.append("")
            lines.append("| Metric | Full Est. | Jackknife | SE | 95% CI | Most Influential |")
            lines.append("|--------|-----------|-----------|-----|--------|------------------|")
            for r in self.cross_validation_report.jackknife_results:
                ci_str = f"[{r.ci_normal[0]:.4f}, {r.ci_normal[1]:.4f}]"
                lines.append(
                    f"| {r.metric_name} | {r.full_estimate:.4f} | {r.jackknife_estimate:.4f} | "
                    f"{r.jackknife_se:.4f} | {ci_str} | Module {r.most_influential_item} |"
                )
            lines.append("")

        # Hypothesis Tests
        if self.hypothesis_results:
            lines.append("## 4. Hypothesis Tests")
            lines.append("")
            lines.append("| Test | Statistic | p-value | Significant | Effect Size |")
            lines.append("|------|-----------|---------|-------------|-------------|")
            for t in self.hypothesis_results:
                sig = "**Yes**" if t.significant else "No"
                es = f"{t.effect_size:.4f}" if t.effect_size is not None else "N/A"
                lines.append(
                    f"| {t.test_name} | {t.statistic:.4f} | {t.p_value:.6f} | {sig} | {es} |"
                )
            lines.append("")

        # Power Analysis
        if self.power_analysis_results:
            lines.append("## 5. Power Analysis")
            lines.append("")
            lines.append("| Effect Size | Alpha | Target Power | Required N | Actual Power | Method |")
            lines.append("|-------------|-------|--------------|------------|--------------|--------|")
            for p in self.power_analysis_results:
                lines.append(
                    f"| {p.effect_size:.4f} | {p.alpha:.3f} | {p.desired_power:.2f} | "
                    f"{p.required_sample_size} | {p.actual_power:.4f} | {p.method} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("*Report generated by OMNI-HUB v11 Statistical Validation Framework*")
        lines.append("*All statistical computations use pure numpy implementations*")

        return "\n".join(lines)

    def save(self, output_dir: str = "/mnt/agents/output/OMNI-HUB/reports") -> Dict[str, str]:
        """保存报告到JSON和Markdown文件."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        timestamp_str = time.strftime("%Y%m%d_%H%M%S", time.localtime(self.timestamp))
        json_file = out_path / f"validation_report_{timestamp_str}.json"
        md_file = out_path / f"validation_report_{timestamp_str}.md"

        json_file.write_text(self.to_json(), encoding="utf-8")
        md_file.write_text(self.to_markdown(), encoding="utf-8")

        logger.info("Validation report saved: %s, %s", json_file, md_file)
        return {
            "json_path": str(json_file),
            "markdown_path": str(md_file),
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要统计."""
        summary: Dict[str, Any] = {}

        if self.bootstrap_result:
            r = self.bootstrap_result
            ci_width = r.ci_bca[1] - r.ci_bca[0]
            summary["bootstrap_E_estimate"] = round(r.point_estimate, 6)
            summary["bootstrap_E_ci_width"] = round(ci_width, 6)
            summary["bootstrap_E_relative_precision"] = round(
                ci_width / r.point_estimate if r.point_estimate != 0 else float("inf"), 4
            )

        if self.monte_carlo_report:
            summary["monte_carlo_stable"] = self.monte_carlo_report.overall_stable
            summary["monte_carlo_critical_noise"] = self.monte_carlo_report.critical_noise_level

        if self.cross_validation_report:
            summary["cv_dependency_rating"] = self.cross_validation_report.dependency_rating

        n_sig = sum(1 for t in self.hypothesis_results if t.significant)
        summary["hypothesis_tests_total"] = len(self.hypothesis_results)
        summary["hypothesis_tests_significant"] = n_sig

        return summary


# =============================================================================
# Section 6: Main Integration Runner
# =============================================================================


class StatisticalValidationRunner:
    """
    统计验证统一运行器.

    协调所有验证器，生成综合报告.
    """

    def __init__(
        self,
        n_bootstrap: int = 1000,
        n_monte_carlo: int = 1000,
        alpha: float = 0.05,
        rng_seed: int = 42,
    ) -> None:
        self.rng = np.random.default_rng(rng_seed)
        self.bootstrap_validator = BootstrapValidator(
            n_bootstrap=n_bootstrap, rng=self.rng,
        )
        self.monte_carlo = MonteCarloStability(
            n_trials=n_monte_carlo, rng=self.rng,
        )
        self.cross_validation = CrossValidationIndex()
        self.hypothesis_suite = HypothesisTestSuite(alpha=alpha)
        logger.info("StatisticalValidationRunner initialized with seed=%d", rng_seed)

    def run_full_validation(
        self,
        coupling_matrix: np.ndarray,
        coupling_matrix_v2: Optional[np.ndarray] = None,
    ) -> ValidationReport:
        """
        执行完整统计验证流程.

        Parameters
        ----------
        coupling_matrix : ndarray
            当前版本的N×N耦合矩阵
        coupling_matrix_v2 : ndarray, optional
            对比版本的N×N耦合矩阵（用于假设检验）
        """
        C = np.asarray(coupling_matrix, dtype=float)
        report = ValidationReport(
            metadata={
                "matrix_shape": list(C.shape),
                "n_modules": C.shape[0],
                "rng_seed": 42,
            }
        )

        # 1. Bootstrap validation
        logger.info("=" * 60)
        logger.info("STEP 1: Bootstrap Validation")
        logger.info("=" * 60)
        report.bootstrap_result = self.bootstrap_validator.validate(C)

        # 2. Monte Carlo stability
        logger.info("=" * 60)
        logger.info("STEP 2: Monte Carlo Stability Analysis")
        logger.info("=" * 60)
        report.monte_carlo_report = self.monte_carlo.test_stability(C)

        # 3. Cross-validation
        logger.info("=" * 60)
        logger.info("STEP 3: Cross-Validation (Jackknife)")
        logger.info("=" * 60)
        report.cross_validation_report = self.cross_validation.validate_all(C)

        # 4. Hypothesis tests
        logger.info("=" * 60)
        logger.info("STEP 4: Hypothesis Tests")
        logger.info("=" * 60)

        # Binomial test: activation rate
        active_count = int(np.sum(np.sum(C, axis=1) > 0.5))
        n_modules = C.shape[0]
        binom_result = self.hypothesis_suite.binomial_test(
            k_success=active_count,
            n_trials=n_modules,
            p_null=0.5,
            alternative="greater",
            description="module_activation_rate",
        )
        report.hypothesis_results.append(binom_result)

        # If v2 matrix provided, compare versions
        if coupling_matrix_v2 is not None:
            C2 = np.asarray(coupling_matrix_v2, dtype=float)
            # Flatten for distribution comparison
            flat1 = C.flatten()
            flat2 = C2.flatten()

            # Welch t-test
            t_result = self.hypothesis_suite.welch_t_test(
                flat1, flat2,
                name1="version_1", name2="version_2",
            )
            report.hypothesis_results.append(t_result)

            # KS test
            ks_result = self.hypothesis_suite.ks_test(
                flat1, flat2,
                name1="version_1", name2="version_2",
            )
            report.hypothesis_results.append(ks_result)

        # 5. Power analysis
        logger.info("=" * 60)
        logger.info("STEP 5: Power Analysis")
        logger.info("=" * 60)
        for effect_size in [0.2, 0.5, 0.8]:
            pa = self.hypothesis_suite.power_analysis(
                effect_size=effect_size,
                alpha=0.05,
                power=0.80,
            )
            report.power_analysis_results.append(pa)
            logger.info(
                "Effect size %.1f: required N = %d", effect_size, pa.required_sample_size
            )

        return report


# =============================================================================
# Section 7: __main__ — Test with simulated 46-module coupling matrix
# =============================================================================


def _generate_simulated_coupling_matrix(
    n_modules: int = 46,
    rng: Optional[Generator] = None,
    structured: bool = True,
) -> np.ndarray:
    """
    生成模拟N×N耦合矩阵.

    Parameters
    ----------
    n_modules : int
        模块数量（默认46）
    rng : Generator, optional
        随机数生成器
    structured : bool
        如果为True，生成具有社区结构的矩阵；否则完全随机

    Returns
    -------
    C : ndarray, shape (n_modules, n_modules)
        对称耦合矩阵（无向图）
    """
    rng = rng or np.random.default_rng(42)
    C = np.zeros((n_modules, n_modules), dtype=float)

    if structured:
        # Create community structure: 3 communities
        comm_sizes = [15, 16, 15]
        start = 0
        intra_strength = 0.4
        inter_strength = 0.1

        for size in comm_sizes:
            end = start + size
            # Intra-community coupling (strong)
            block = rng.random((size, size)) * intra_strength
            C[start:end, start:end] = block
            start = end

        # Inter-community coupling (weak)
        for i in range(n_modules):
            for j in range(i + 1, n_modules):
                if C[i, j] == 0:
                    if rng.random() < 0.3:
                        C[i, j] = rng.random() * inter_strength
                    C[j, i] = C[i, j]
    else:
        # Random sparse coupling
        for i in range(n_modules):
            for j in range(i + 1, n_modules):
                if rng.random() < 0.4:
                    C[i, j] = rng.random() * 0.5
                    C[j, i] = C[i, j]

    # Ensure diagonal is non-zero (self-coupling)
    np.fill_diagonal(C, rng.random(n_modules) * 0.3 + 0.1)

    # Make symmetric
    C = (C + C.T) / 2.0

    return C


def main() -> None:
    """主测试入口."""
    print("=" * 70)
    print("OMNI-HUB v11.0 — Statistical Validation Framework")
    print("=" * 70)
    print()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )

    rng = np.random.default_rng(42)

    # Generate simulated 46×46 coupling matrices
    print("[1/7] Generating simulated 46-module coupling matrices...")
    C_v1 = _generate_simulated_coupling_matrix(n_modules=46, rng=rng, structured=True)
    C_v2 = _generate_simulated_coupling_matrix(n_modules=46, rng=rng, structured=False)
    print(f"      Matrix v1 shape: {C_v1.shape}, non-zero: {np.count_nonzero(C_v1)}")
    print(f"      Matrix v2 shape: {C_v2.shape}, non-zero: {np.count_nonzero(C_v2)}")
    print()

    # Initialize runner
    print("[2/7] Initializing StatisticalValidationRunner...")
    runner = StatisticalValidationRunner(
        n_bootstrap=1000,
        n_monte_carlo=1000,
        alpha=0.05,
        rng_seed=42,
    )
    print("      Runner initialized.")
    print()

    # Run full validation
    print("[3/7] Running full statistical validation pipeline...")
    print()
    report = runner.run_full_validation(C_v1, C_v2)
    print()

    # Display key results
    print("=" * 70)
    print("VALIDATION RESULTS SUMMARY")
    print("=" * 70)
    print()

    # Bootstrap
    if report.bootstrap_result:
        r = report.bootstrap_result
        print(f"[Bootstrap — {r.metric_name}]")
        print(f"  Point Estimate:       {r.point_estimate:.6f}")
        print(f"  95% Percentile CI:    [{r.ci_percentile[0]:.6f}, {r.ci_percentile[1]:.6f}]")
        print(f"  95% BCa CI:           [{r.ci_bca[0]:.6f}, {r.ci_bca[1]:.6f}]")
        print(f"  Standard Error:       {r.standard_error:.6f}")
        print(f"  Bias:                 {r.bias:.6f}")
        print(f"  Acceleration (a):     {r.acceleration:.6f}")
        print(f"  Bias Correction (z0): {r.bias_correction:.6f}")
        print()

    # Monte Carlo
    if report.monte_carlo_report:
        print("[Monte Carlo Stability]")
        print(f"  Overall Stable:       {report.monte_carlo_report.overall_stable}")
        print(f"  Critical Noise:       {report.monte_carlo_report.critical_noise_level}")
        print(f"  Noise-CV Correlation: {report.monte_carlo_report.correlation_with_noise:.4f}")
        for res in report.monte_carlo_report.results:
            status = "STABLE" if res.is_stable else "UNSTABLE"
            print(f"  Noise={res.noise_level:.2f}: mean={res.mean_E:.4f}, "
                  f"std={res.std_E:.4f}, CV={res.cv_E * 100:.2f}% [{status}]")
        print()

    # Cross-validation
    if report.cross_validation_report:
        print("[Cross-Validation (Jackknife)]")
        print(f"  Stability Score:      {report.cross_validation_report.stability_score:.4f}")
        print(f"  Dependency Rating:    {report.cross_validation_report.dependency_rating}")
        for r in report.cross_validation_report.jackknife_results[:3]:
            print(f"  {r.metric_name:24s}: full={r.full_estimate:.4f}, "
                  f"jack={r.jackknife_estimate:.4f}, SE={r.jackknife_se:.4f}, "
                  f"CI=[{r.ci_normal[0]:.4f}, {r.ci_normal[1]:.4f}]")
        print()

    # Hypothesis tests
    if report.hypothesis_results:
        print("[Hypothesis Tests]")
        for t in report.hypothesis_results:
            sig = "SIGNIFICANT" if t.significant else "not significant"
            print(f"  {t.test_name:40s}: stat={t.statistic:.4f}, p={t.p_value:.6f} [{sig}]")
        print()

    # Power analysis
    if report.power_analysis_results:
        print("[Power Analysis]")
        for p in report.power_analysis_results:
            print(f"  Effect size={p.effect_size:.1f}: required N={p.required_sample_size}, "
                  f"actual power={p.actual_power:.4f}")
        print()

    # Save report
    print("[4/7] Saving validation report...")
    paths = report.save()
    print(f"      JSON:  {paths['json_path']}")
    print(f"      MD:    {paths['markdown_path']}")
    print()

    # Print markdown summary
    print("[5/7] Markdown report preview (first 30 lines):")
    md_lines = report.to_markdown().split("\n")
    for line in md_lines[:30]:
        print(f"      {line}")
    print("      ...")
    print()

    # Statistics
    print("=" * 70)
    print("FRAMEWORK STATISTICS")
    print("=" * 70)

    # Count lines
    import inspect
    source_lines = inspect.getsourcelines(sys.modules[__name__])[0]
    n_lines = len(source_lines)

    n_classes = sum(
        1 for name, obj in globals().items()
        if inspect.isclass(obj) and not name.startswith("_")
    )
    n_methods = sum(
        len([m for m in inspect.getmembers(obj, inspect.isfunction) if not m[0].startswith("_")])
        for name, obj in globals().items()
        if inspect.isclass(obj) and not name.startswith("_")
    )
    n_functions = sum(
        1 for name, obj in globals().items()
        if inspect.isfunction(obj) and name.startswith("_")
    )

    print(f"  Total code lines:        {n_lines}")
    print(f"  Public classes:          {n_classes}")
    print(f"  Public methods:          {n_methods}")
    print(f"  Internal functions:      {n_functions}")
    print(f"  Statistical methods:     Bootstrap(BCa), MonteCarlo(Halton), "
          f"Jackknife, Welch-t, KS-test, Binomial, PowerAnalysis")
    print()
    print("All tests completed successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
