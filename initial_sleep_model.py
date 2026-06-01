"""Initial WeBe sleep/wake model.
Step 1: build per-minute tables (run build_tables.py first -> table_*.csv)
Step 2: per-person relative threshold (60th pct) -> S/W prediction -> metrics."""
import pandas as pd, numpy as np

TABLES = {"Jiaqi":"table_jiaqi.csv","Shifan":"table_shifan.csv","Tina":"table_tina.csv"}
PCT = 60  # per-person percentile threshold

def metrics(pred, gt):
    acc=(pred==gt).mean()
    TP=((pred=="S")&(gt=="S")).sum(); TN=((pred=="W")&(gt=="W")).sum()
    FP=((pred=="S")&(gt=="W")).sum(); FN=((pred=="W")&(gt=="S")).sum()
    sens=TP/(TP+FN); spec=TN/(TN+FP); n=len(gt); po=acc
    pe=((TP+FP)/n)*((TP+FN)/n)+((TN+FN)/n)*((TN+FP)/n)
    return acc, sens, spec, (po-pe)/(1-pe)

rows=[]
for name, path in TABLES.items():
    d = pd.read_csv(path).dropna(subset=["webe_count"]).reset_index(drop=True)
    thr = np.percentile(d["webe_count"], PCT)          # per-person -> handles unit mismatch
    pred = np.where(d["webe_count"] > thr, "W", "S")    # high activity -> Wake
    gt = d["actigraph_SW"].values
    a,se,sp,ka = metrics(pred, gt)
    rows.append([name, round(thr,2), f"{a:.1%}", f"{se:.1%}", f"{sp:.1%}", round(ka,2)])

print(pd.DataFrame(rows, columns=
    ["Person","Threshold","Accuracy","SleepSens","WakeSpec","Kappa"]).to_string(index=False))
