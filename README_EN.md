# Sleep_wake_algorithm — File Guide (README)

This folder contains all code, input data, and output results for the WeBe vs.
ActiGraph analysis. For the report, the main pieces are: the sleep/wake models
(initial + improved), the accelerometer comparison, and the data-quality issues
they revealed (unit inconsistency, corrupted raw timestamps).

Subjects and data (each person, one overnight session, 22:00 → 10:00 next day):
- Jessie (Jiaqi Zhang) — night of 2026/5/17, WeBe Regular 25Hz offline
- Shifan — night of 2026/5/16, WeBe Regular 25Hz offline
- Tina (Tiannan Zhang) — night of 2026/5/19, WeBe 100Hz online → downsampled to 25Hz

---

## 1. Run order (important)

Scripts depend on each other and must be run in this order:

1. `build_tables.py`  → produces table_jiaqi/shifan/tina.csv (all other scripts depend on these)
2. `initial_sleep_model.py`   (reads table_*.csv)
3. `improved_sleep_model.py`  (reads table_*.csv)
4. `accelerometer_comparison.py`  (reads table_*.csv + the three *_10sec.csv)

All files are in the same folder. The code uses filenames only (no path
prefixes), so the scripts run as-is.

---

## 2. Python scripts (.py)

### build_tables.py — data alignment (the foundation)
Aligns each person's raw WeBe accelerometer data with the corresponding
ActiGraph minute-level sleep labels (ground truth) into one "one row per minute"
table.

- WeBe activity feature (webe_count): within each minute, the sum of the
  sample-to-sample absolute change in acceleration magnitude √(x²+y²+z²) —
  analogous to ActiGraph activity counts (more movement → larger value).
- Time alignment: WeBe timestamps are in UTC; they are shifted by −7 hours to
  Pacific Time (PT), then binned by minute to match the ground-truth
  22:00–10:00 window.

Produces three tables. On run, the console prints each table's match rate;
expected values are:
- Jiaqi 719/720 (100%), Shifan 687/720 (95%), Tina 661/720 (92%)
(If a match rate is clearly too low, it is most likely a timezone-conversion
issue — check the UTC→PT step.)

### initial_sleep_model.py — initial sleep/wake model (assignment pt. 4)
The simplest threshold method: a person is nearly still when asleep and moves
when awake.
- For each person, the threshold is the 60th percentile of that person's own
  webe_count distribution (a per-person relative threshold, used to offset the
  unit inconsistency between the three files).
- Above threshold → Wake, below → Sleep.
- Compared minute-by-minute with ground truth, outputting Accuracy /
  Sleep Sensitivity / Wake Specificity / Cohen's kappa.

Reference results: Accuracy ~76–82%, kappa ~0.51–0.61.

### improved_sleep_model.py — improved model (assignment pt. 5)
Adds three standard improvements on top of the initial model:
1. log1p + per-person z-score normalization (more robustly removes inter-device
   unit differences);
2. 5-minute majority-vote smoothing (removes brief misclassifications);
3. 5-minute minimum run length (removes single-minute flips during sleep).

Reference results: mean Accuracy improves from 78.5% to 84.2%, kappa from 0.55
to 0.65. (Jessie improves most: Acc 77.6%→88%, kappa 0.51→0.71.)
Note the trade-off: smoothing merges brief wake periods into sleep, slightly
lowering wake specificity for some subjects — worth mentioning in the Discussion.

### accelerometer_comparison.py — accelerometer comparison (assignment pt. 3)
Compares WeBe vs. ActiGraph per-minute activity to check whether the two devices
agree.
- Does NOT use ActiGraph raw data (see "Known issue 2" below); instead uses the
  10-sec counts (*_10sec.csv), whose timestamps are correct, aggregated by
  minute and compared with the WeBe activity count.
- Because of the unit inconsistency, both sides are log + z-score normalized
  before comparison, so the comparison is about pattern shape rather than
  absolute values.
- Outputs each person's Pearson r.

Reference results: Jessie 0.39 / Shifan 0.22 / Tina 0.49, mean 0.36 (moderate
positive correlation).
Meaning: WeBe and ActiGraph activity/rest patterns are broadly consistent,
supporting that WeBe functions properly. Reasons it is not higher: different
wear position, ActiGraph's proprietary counts algorithm, calibration
differences, and minute-level (approximate) alignment.

---

## 3. Input data files

WeBe raw data (per-person overnight):
- `jessie2_debug_log2csv.csv` — Jessie's WeBe (exported by the developer)
- `Shifan_Liu_20260516053310_..._8c98.csv` — Shifan's WeBe
- `output_25hz-LPF.csv` — Tina's WeBe (100Hz, downsampled + low-pass filtered to 25Hz)

ActiGraph ground truth (per-person minute-level S/W labels + summary, Cole-Kripke algorithm):
- `Sleep_analysis_data.csv` — Jessie's minute-level sleep labels
- `Shifan_Sleep_analysis_data.csv` — Shifan's
- `Tina_Sleep_analysis_data.csv` — Tina's

ActiGraph 10-sec epoch counts (correct timestamps, used for the accelerometer comparison):
- `Jessie_STM2E40243809_10sec.csv`
- `Shifan_STM2E40243809_10sec.csv`
- `Tina_STM2E40243809_10sec.csv`

---

## 4. Output files

- `table_jiaqi.csv` / `table_shifan.csv` / `table_tina.csv`
  One row per minute: minute (time), webe_count (WeBe activity feature),
  actigraph_SW (ground-truth label S/W).
  (Some versions also include model_pred_SW = model prediction.)
  These are the core tables for all analyses.

- `initial_model_results.csv`
  Summary of the initial model's performance for all three subjects (threshold,
  Accuracy, Sensitivity, Specificity, kappa). Can go straight into a Results
  table in the report.

---

## 5. Known data issues (recommended for the Discussion; also required by assignment pt. 3)

1. **Unit inconsistency between WeBe files.** The three subjects' WeBe
   acceleration magnitudes differ by orders of magnitude (Shifan ≈ 1g, Jessie in
   the tens of thousands, Tina in between), and ActiGraph uses yet another scale.
   All cross-file / cross-device comparisons must therefore be normalized first.
   The early WeBe activity-summary logs showed physically impossible values
   (e.g. millions of kcal / MET), most likely a manifestation of this unit issue
   in the actigraphy pipeline — those absolute numbers should not be cited
   directly.

2. **ActiGraph raw (.agsd→csv) timestamps are corrupted.** The exported datetime
   is synthetically generated at a fixed step and the counter column has garbage
   values, so it cannot be used for precise time alignment (using it directly
   yields near-zero or even negative correlation). The accelerometer comparison
   therefore uses the .agd 10-sec counts (correct timestamps) instead.

3. **Match rate below 100%.** WeBe data has some missing minutes (Tina 92%,
   Shifan 95%); those minutes are treated as missing and excluded from comparison.

---

## 6. Individual differences (Discussion material)

The three subjects' sleep patterns differ markedly, which is useful for testing
model robustness:
- Jessie: efficiency 87%, one consolidated sleep period (22:51→7:49).
- Shifan: split into two sleep periods (long wake gap in between); fragmented
  Sleep/Wake overall.
- Tina: late bedtime (0:25), slept soundly but with a long wake period in the
  first half of the night.

A model that is only accurate for a person who sleeps in one good block is not a
good model; being robust to fragmented and late sleep is what matters. This may
also explain why the accelerometer correlation is lower for Shifan and higher
for Tina.
