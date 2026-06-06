
import pandas as pd, numpy as np

z = lambda x: (x - x.mean()) / x.std()

cfg = {  # person: (actigraph 10sec counts csv, webe per-minute table from build_tables.py)
    "Jessie": ("Jessie_STM2E40243809_10sec.csv", "table_jiaqi.csv"),
    "Shifan": ("Shifan_STM2E40243809_10sec.csv", "table_shifan.csv"),
    "Tina":   ("Tina_STM2E40243809_10sec.csv",   "table_tina.csv"),
}

print(f"{'Person':<8}{'PearsonR':>10}{'n_min':>8}")
rs = []
for name, (af, wf) in cfg.items():
    a = pd.read_csv(af)
    a["datetime"] = pd.to_datetime(a["datetime"])
    a["vm"] = np.sqrt(a.axis1**2 + a.axis2**2 + a.axis3**2)
    a["min"] = a["datetime"].dt.floor("min")
    am = a.groupby("min")["vm"].sum().reset_index(); am["min_idx"] = range(len(am))

    w = pd.read_csv(wf).dropna(subset=["webe_count"]).reset_index(drop=True)
    w["min_idx"] = range(len(w))

    m = pd.merge(am[["min_idx","vm"]], w[["min_idx","webe_count"]], on="min_idx")
    r = np.corrcoef(z(m.vm), z(np.log1p(m.webe_count)))[0,1]
    rs.append(r)
    print(f"{name:<8}{r:>10.3f}{len(m):>8}")
print(f"{'MEAN':<8}{np.mean(rs):>10.3f}")
