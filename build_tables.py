
import csv, datetime
import numpy as np
import pandas as pd

PT_OFFSET = datetime.timedelta(hours=7)  # epoch is UTC; local PT = UTC-7 (May)

def minute_key_from_epoch(ts):
    #epoch seconds (UTC) -> local-PT minute string 'YYYY/M/D H:MM' matching GT
    dt = datetime.datetime.fromtimestamp(ts) - PT_OFFSET
    dt = dt.replace(second=0, microsecond=0)
    return f"{dt.year}/{dt.month}/{dt.day} {dt.hour}:{dt.minute:02d}", dt

def load_gt(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines=[l.rstrip("\n") for l in fh]
    hi=[i for i,l in enumerate(lines) if l.startswith("Date,Time")][0]
    gt={}; order=[]
    for l in lines[hi+1:]:
        if not l.strip() or "," not in l: continue
        p=l.split(",")
        if len(p)<8: continue
        date,time,*_=p
        label=p[-1].strip()
        if label not in ("S","W"): continue
        # build datetime
        y,mo,d=[int(x) for x in date.split("/")]
        hh,mm=[int(x) for x in time.split(":")]
        dt=datetime.datetime(y,mo,d,hh,mm)
        key=f"{y}/{mo}/{d} {hh}:{mm:02d}"
        gt[key]=label; order.append((dt,label))
    return gt, order

def stream_webe_counts(path, ts_idx, ax_idx, ay_idx, az_idx, skip):
    #Stream WeBe csv, fill forward timestamps for blank rows (your file), and accumulate per-minute activity counts. Returns dict minute_key->count
    counts={}
    prev_mag=None
    last_ts=None
    # for blank-timestamp rows: we forward-fill the integer-second ts and rely on
    # 25 Hz spacing only for binning; exact sub-second not needed for minute bins.
    with open(path, encoding="utf-8", errors="replace") as fh:
        for i,line in enumerate(fh):
            if i<skip: continue
            p=line.rstrip("\n").split(",")
            if len(p)<=max(ax_idx,ay_idx,az_idx): continue
            tsraw=p[ts_idx].strip()
            if tsraw and tsraw.replace(".","").isdigit() and float(tsraw)>1e9:
                last_ts=float(tsraw)
            if last_ts is None:
                continue
            try:
                ax=float(p[ax_idx]); ay=float(p[ay_idx]); az=float(p[az_idx])
            except (ValueError, IndexError):
                continue
            mag=(ax*ax+ay*ay+az*az)**0.5
            if prev_mag is not None:
                d=abs(mag-prev_mag)
                key,_=minute_key_from_epoch(last_ts)
                counts[key]=counts.get(key,0.0)+d
            prev_mag=mag
    return counts

def build(person, webe_path, ts_idx, accel_idxs, skip, gt_path, out_path):
    gt, order = load_gt(gt_path)
    counts = stream_webe_counts(webe_path, ts_idx, *accel_idxs, skip)
    rows=[]
    for dt,label in order:
        key=f"{dt.year}/{dt.month}/{dt.day} {dt.hour}:{dt.minute:02d}"
        c=counts.get(key, np.nan)
        rows.append({"minute":dt, "webe_count":c, "actigraph_SW":label})
    df=pd.DataFrame(rows)
    matched=df["webe_count"].notna().sum()
    df.to_csv(out_path, index=False)
    print(f"{person}: GT minutes={len(df)}, WeBe-matched minutes={matched} "
          f"({100*matched/len(df):.0f}%), Sleep={sum(df.actigraph_SW=='S')} "
          f"Wake={sum(df.actigraph_SW=='W')}")
    return df

# accel column indices per file (from header inspection)
# jessie2: ts=0; accelx,accely,accelz at 27,28,29
import_hdr = lambda f,skip: open(f,encoding="utf-8",errors="replace").readlines()[skip-1].strip().split(",")

for person, wf, skip, gtf, outf in [
    ("Jiaqi (you)", "jessie2_debug_log2csv.csv", 1, None, "table_jiaqi.csv"),
    ("Shifan",      "Shifan_Liu_20260516053310_20260516170230_0a1e6c13_8c98.csv", 3, "Shifan_Sleep_analysis_data.csv", "table_shifan.csv"),
    ("Tina",        "output_25hz-LPF.csv", 1, "Tina_Sleep_analysis_data.csv", "table_tina.csv"),
]:
    hdr=import_hdr(wf,skip)
    ts_idx=hdr.index("timestamp")
    ai=(hdr.index("accelx"),hdr.index("accely"),hdr.index("accelz"))
    if person.startswith("Jiaqi"):
        # your GT data file from previous turn
        gtf="Sleep_analysis_data.csv"
    build(person, wf, ts_idx, ai, skip, gtf, "/home/claude/"+outf)
