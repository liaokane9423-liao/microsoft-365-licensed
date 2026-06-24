"""
=============================================================
  SIP 空品前驅物 CP 值分析 — 執行程式
=============================================================
填好 input_data.py 後，執行：
    python run_analysis.py
=============================================================
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from input_data import (
    STUDY_REGION,
    PRECURSORS,
    PRECURSOR_PARAMS,
    HEALTH_PARAMS,
    SIP_SCENARIOS,
)


# ─────────────────────────────────────────────────────────────
# 資料驗證
# ─────────────────────────────────────────────────────────────
def validate():
    errors = []

    if not STUDY_REGION["name"]:
        errors.append("STUDY_REGION['name'] 尚未填寫")

    required_region = ["area_km2", "population", "mix_height_m",
                       "base_pm25_ug_m3", "target_pm25_ug_m3"]
    for k in required_region:
        if STUDY_REGION[k] is None:
            errors.append(f"STUDY_REGION['{k}'] 尚未填寫")

    for p in PRECURSORS:
        if p not in PRECURSOR_PARAMS:
            errors.append(f"前驅物 '{p}' 在 PRECURSOR_PARAMS 中找不到")
            continue
        params = PRECURSOR_PARAMS[p]
        for field in ["formation_factor", "emission_ton_yr",
                      "reduction_target_pct", "cost_ntd_per_ton"]:
            if params.get(field) is None:
                errors.append(f"PRECURSOR_PARAMS['{p}']['{field}'] 尚未填寫")

    if errors:
        print("\n[錯誤] 以下欄位尚未填寫，請先完成 input_data.py：\n")
        for e in errors:
            print(f"  ✗ {e}")
        print()
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# 核心計算
# ─────────────────────────────────────────────────────────────
def calc_cp(formation_factor, cost_ntd_per_ton):
    """CP 值：每投入 100 萬 NT$，可削減 PM2.5 等量 (kg)"""
    return (formation_factor * 1_000_000) / cost_ntd_per_ton


def calc_reduction_amount(p):
    """依削減目標百分比計算絕對削減量 (公噸/年)"""
    params = PRECURSOR_PARAMS[p]
    return params["emission_ton_yr"] * params["reduction_target_pct"] / 100


def calc_total_cost(p):
    """達成削減目標所需總成本 (NT$)"""
    params = PRECURSOR_PARAMS[p]
    reduction = calc_reduction_amount(p)
    return reduction * params["cost_ntd_per_ton"]


def calc_pm25_reduction(p):
    """達成削減目標可減少的 PM2.5 等量 (公噸/年)"""
    params = PRECURSOR_PARAMS[p]
    reduction = calc_reduction_amount(p)
    return reduction * params["formation_factor"]


def calc_bcr(cp_value):
    """效益成本比 BCR（若未填健康效益參數則回傳 None）"""
    required = ["benefit_per_ug_m3_ntd", "area_km2", "mix_height_m"]
    if any(HEALTH_PARAMS.get("benefit_per_ug_m3_ntd") is None
           for k in required):
        return None
    if HEALTH_PARAMS["benefit_per_ug_m3_ntd"] is None:
        return None

    domain_m3 = (STUDY_REGION["area_km2"] * 1e6
                 * STUDY_REGION["mix_height_m"])
    delta_conc_per_kg = 1e9 / domain_m3          # μg/m³ per kg PM2.5
    benefit_per_million = (
        cp_value
        * delta_conc_per_kg
        * HEALTH_PARAMS["benefit_per_ug_m3_ntd"]
    )
    return benefit_per_million / 1_000_000        # BCR = 效益/成本


# ─────────────────────────────────────────────────────────────
# 輸出
# ─────────────────────────────────────────────────────────────
DIV = "─" * 78

def print_header():
    print("\n" + "=" * 78)
    print(f"  SIP 空品前驅物 CP 值分析 — {STUDY_REGION['name']}")
    print(f"  現況 PM2.5：{STUDY_REGION['base_pm25_ug_m3']} μg/m³"
          f"  → 目標：{STUDY_REGION['target_pm25_ug_m3']} μg/m³")
    print("=" * 78)


def print_cp_table():
    results = []
    for p in PRECURSORS:
        params = PRECURSOR_PARAMS[p]
        cp = calc_cp(params["formation_factor"], params["cost_ntd_per_ton"])
        reduction = calc_reduction_amount(p)
        pm25 = calc_pm25_reduction(p)
        cost = calc_total_cost(p)
        bcr = calc_bcr(cp)
        results.append({
            "p": p,
            "label": params["label"],
            "ff": params["formation_factor"],
            "cost_wan": params["cost_ntd_per_ton"] / 10_000,
            "cp": cp,
            "reduction_ton": reduction,
            "pm25_ton": pm25,
            "total_cost_million": cost / 1_000_000,
            "bcr": bcr,
        })

    results.sort(key=lambda x: x["cp"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank

    print(f"\n{DIV}")
    print("  【前驅物 CP 值排名】")
    print(DIV)
    bcr_col = "    BCR" if results[0]["bcr"] is not None else ""
    print(f"  {'排名':<4} {'前驅物':<20} {'形成因子':>10} {'成本(萬/t)':>12} "
          f"{'CP值':>12} {'削減量(t)':>11} {'PM2.5削減(t)':>14}"
          + (f"{'BCR':>8}" if bcr_col else ""))
    print(f"  {'':4} {'':20} {'(kg/kg)':>10} {'':>12} "
          f"{'(kg/百萬$)':>12} {'':>11} {'':>14}")
    print(f"  {DIV}")

    for r in results:
        bcr_str = f"{r['bcr']:>8.2f}" if r["bcr"] is not None else ""
        print(
            f"  {r['rank']:<4}"
            f" {r['label']:<20}"
            f" {r['ff']:>10.3f}"
            f" {r['cost_wan']:>12.1f}"
            f" {r['cp']:>12.1f}"
            f" {r['reduction_ton']:>11.1f}"
            f" {r['pm25_ton']:>14.2f}"
            + (f" {bcr_str}" if r["bcr"] is not None else "")
        )

    print(f"  {DIV}")
    print(f"  CP值 = 每投入 100萬 NT$，可削減的 PM2.5 等量 (kg)")
    if results[0]["bcr"] is not None:
        print(f"  BCR  = 健康效益 NT$ / 減量成本 NT$")
    print()

    return results


def print_scenarios(cp_results_by_precursor):
    print(f"\n{DIV}")
    print("  【SIP 情境分析】")

    for name, scenario in SIP_SCENARIOS.items():
        if scenario["total_budget_million_ntd"] is None:
            continue

        budget = scenario["total_budget_million_ntd"]
        alloc = scenario["budget_allocation"]

        if all(v is None for v in alloc.values()):
            continue

        print(f"\n  ── {name}：{scenario['description']}")
        print(f"     總預算：{budget} 百萬 NT$")

        total_pm25 = 0.0
        total_used = 0.0
        for p, share in alloc.items():
            if share is None or share == 0:
                continue
            if p not in cp_results_by_precursor:
                continue
            r = cp_results_by_precursor[p]
            b = budget * share
            pm25 = r["cp"] * b
            label = PRECURSOR_PARAMS[p]["label"]
            print(f"     {label:<20}  {share*100:.0f}%  "
                  f"→ 削減 {pm25:>8,.1f} kg PM2.5")
            total_pm25 += pm25
            total_used += b

        portfolio_cp = total_pm25 / total_used if total_used > 0 else 0
        print(f"     {'─'*50}")
        print(f"     總削減量：{total_pm25:,.1f} kg PM2.5"
              f"   組合 CP：{portfolio_cp:.1f} kg/百萬$")

    print()


def print_recommendation(ranked):
    print(f"\n{DIV}")
    print("  【分析結論】")
    print(DIV)
    best = ranked[0]
    print(f"\n  CP 值最高前驅物：{best['label']}")
    print(f"  CP 值：{best['cp']:.1f} kg PM2.5 / 百萬 NT$")
    print(f"  每公噸削減成本：{best['cost_wan']:.1f} 萬 NT$")
    print(f"  二次生成因子：{best['ff']:.3f} kg PM2.5 / kg 前驅物")
    print(f"\n  排名總覽：")
    for r in ranked:
        print(f"    第{r['rank']}名  {r['label']:<20}  CP = {r['cp']:>8.1f}")
    print()


# ─────────────────────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────────────────────
def main():
    validate()
    print_header()
    ranked = print_cp_table()

    by_precursor = {r["p"]: r for r in ranked}
    print_scenarios(by_precursor)
    print_recommendation(ranked)


if __name__ == "__main__":
    main()
