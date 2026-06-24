# 專案背景

使用者正在進行**空品專題研究**，主題：

> 透過 **SIP（State Implementation Plan）政策**框架，分析每公噸前驅物（NOx、SO2、NH3、VOC、一次 PM2.5）對環境的影響，找出 **CP 值最高**的前驅物作為優先減量標的。

分析工具放在 `sip_analysis/`：
- `input_data.py`：使用者自行填入數據（生成因子、排放量、成本、情境）
- `run_analysis.py`：計算 CP 值、BCR、SIP 情境比較

使用者要**自己填數據、自己跑分析**，不需要我預先填入或給出結論。
