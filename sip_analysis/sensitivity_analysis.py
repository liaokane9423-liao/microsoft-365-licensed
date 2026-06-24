"""
敏感度分析模組 - 評估各參數不確定性對 CP 值排名的影響
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from cp_analysis import calc_cp
from precursor_data import (
    SECONDARY_FORMATION_FACTORS,
    ABATEMENT_COSTS_NTD,
    PRECURSOR_LABELS,
)

PRECURSORS = ["NOx", "SO2", "NH3", "VOC", "PM25_primary"]
SOURCE_TYPES = ["stationary", "mobile", "area"]


def monte_carlo_cp(n_samples: int = 10_000, source_type: str = "stationary", seed: int = 42):
    """
    Monte Carlo 不確定性分析
    在 ff 和 cost 的 [low, high] 區間均勻抽樣，估計 CP 值分佈
    """
    import random
    random.seed(seed)

    cp_samples: dict[str, list[float]] = {p: [] for p in PRECURSORS}

    for _ in range(n_samples):
        for p in PRECURSORS:
            ff_low  = SECONDARY_FORMATION_FACTORS[p]["low"]
            ff_high = SECONDARY_FORMATION_FACTORS[p]["high"]
            ff = random.uniform(ff_low, ff_high)

            cost_data = ABATEMENT_COSTS_NTD[p][source_type]
            cost = random.uniform(cost_data["low"], cost_data["high"])

            cp_samples[p].append(calc_cp(ff, cost))

    return cp_samples


def rank_frequency(cp_samples: dict, n_top: int = 2) -> dict:
    """計算各前驅物排名第 1、第 2 的頻率"""
    n = len(next(iter(cp_samples.values())))
    freq: dict[str, dict[int, int]] = {p: {i: 0 for i in range(1, n_top + 2)} for p in cp_samples}

    for i in range(n):
        ranked = sorted(cp_samples.keys(), key=lambda p: cp_samples[p][i], reverse=True)
        for rank_idx, p in enumerate(ranked[:n_top + 1], start=1):
            if rank_idx in freq[p]:
                freq[p][rank_idx] += 1

    return {p: {r: c / n for r, c in ranks.items()} for p, ranks in freq.items()}


def percentile(data: list, pct: float) -> float:
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * pct / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def run_sensitivity(source_type: str = "stationary"):
    print(f"\n{'─'*70}")
    print(f"  Monte Carlo 敏感度分析 — {source_type} 排放源")
    print(f"{'─'*70}")

    samples = monte_carlo_cp(n_samples=20_000, source_type=source_type)

    print(f"\n  {'前驅物':<22} {'P5':>8} {'P50(中位)':>12} {'P95':>8} {'均值':>8}")
    print(f"  {'':22} {'(kg/百萬$)':>8} {'(kg/百萬$)':>12} {'(kg/百萬$)':>8}")
    print(f"  {'─'*62}")

    stats = {}
    for p in PRECURSORS:
        data = samples[p]
        p5  = percentile(data, 5)
        p50 = percentile(data, 50)
        p95 = percentile(data, 95)
        avg = sum(data) / len(data)
        stats[p] = {"p50": p50, "mean": avg}
        label = PRECURSOR_LABELS.get(p, p)
        print(f"  {label:<22} {p5:>8.1f} {p50:>12.1f} {p95:>8.1f} {avg:>8.1f}")

    freq = rank_frequency(samples)
    print(f"\n  各前驅物於 Monte Carlo 模擬中奪得 CP 第 1 名的機率：")
    ranked_by_prob = sorted(PRECURSORS, key=lambda p: freq[p].get(1, 0), reverse=True)
    for p in ranked_by_prob:
        label = PRECURSOR_LABELS.get(p, p)
        prob1 = freq[p].get(1, 0) * 100
        prob2 = freq[p].get(2, 0) * 100
        print(f"   {label:<22}  P(rank=1): {prob1:>5.1f}%   P(rank=2): {prob2:>5.1f}%")

    print()


def run_all():
    print("\n" + "=" * 70)
    print("  SIP 前驅物 CP 值 — 不確定性 / 敏感度分析")
    print("=" * 70)
    for source in SOURCE_TYPES:
        run_sensitivity(source)


if __name__ == "__main__":
    run_all()
