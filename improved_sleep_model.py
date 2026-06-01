"""Improved WeBe sleep/wake model (assignment pt.5).
Improvements over initial: (1) log1p + per-person z-score normalization
(removes inter-device unit mismatch), (2) 5-min majority-vote smoothing,
(3) 5-min minimum run length (removes single-minute flicker).
Run build_tables.py first to get table_*.csv."""
import pandas as pd, numpy as np

TBL={"Jiaqi":"table_jiaqi.csv","Shifan":"table_shifan.csv","Tina":"table_tina.csv"}
WIN, MINLEN = 5, 5

def metrics(pred,gt):
    acc=(pred==gt).mean()
    TP=((pred=="S")&(gt=="S")).sum();TN=((pred=="W")&(gt=="W")).sum()
    FP=((pred=="S")&(gt=="W")).sum();FN=((pred=="W")&(gt=="S")).sum()
    se=TP/(TP+FN);sp=TN/(TN+FP);n=len(gt);po=acc
    pe=((TP+FP)/n)*((TP+FN)/n)+((TN+FN)/n)*((TN+FP)/n)
    return acc,se,sp,(po-pe)/(1-pe)

def smooth_minlen(pred,win,minlen):
    s=pd.Series(pred).map({"S":1,"W":0})
    sm=(s.rolling(win,center=True,min_periods=1).mean()>=0.5).map({True:"S",False:"W"}).values
    out=sm.copy();i=0;n=len(out)
    while i<n:
        j=i
        while j<n and out[j]==out[i]: j+=1
        if j-i<minlen and i>0: out[i:j]=out[i-1]
        i=j
    return out

def predict(d):
    c=np.log1p(d["webe_count"].values)
    z=(c-c.mean())/c.std()
    return smooth_minlen(np.where(z>0,"W","S"),WIN,MINLEN)

if __name__=="__main__":
    rows=[]
    for k,p in TBL.items():
        d=pd.read_csv(p).dropna(subset=["webe_count"]).reset_index(drop=True)
        a,se,sp,ka=metrics(predict(d),d["actigraph_SW"].values)
        rows.append([k,f"{a:.1%}",f"{se:.1%}",f"{sp:.1%}",round(ka,2)])
    print(pd.DataFrame(rows,columns=["Person","Acc","Sens","Spec","Kappa"]).to_string(index=False))
