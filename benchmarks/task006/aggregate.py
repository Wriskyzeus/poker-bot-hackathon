import csv, glob, json, os, hashlib, collections
R="/tmp/t006/results"; rows=[]
for d in sorted(glob.glob(R+"/*_*_*/")):
    name=os.path.basename(d.rstrip("/")); block,setting,opp=name.split("_",2)
    pairs=list(csv.DictReader(open(d+"pairs.csv"))); ms=list(csv.DictReader(open(d+"matches.csv")))
    c=collections.Counter(p["outcome_for_A"] for p in pairs)
    ok=[m for m in ms if m["status"]=="ok"]; aw=sum(1 for m in ok if m["winner"]=="A")
    bad=sum(int(m["a_errors"])+int(m["b_errors"])+int(m["a_timeouts"])+int(m["b_timeouts"])+int(m["a_restarts"])+int(m["b_restarts"]) for m in ms)
    hands=sum(int(m["hands"]) for m in ok)
    rows.append(dict(block=block,setting=setting,opp=opp,pairs=len(pairs),W=c["W"],D=c["D"],L=c["L"],
      matches=len(ok),v34_match_wins=aw,pair_score=round((c["W"]+0.5*c["D"])/max(1,len(pairs)),3),
      incomplete=len(ms)-len(ok),problems=bad,avg_hands=round(hands/max(1,len(ok)),1),
      v34_avg_think_ms=round(sum(float(m["a_avg_think_ms"]) for m in ok)/max(1,len(ok)),2),
      v34_max_think_ms=max(float(m["a_max_think_ms"]) for m in ok) if ok else 0,
      opp_max_think_ms=max(float(m["b_max_think_ms"]) for m in ok) if ok else 0,
      csv_sha256=hashlib.sha256(open(d+"matches.csv","rb").read()).hexdigest()[:16]))
os.makedirs("/tmp/t006/analysis",exist_ok=True)
json.dump(rows,open("/tmp/t006/analysis/aggregate.json","w"),indent=1)
w=csv.DictWriter(open("/tmp/t006/analysis/aggregate.csv","w"),fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print("%-5s %-8s %-13s %5s %3s %3s %3s  %9s %6s %5s"%("blk","struct","opp","pairs","W","D","L","matchwins","score","prob"))
for r in rows: print("%-5s %-8s %-13s %5d %3d %3d %3d  %3d/%-5d %6.3f %5d"%(r["block"],r["setting"],r["opp"],r["pairs"],r["W"],r["D"],r["L"],r["v34_match_wins"],r["matches"],r["pair_score"],r["problems"]))
# combined across dev+hold
print("\nCOMBINED dev+hold")
comb=collections.defaultdict(lambda:[0,0,0,0,0])
for r in rows:
    k=(r["setting"],r["opp"]); x=comb[k]; x[0]+=r["W"];x[1]+=r["D"];x[2]+=r["L"];x[3]+=r["v34_match_wins"];x[4]+=r["matches"]
for k,x in sorted(comb.items()): print("%-8s %-13s pairs W/D/L %2d/%2d/%2d  match wins %2d/%2d  pair-score %.3f"%(k[0],k[1],x[0],x[1],x[2],x[3],x[4],(x[0]+.5*x[1])/(x[0]+x[1]+x[2])))
