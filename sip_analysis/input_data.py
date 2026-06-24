"""
=============================================================
  SIP 空品前驅物 CP 值分析 — 使用者輸入資料
=============================================================
請自行填入你的研究數據。
每個區塊都有說明欄位意義與單位。
填完後執行 `python run_analysis.py` 即可得到結果。
=============================================================
"""

# ─────────────────────────────────────────────────────────────
# 1. 你的研究區域基本設定
# ─────────────────────────────────────────────────────────────
STUDY_REGION = {
    "name":              "",        # 例："台中市"、"高雄市"、"全台灣"
    "area_km2":          None,      # 研究範圍面積 (km²)
    "population":        None,      # 人口數
    "mix_height_m":      None,      # 混合層高度 (m)，常用 500~1500
    "base_pm25_ug_m3":   None,      # 現況 PM2.5 年均濃度 (μg/m³)
    "target_pm25_ug_m3": None,      # SIP 目標濃度 (μg/m³)
}

# ─────────────────────────────────────────────────────────────
# 2. 前驅物清單（可新增或刪除）
#    key = 你想用的名稱代碼（英文、無空格）
# ─────────────────────────────────────────────────────────────
PRECURSORS = [
    "NOx",
    "SO2",
    "NH3",
    "VOC",
    "PM25_primary",
    # 可自行新增，例如 "EC"、"OC"
]

# ─────────────────────────────────────────────────────────────
# 3. 每種前驅物的參數
#
#    formation_factor : 二次 PM2.5 生成因子
#                       (kg PM2.5 生成 / kg 前驅物削減)
#                       一次 PM2.5 請填 1.0
#                       可來自 CMB/PMF 受體模式、CMAQ 靈敏度模擬
#                       或文獻引用值
#
#    emission_ton_yr  : 現況年排放量 (公噸/年)
#                       來自你的排放清冊 (TEDS 或自建)
#
#    reduction_target_pct : SIP 設定的削減目標百分比 (0~100)
#
#    cost_ntd_per_ton : 每削減 1 公噸該前驅物的成本 (NT$)
#                       建議填入你的成本效益評估數字
#                       或 EPA 公告的控制技術成本
#
# ─────────────────────────────────────────────────────────────
PRECURSOR_PARAMS = {
    "NOx": {
        "label":               "NOx (氮氧化物)",
        "formation_factor":    None,   # 填入你的數值，例：0.18
        "emission_ton_yr":     None,   # 例：12000
        "reduction_target_pct":None,   # 例：20
        "cost_ntd_per_ton":    None,   # 例：55000
    },
    "SO2": {
        "label":               "SO2 (二氧化硫)",
        "formation_factor":    None,
        "emission_ton_yr":     None,
        "reduction_target_pct":None,
        "cost_ntd_per_ton":    None,
    },
    "NH3": {
        "label":               "NH3 (氨)",
        "formation_factor":    None,
        "emission_ton_yr":     None,
        "reduction_target_pct":None,
        "cost_ntd_per_ton":    None,
    },
    "VOC": {
        "label":               "VOC (揮發性有機物)",
        "formation_factor":    None,
        "emission_ton_yr":     None,
        "reduction_target_pct":None,
        "cost_ntd_per_ton":    None,
    },
    "PM25_primary": {
        "label":               "一次 PM2.5",
        "formation_factor":    1.0,    # 一次排放固定為 1.0，不需改動
        "emission_ton_yr":     None,
        "reduction_target_pct":None,
        "cost_ntd_per_ton":    None,
    },
}

# ─────────────────────────────────────────────────────────────
# 4. 健康效益參數
#    用於計算效益成本比 (BCR)
#    若不做 BCR 分析，全部留 None 即可
# ─────────────────────────────────────────────────────────────
HEALTH_PARAMS = {
    # 每降低 1 μg/m³ PM2.5，該地區一年的健康貨幣化效益 (NT$)
    # 計算方式：人口 × 死亡率 × CR係數 × VSL
    # 或直接引用 EPA 環境部的地區效益值
    "benefit_per_ug_m3_ntd": None,   # 例：1_500_000_000 (15億)

    # 參考 VSL（生命統計價值，NT$），如有自算的話填這邊
    "vsl_ntd":               None,   # 例：25_000_000

    # PM2.5 濃度反應係數 β (per μg/m³)，來自流行病學文獻
    "cr_coefficient":        None,   # 例：0.007
}

# ─────────────────────────────────────────────────────────────
# 5. SIP 情境設定（可設定多個情境）
# ─────────────────────────────────────────────────────────────
SIP_SCENARIOS = {
    "情境一": {
        "description": "",           # 情境說明，例："優先削減固定源 SO2"
        "total_budget_million_ntd": None,  # SIP 總預算 (百萬 NT$)
        # 各前驅物預算分配比例（相加應 ≤ 1.0）
        "budget_allocation": {
            "NOx":          None,    # 例：0.30
            "SO2":          None,
            "NH3":          None,
            "VOC":          None,
            "PM25_primary": None,
        },
    },
    "情境二": {
        "description": "",
        "total_budget_million_ntd": None,
        "budget_allocation": {
            "NOx":          None,
            "SO2":          None,
            "NH3":          None,
            "VOC":          None,
            "PM25_primary": None,
        },
    },
    # 可複製上方格式繼續新增情境三、四...
}
