# Sleep_wake_algorithm — 文件说明 (README)

本文件夹包含 WeBe vs ActiGraph 分析的全部代码、输入数据和输出结果。
写报告时主要参考三块：sleep/wake 模型（initial + improved）、accelerometer
comparison，以及它们暴露的数据质量问题（单位不一致、raw 时间戳损坏）。

被试与对应数据（三人各一晚 overnight，22:00 → 次日 10:00）：
- Jessie (Jiaqi Zhang) — 2026/5/17 那晚，WeBe Regular 25Hz offline
- Shifan — 2026/5/16 那晚，WeBe Regular 25Hz offline
- Tina (Tiannan Zhang) — 2026/5/19 那晚，WeBe 100Hz online → 已降采样到 25Hz

---

## 一、运行顺序（重要）

脚本之间有依赖，必须按此顺序跑：

1. `build_tables.py`  → 生成 table_jiaqi/shifan/tina.csv（其它脚本都依赖这三张表）
2. `initial_sleep_model.py`   （读 table_*.csv）
3. `improved_sleep_model.py`  （读 table_*.csv）
4. `accelerometer_comparison.py`  （读 table_*.csv + 三个 *_10sec.csv）

所有文件都在同一文件夹内，代码里只写文件名、无路径前缀，直接运行即可。

---

## 二、Python 脚本（.py）

### build_tables.py — 数据对齐（地基）
把每个人的 WeBe 原始加速度，和对应的 ActiGraph 逐分钟睡眠标签（ground
truth），对齐成一张「每分钟一行」的建模表。

- WeBe 活动特征（webe_count）：每分钟内，加速度幅值 √(x²+y²+z²) 的逐样本
  变化量绝对值之和 —— 类比 ActiGraph 的 activity counts（动得多→值大）。
- 时间对齐：WeBe 时间戳是 UTC，统一减 7 小时换算成太平洋时间（PT），
  再按分钟归桶，与 ground truth 的 22:00–10:00 窗口对齐。

输出三张表，运行时控制台会打印每张表的匹配率，正常应为：
- Jiaqi 719/720 (100%)、Shifan 687/720 (95%)、Tina 661/720 (92%)
（匹配率若明显偏低，多半是时区换算问题，须检查 UTC→PT 那一步。）

### initial_sleep_model.py — 最初版 sleep/wake 模型（作业第4点）
最朴素的阈值法：人睡着时几乎不动、清醒时动得多。
- 对每个人，用其自身 webe_count 分布的 60th 百分位作阈值
  （per-person 相对阈值，用来抵消三人文件之间的单位不一致）。
- 高于阈值判 Wake，低于判 Sleep。
- 与 ground truth 逐分钟对比，输出 Accuracy / Sleep Sensitivity /
  Wake Specificity / Cohen's kappa。

参考结果：Accuracy 约 76–82%，kappa 约 0.51–0.61。

### improved_sleep_model.py — 改进版模型（作业第5点）
在 initial 基础上加三项标准改进：
1. log1p + per-person z-score 归一化（更稳地消除设备间单位差异）；
2. 5 分钟多数投票平滑（去掉短暂误判）；
3. 5 分钟最小连续段（去掉睡眠中的单分钟跳变）。

参考结果：平均 Accuracy 由 78.5% 提升到 84.2%，kappa 由 0.55 提升到 0.65。
（其中 Jessie 提升最大：Acc 77.6%→88%，kappa 0.51→0.71。）
注意 trade-off：平滑会把短暂清醒并入睡眠，使部分人的 wake specificity 略降，
这点可写进 Discussion。

### accelerometer_comparison.py — 加速度对比（作业第3点）
对比 WeBe 与 ActiGraph 的每分钟活动量，看两设备是否一致。
- 不用 ActiGraph 的 raw（见下方「已知问题2」），改用时间戳正确的 10sec
  counts（*_10sec.csv），按分钟聚合后与 WeBe activity count 比较。
- 因单位不一致，比较前对双方做 log + z-score 归一化，比的是「模式形状」
  而非绝对值。
- 输出每人的 Pearson r。

参考结果：Jessie 0.39 / Shifan 0.22 / Tina 0.49，平均 0.36（中等正相关）。
含义：WeBe 与 ActiGraph 的活动/静止模式总体一致，验证 WeBe 基本功能正常。
未达高相关的原因：佩戴位置不同、ActiGraph 专有 counts 算法、单位标定差异、
分钟级近似对齐。

---

## 三、输入数据文件

WeBe 原始数据（每人 overnight）：
- `jessie2_debug_log2csv.csv` — Jessie 的 WeBe（由开发同学导出）
- `Shifan_Liu_20260516053310_..._8c98.csv` — Shifan 的 WeBe
- `output_25hz-LPF.csv` — Tina 的 WeBe（100Hz 已降采样+低通滤波到 25Hz）

ActiGraph ground truth（每人那晚的逐分钟 S/W 标签 + 汇总，Cole-Kripke 算法）：
- `Sleep_analysis_data.csv` — Jessie 的逐分钟睡眠标签
- `Shifan_Sleep_analysis_data.csv` — Shifan 的
- `Tina_Sleep_analysis_data.csv` — Tina 的

ActiGraph 10 秒 epoch counts（时间戳正确，供加速度对比用）：
- `Jessie_STM2E40243809_10sec.csv`
- `Shifan_STM2E40243809_10sec.csv`
- `Tina_STM2E40243809_10sec.csv`

---

## 四、输出文件

- `table_jiaqi.csv` / `table_shifan.csv` / `table_tina.csv`
  每分钟一行：minute（时间）、webe_count（WeBe 活动特征）、
  actigraph_SW（ground truth 标签 S/W）。
  （部分版本还含 model_pred_SW = 模型预测。）这是所有分析的核心表。

- `initial_model_results.csv`
  initial 模型三人表现汇总（阈值、Accuracy、Sensitivity、Specificity、kappa），
  可直接放进报告 Results 表格。

---

## 五、已知数据问题（建议写进报告 Discussion，作业第3点也要求分析）

1. **WeBe 文件间单位不一致。** 三人 WeBe 加速度幅值量纲差几个数量级
   （Shifan ≈ 1g、Jessie 上万、Tina 居中），ActiGraph 又是另一套。
   故所有跨文件/跨设备比较前都必须归一化。早期 WeBe activity summary 日志里
   出现「数百万 kcal / MET」等物理上不可能的数值，很可能就是这个单位问题
   在 actigraphy 计算管线里的体现 —— 那些绝对数值不可直接引用。

2. **ActiGraph raw（.agsd→csv）时间戳损坏。** 导出的 datetime 是按固定步长
   人工生成的、counter 列数值乱跳，无法用于精确时间对齐（直接用会得到接近 0
   甚至负的相关）。因此加速度对比改用 .agd 的 10sec counts（时间戳正确）。

3. **匹配率不足 100%。** WeBe 数据存在少量缺失分钟（Tina 92%、Shifan 95%），
   分析时这些分钟按缺失处理、不参与对比。

---

## 六、个体差异（Discussion 素材）

三人睡眠模式差异明显，正好测试模型鲁棒性：
- Jessie：efficiency 87%，整段睡眠（22:51→7:49）。
- Shifan：分两段睡（中间长时间清醒），整夜 Sleep/Wake 较碎。
- Tina：上床晚（0:25），睡得实但前半夜大段清醒。

一个只在「整段好睡」的人身上准的模型不算好；能同时 handle 分段睡和晚睡才算
鲁棒。这也是 accelerometer 相关性 Shifan 偏低、Tina 偏高的可能原因之一。
