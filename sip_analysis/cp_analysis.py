"""
SIP 政策前驅物 CP 值核心計算模組

CP 值定義：每 NT$ 百萬元減量成本，可減少的 PM2.5 等量排放量 (公噸)
CP = (形成因子 × 減量量) / 成本 = kg PM2.5 減量 / NT$
或以健康效益表達：健康貨幣效益 / 減量成本
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from precursor_data import (
    SECONDARY_FORMATION_FACTORS,
    ABATEMENT_COSTS_NTD,
    HEALTH_BENEFIT_PER_UG_M3,
    PRECURSOR_LABELS,
)


@dataclass
class CPResult:
    precursor: str
    source_type: str
    formation_factor: float          # kg PM2.5 / kg 前驅物
    abatement_cost_ntd_per_ton: float
    cp_kg_pm25_per_million_ntd: float  # 主要 CP 值
    cp_low: float
    cp_high: float
    benefit_cost_ratio: float          # 健康效益 / 減量成本
    tech: str
    rank: int = 0


def calc_cp(
    formation_factor: float,
    cost_ntd_per_ton: float,
) -> float:
    """
    CP 值：每投入 NT$ 百萬元，可削減的 PM2.5 等量公噸數
    formation_factor: kg PM2.5 / kg 前驅物
    cost_ntd_per_ton: NT$ / 公噸前驅物
    return: kg PM2.5 / NT$百萬  (= 公噸 PM2.5 / NT$百萬)
    """
    if cost_ntd_per_ton == 0:
        return 0.0
    # 1 公噸前驅物 → formation_factor * 1000 g → formation_factor kg PM2.5
    # 成本 cost_ntd_per_ton NT$
    # CP = (formation_factor kg PM2.5) / cost_ntd_per_ton * 1_000_000
    return (formation_factor * 1_000_000) / cost_ntd_per_ton  # kg PM2.5 / 百萬NT$


def calc_benefit_cost_ratio(
    cp_value: float,
    population_m: float = 23.0,
    mix_height_m: float = 800.0,
    domain_km2: float = 36_000.0,
) -> float:
    """
    粗估效益成本比 (BCR)
    用大氣稀釋假設將 PM2.5 削減量轉為濃度降幅，再乘健康效益值
    cp_value: kg PM2.5 / 百萬 NT$
    回傳：NT$ 健康效益 / NT$ 成本 (BCR)
    """
    # 1 kg PM2.5 散布於 domain 空氣柱中的濃度降幅 (μg/m³ 年均)
    domain_m3 = domain_km2 * 1e6 * mix_height_m  # m³ (36,000 km² × 800 m)
    # 假設均勻混合（保守估計）
    delta_conc_per_kg = 1e9 / domain_m3  # μg/m³ per kg PM2.5

    # 每百萬 NT$ 投入的健康效益
    health_benefit_per_million = (
        cp_value                             # kg PM2.5 減量
        * delta_conc_per_kg                  # → μg/m³ 降低
        * HEALTH_BENEFIT_PER_UG_M3["value_nt$_per_ug_m3_per_year"]
    )

    bcr = health_benefit_per_million / 1_000_000  # 成本是 1 百萬 NT$
    return bcr


def analyze_all_precursors(
    source_type: str = "stationary",
) -> List[CPResult]:
    """
    計算所有前驅物在指定排放源類型下的 CP 值
    source_type: 'stationary' | 'mobile' | 'area'
    """
    results: List[CPResult] = []

    for precursor, ff_data in SECONDARY_FORMATION_FACTORS.items():
        if precursor not in ABATEMENT_COSTS_NTD:
            continue
        cost_data = ABATEMENT_COSTS_NTD[precursor].get(source_type)
        if cost_data is None:
            continue

        ff_mean = ff_data["mean"]
        ff_low  = ff_data["low"]
        ff_high = ff_data["high"]

        cost_mean = cost_data["mean"]
        cost_low  = cost_data["low"]
        cost_high = cost_data["high"]

        cp_mean = calc_cp(ff_mean, cost_mean)
        # 不確定性：ff 高 / cost 低 → CP 最大
        cp_high = calc_cp(ff_high, cost_low)
        # ff 低 / cost 高 → CP 最小
        cp_low  = calc_cp(ff_low,  cost_high)

        bcr = calc_benefit_cost_ratio(cp_mean)

        results.append(CPResult(
            precursor=precursor,
            source_type=source_type,
            formation_factor=ff_mean,
            abatement_cost_ntd_per_ton=cost_mean,
            cp_kg_pm25_per_million_ntd=cp_mean,
            cp_low=cp_low,
            cp_high=cp_high,
            benefit_cost_ratio=bcr,
            tech=cost_data["tech"],
        ))

    # 由高到低排名
    results.sort(key=lambda r: r.cp_kg_pm25_per_million_ntd, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    return results


def analyze_cross_source() -> Dict[str, List[CPResult]]:
    """跨排放源別分析"""
    return {
        source: analyze_all_precursors(source)
        for source in ["stationary", "mobile", "area"]
    }


def best_strategy(
    budget_million_ntd: float,
    source_type: str = "stationary",
) -> Tuple[str, float, float]:
    """
    給定 SIP 預算，找出 CP 值最高的前驅物及預期 PM2.5 減量
    return: (最佳前驅物, 可削減 PM2.5 kg, BCR)
    """
    results = analyze_all_precursors(source_type)
    best = results[0]  # 已排序
    pm25_reduced_kg = best.cp_kg_pm25_per_million_ntd * budget_million_ntd
    return best.precursor, pm25_reduced_kg, best.benefit_cost_ratio


def sip_portfolio_analysis(
    budget_million_ntd: float,
    allocation: Dict[str, float],  # {'NOx': 0.3, 'SO2': 0.4, ...}
    source_type: str = "stationary",
) -> Dict[str, float]:
    """
    多前驅物組合 SIP 策略分析
    allocation: 各前驅物預算佔比 (總和須 ≤ 1.0)
    return: {'total_pm25_kg': x, 'per_precursor': {...}, 'portfolio_cp': y}
    """
    results_by_precursor = {
        r.precursor: r for r in analyze_all_precursors(source_type)
    }

    per_precursor = {}
    total_pm25 = 0.0
    total_cost = 0.0

    for precursor, share in allocation.items():
        if precursor not in results_by_precursor:
            continue
        r = results_by_precursor[precursor]
        budget_p = budget_million_ntd * share
        pm25 = r.cp_kg_pm25_per_million_ntd * budget_p
        per_precursor[precursor] = {
            "budget_million_ntd": budget_p,
            "pm25_reduced_kg": pm25,
            "cp": r.cp_kg_pm25_per_million_ntd,
        }
        total_pm25 += pm25
        total_cost += budget_p

    portfolio_cp = total_pm25 / total_cost if total_cost > 0 else 0.0

    return {
        "total_pm25_kg": total_pm25,
        "portfolio_cp_kg_per_million": portfolio_cp,
        "per_precursor": per_precursor,
    }
