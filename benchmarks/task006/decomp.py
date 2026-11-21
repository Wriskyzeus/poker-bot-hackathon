import sys, collections, json
exec(open("/tmp/t006/analyze_t006.py").read().split("facing = ")[0])
dec=collections.defaultdict(lambda:[0.0,0]); posn=collections.defaultdict(lambda:[0.0,0]); floatfold=collections.defaultdict(lambda:[0,0,0.0])
for block,setting,opp,f in load_runs():
    if setting!="standard": continue
    for hn,h in parse(f).items():
        if "board" not in h or not h["dec"]: continue
        hero=hero_of(h); bbv=h["blinds"]["bb"]; net=h["net"].get(hero,0)/bbv
        hd=h["dec"]; nb=len(h["board"]); ended={0:"preflop",3:"flop",4:"turn",5:"river"}.get(nb,"?")
        l=hd[-1]; act=l["applied"]["action"]
        kind=("hero_folded" if (l["bot"]==hero and act=="fold") else "opp_folded" if (l["bot"]!=hero and act=="fold") else "showdown/allin")+"@"+ended
        dec[(opp,kind)][0]+=net; dec[(opp,kind)][1]+=1
        hd_h=[d for d in hd if d["bot"]==hero]
        if hd_h:
            s=hd_h[0]["state"]; pos="SB(button)" if s["seat_to_act"]==s["sb_seat"] else "BB"
            posn[(opp,pos)][0]+=net; posn[(opp,pos)][1]+=1
        fl=[d for d in hd_h if d["street"]=="flop" and d["state"]["amount_owed"]>0 and d["applied"]["action"]=="call"]
        if fl:
            lf=any(d["street"] in("turn","river") and d["applied"]["action"]=="fold" for d in hd_h)
            floatfold[opp][0]+=1; floatfold[opp][1]+=lf
            if lf: floatfold[opp][2]+=net
print("net bb/hand for V3.4 by how hands ended (standard blinds, dev+hold):")
for k in sorted(dec):
    if dec[k][1]>=30: print("  %-13s %-26s n=%5d  sum %+8.1f bb  avg %+.2f"%(k[0],k[1],dec[k][1],dec[k][0],dec[k][0]/dec[k][1]))
print("\nnet bb/hand by position:")
for k in sorted(posn): print("  %-13s %-11s n=%5d avg %+.3f bb/hand"%(k[0],k[1],posn[k][1],posn[k][0]/posn[k][1]))
print("\nflop call then later fold:")
for k,v in sorted(floatfold.items()): print("  %-13s flop calls %4d  later folded %4d (%.0f%%)  net of those hands %+.0f bb"%(k,v[0],v[1],100*v[1]/v[0],v[2]))
