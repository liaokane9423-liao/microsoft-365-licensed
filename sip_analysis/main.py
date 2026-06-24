"""
SIP 空品前驅物 CP 值分析 - 主程式
執行：python main.py
輸出：終端機報表 + (選用) 圖表
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cp_analysis import (
    analyze_all_precursors,
    analyze_cross_source,
    best_strategy,
    sip_portfolio_analysis,
)
from precursor_data import PRECURSOR_LABELS

DIVIDER = "─" * 80


def fmt_cp(val: float) -> str:
    return f"{val:>8.1f}"


def print_table(results, title: str):
    print(f"\n{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}")
    print(f"  {'排名':<4} {'前驅物':<22} {'形成因子':>10} {'成本(萬NT$/t)':>14} "
          f"{'CP值':>12} {'CP低':>10} {'CP高':>10} {'BCR':>8}")
    print(f"  {'':4} {'':22} {'(kg/kg)':>10} {'':>14} "
          f"{'(kg/百萬$)':>12} {'':>10} {'':>10} {'':>8}")
    print(f"{'─'*80}")

    for r in results:
        label = PRECURSOR_LABELS.get(r.precursor, r.precursor)
        print(
            f"  {r.rank:<4}"
            f" {label:<22}"
            f" {r.formation_factor:>10.3f}"
            f" {r.abatement_cost_ntd_per_ton/10000:>14.1f}"
            f" {fmt_cp(r.cp_kg_pm25_per_million_ntd)}"
            f" {fmt_cp(r.cp_low)}"
            f" {fmt_cp(r.cp_high)}"
            f" {r.benefit_cost_ratio:>8.1f}"
        )
    print(f"{'─'*80}")
    print(f"  CP值 = 每投入 100萬 NT$，可削減 PM2.5 等量 (kg)")
    print(f"  BCR  = 健康效益 NT$ / 減量成本 NT$\n")


def main():
    print("\n" + "=" * 80)
    print("  台灣 SIP 政策 — 空品前驅物減量 CP 值分析")
    print("  (每公噸前驅物減量的環境效益成本比)")
    print("=" * 80)

    # ── 1. 各排放源別 CP 值排名 ─────────────────────────────────────────────
    source_labels = {
        "stationary": "固定源 (工廠、電廠)",
        "mobile":     "移動源 (車輛、船舶)",
        "area":       "逸散/面源 (農業、溶劑、揚塵)",
    }

    cross = analyze_cross_source()

    for source, results in cross.items():
        print_table(results, f"【{source_labels[source]}】前驅物 CP 值排名")

    # ── 2. 綜合建議 ──────────────────────────────────────────────────────────
    print("=" * 80)
    print("  SIP 政策建議摘要")
    print("=" * 80)

    for source, results in cross.items():
        best = results[0]
        label = PRECURSOR_LABELS.get(best.precursor, best.precursor)
        print(f"\n  [{source_labels[source]}]")
        print(f"   → CP 最高前驅物：{label}")
        print(f"   → CP 值：{best.cp_kg_pm25_per_million_ntd:.1f} kg PM2.5 / 百萬NT$")
        print(f"   → 技術路徑：{best.tech}")
        print(f"   → BCR：{best.benefit_cost_ratio:.2f}")

    # ── 3. 假設 SIP 預算 10 億 NT$ 的情境試算 ───────────────────────────────
    budget = 1_000  # 百萬 NT$
    print(f"\n{'─'*80}")
    print(f"  情境模擬：SIP 預算 {budget} 百萬 NT$ ({budget/1000:.0f} 億)")
    print(f"{'─'*80}")

    # 情境 A：集中在固定源 CP 最高者
    best_precursor, pm25_kg, bcr = best_strategy(budget, "stationary")
    label = PRECURSOR_LABELS.get(best_precursor, best_precursor)
    print(f"\n  [情境A] 全部投入固定源最佳前驅物 ({label})")
    print(f"   → 可削減 PM2.5 等量：{pm25_kg:,.0f} kg ({pm25_kg/1000:.1f} 公噸)")
    print(f"   → 效益成本比 (BCR)：{bcr:.2f}")

    # 情境 B：多前驅物組合策略 (固定源)
    portfolio_alloc = {
        "SO2":          0.35,
        "NH3":          0.25,
        "NOx":          0.20,
        "PM25_primary": 0.15,
        "VOC":          0.05,
    }
    port = sip_portfolio_analysis(budget, portfolio_alloc, "stationary")
    print(f"\n  [情境B] 組合策略 (固定源)")
    for p, share in portfolio_alloc.items():
        lbl = PRECURSOR_LABELS.get(p, p)
        d = port["per_precursor"].get(p)
        if d:
            print(f"   {lbl:20s}  預算占比 {share*100:.0f}%"
                  f"  → 削減 {d['pm25_reduced_kg']:>7,.0f} kg PM2.5"
                  f"  (CP={d['cp']:.1f})")
    print(f"   ══ 總削減量：{port['total_pm25_kg']:,.0f} kg PM2.5")
    print(f"   ══ 組合 CP 值：{port['portfolio_cp_kg_per_million']:.1f} kg/百萬NT$")

    # 情境 C：逸散源中 NH3 農業管理
    best_p_area, pm25_area, bcr_area = best_strategy(budget, "area")
    label_area = PRECURSOR_LABELS.get(best_p_area, best_p_area)
    print(f"\n  [情境C] 全部投入逸散/面源最佳前驅物 ({label_area})")
    print(f"   → 可削減 PM2.5 等量：{pm25_area:,.0f} kg ({pm25_area/1000:.1f} 公噸)")
    print(f"   → BCR：{bcr_area:.2f}")

    # ── 4. 關鍵解讀 ──────────────────────────────────────────────────────────
    print(f"\n{'='*80}")
    print("  關鍵發現與 SIP 政策意涵")
    print(f"{'='*80}")
    print("""
  1. SO2 (固定源)
     → 硫酸鹽生成因子高 (0.54)、FGD 技術成熟、成本相對低
     → 通常在台灣固定源中 CP 值最高，每百萬 NT$ 可減最多 PM2.5

  2. NH3 (逸散/農業)
     → 在 NH3 飽和條件下，生成因子可高達 0.95
     → 精準施肥/廢水覆蓋成本極低，面源 CP 值往往最高
     → 台灣豬糞尿、農田施肥是重要標的，但管制困難度高

  3. NOx (移動源)
     → 車輛汰換成本極高，導致移動源 NOx 的 CP 值偏低
     → 但 NOx 對臭氧及硝酸鹽有雙重效益，長期效益被低估

  4. VOC
     → SOA 生成率不確定性大，平均 CP 值最低
     → 但對臭氧改善有共同效益 (PM2.5 + O3 協同減量)

  5. 一次 PM2.5
     → 形成因子 = 1 (直接計入)，但控制成本高 (DPF、布袋集塵)
     → 固定源 CP 值居中，逸散源 (揚塵抑制) CP 值最高

  SIP 最佳策略建議：
  ► 短期 (3年內)：優先 SO2 固定源減量 + NH3 農業面源管制
  ► 中期 (3-10年)：加強 NOx 移動源汰舊換新 + VOC 工業管制
  ► 長期：全面轉型清潔能源，系統性降低所有前驅物排放
""")


if __name__ == "__main__":
    main()
