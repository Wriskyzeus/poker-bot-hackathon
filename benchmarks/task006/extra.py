import sys, collections, json, numpy as np
exec(open("/tmp/t006/analyze_t006.py").read().split("facing = ")[0])
W=np.load("/tmp/t005/work/weights.npy"); E=np.load("/tmp/t005/work/equity.npy"); E=(E+(1-E.T))/2
def ev_call(i,d,a):
    s=np.array(NASH["res"]["%d_%s"%(d,a)]["jam"]); w=W[i]*s
    e=(w*E[i]).sum()/w.sum(); return d*(2*e-1)
missed=[];spots=collections.Counter(); flopnet=collections.defaultdict(lambda:[0.0,0]); stage=collections.defaultdict(lambda:[0.0,0])
ex_traces=collections.defaultdict(list)
for block,setting,opp,f in load_runs():
    for hn,h in parse(f).items():
        if "board" not in h or not h["dec"]: continue
        hero=hero_of(h); bbv=h["blinds"]["bb"]; net=h["net"].get(hero,0)/bbv
        if setting=="standard":
            stage[(opp,"early<40" if hn<40 else "mid40-99" if hn<100 else "late100+")][0]+=net; stage[(opp,"early<40" if hn<40 else "mid40-99" if hn<100 else "late100+")][1]+=1
            hh=[d for d in h["dec"] if d["bot"]==hero]
            if any(d["street"]=="flop" and d["state"]["amount_owed"]>0 and d["applied"]["action"]=="call" for d in hh):
                flopnet[opp][0]+=net; flopnet[opp][1]+=1
        if opp=="pressure" and setting=="standard":
            for d in h["dec"]:
                if d["bot"]!=hero or d["street"]!="preflop": continue
                s=d["state"]
                if s["seat_to_act"]==s["sb_seat"]: continue
                opp_p=[p for p in s["players"] if p["bot_id"]!=hero][0]
                if not opp_p["is_all_in"]: continue
                S=min(s["your_stack"]+s["your_bet_this_street"],opp_p["stack"]+opp_p["bet_this_street"])/bbv
                if S>15: continue
                dd=min((3,4,5,6,7,8,10,12,15),key=lambda x:abs(x-S)); a=0.1 if s["blinds"]["ante"]>0 else 0.0
                i=IDX[cls(*h["hole"][hero])]; call=NASH["res"]["%d_%s"%(dd,a)]["call"][i]>=0.5
                act=d["applied"]["action"]; ev=ev_call(i,dd,a)-(-(1+a))
                spots[(round(S) if False else ("<=8" if S<=8 else "8-15"),act=="call",call)]+=1
                if call and act=="fold": missed.append(ev)
                if call and act=="fold" and len(ex_traces["missedcall"])<4: ex_traces["missedcall"].append((os.path.basename(f),hn,round(S,1),h["hole"][hero],round(ev,2)))
print("pressure shoves <=15bb, V3.4 in BB: (bucket, V3.4 called?, Nash call?) counts:",dict(spots))
print("missed Nash calls: n=%d  avg EV gain from calling instead of folding = %.2f bb  total %.0f bb over 80 standard matches"%(len(missed),np.mean(missed),np.sum(missed)))
print("examples",ex_traces["missedcall"])
print("\nflop-call hands net (standard):")
for k,v in sorted(flopnet.items()): print("  %-13s hands with a flop call %4d  avg net %+.2f bb/hand  total %+.0f bb"%(k,v[1],v[0]/v[1],v[0]))
print("\nstage avg V3.4 bb/hand (standard):")
for k in sorted(stage): print("  %-13s %-9s n=%5d %+.3f"%(k[0],k[1],stage[k][1],stage[k][0]/stage[k][1]))
