from pathlib import Path
import json,math
ROOT=Path(__file__).parent;j=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'));D={x['name']:x for x in j['devices']}
def pos(n,x,y):D[n]['x']=x;D[n]['y']=y
for x,n,h in [(350,'ISP-R1','PUBLIC-WEB'),(650,'ISP-R2','PUBLIC-BACKUP'),(50,'HEALTH-R','HEALTH-PC')]:pos(n,x,150);pos(h,x,20)
for n,x,y in [('WAN-L2',170,220),('FW-A',470,330),('FW-B',770,330),('DMZ-SW',1040,180),('DMZ-WEB',1200,20),('CORE-SW1',300,500),('CORE-SW2',1120,500)]:pos(n,x,y)
for gi,(agg,area,acclist) in enumerate(j['groups']):
    y=650+gi*300;pos(agg,710,y)
    for k,(acc,v,sub,h) in enumerate(acclist):
        x=1280+k*250;pos(acc,x,y+150);pos(h,x,y+230)
        if acc=='ACC-WLAN':pos('GUEST-PC',x+140,y+230)
        if acc=='NMS-SW':pos('BASTION',x+130,y+230)
pos('TELEMED-GW',50,2600);pos('TELEMED-PC',50,2720)
over=[]
vals=list(D.values())
for i,a in enumerate(vals):
    for b in vals[i+1:]:
        if abs(a['x']-b['x'])<112 and abs(a['y']-b['y'])<72:over.append([a['name'],b['name']])
def intersects(a,b,r):
    x0,y0=a;x1,y1=b;dx=x1-x0;dy=y1-y0;lo,hi=0.,1.
    for p,q in [(-dx,x0-r[0]),(dx,r[2]-x0),(-dy,y0-r[1]),(dy,r[3]-y0)]:
        if p==0:
            if q<0:return False
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
    return lo<=hi
cuts=[]
for l in j['links']:
    a=D[l['a']];b=D[l['b']];ap=(a['x']+32,a['y']+32);bp=(b['x']+32,b['y']+32)
    for n,d in D.items():
        if n in [l['a'],l['b']]:continue
        # Actual symbol footprint; labels are inspected in the live screenshot.
        r=(d['x']+4,d['y']+4,d['x']+60,d['y']+60)
        if intersects(ap,bp,r):cuts.append([l['a'],l['b'],n])
(ROOT/'evidence/layout-proposed.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'evidence/layout-audit.json').write_text(json.dumps(dict(devices=len(D),links=len(j['links']),device_overlaps=over,lines_through_symbols=cuts),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(overlaps=over,through_symbols=cuts),ensure_ascii=False))
