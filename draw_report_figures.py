from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent;INV=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'));OUT=ROOT/'evidence'/'diagrams';OUT.mkdir(parents=True,exist_ok=True)
FONT=r'C:\Windows\Fonts\msyh.ttc'
def font(s):return ImageFont.truetype(FONT,s)
def text(d,xy,t,size=36,fill='#152536',anchor='mm'):d.multiline_text(xy,t,font=font(size),fill=fill,anchor=anchor,align='center',spacing=10)
def box(d,x,y,t,w=420,h=110,fill='#e8f2fb',size=36):d.rounded_rectangle((x-w/2,y-h/2,x+w/2,y+h/2),18,fill=fill,outline='#36566f',width=3);text(d,(x,y),t,size)
def line(d,a,b,color='#4d6980',width=5):d.line([a,b],fill=color,width=width)
def host(n):return next(x for x in INV['devices'] if x['name']==n)
def cn(n):return host(n).get('display_name',n)
for gi,(agg,area,accs) in enumerate(INV['groups']):
    im=Image.new('RGB',(1800,1100),'white');d=ImageDraw.Draw(im)
    text(d,(900,55),f'{cn(agg)}：业务分区与实际接口',52)
    box(d,450,180,'核心交换机一\nS5700',500,125);box(d,1350,180,'核心交换机二\nS5700',500,125)
    box(d,900,420,f'{cn(agg)}\nS5700 · 区域 0/{area} 边界路由器',650,130)
    for x,k in [(450,0),(1350,1)]:
        line(d,(x,243),(900,355),'#386b96' if k==0 else '#ba751b')
        text(d,(400 if x==450 else 1400,305),f'GE0/0/{3+gi} ↔ GE0/0/{23+k}\nVLAN {1101+gi if k==0 else 1201+gi}',30)
    xs=[900] if len(accs)==1 else [500,1300] if len(accs)==2 else [300,900,1500]
    for j,((acc,v,sub,hn),x) in enumerate(zip(accs,xs)):
        for ofs in [-7,7]:line(d,(900+ofs,485),(x+ofs,635),width=5)
        box(d,x,690,cn(acc),490,110,size=34)
        text(d,(x,570),f'Eth-Trunk {j+1} · 2×GE\n汇聚 GE{2*j+1}/{2*j+2} ↔ 接入 GE23/24',27)
        line(d,(x,745),(x,850));h=host(hn)
        label=f'{cn(hn)}\n{h["ip"]}\nVLAN {v} · 网关 {h["gw"]}'
        if acc=='ACC-WLAN':label+='\n访客无线：10.162.116.10 / VLAN 140'
        if acc=='NMS-SW':label+='\n运维堡垒机：10.162.120.20'
        box(d,x,945,label,550,190,fill='#edf6eb',size=29 if acc in ['ACC-WLAN','NMS-SW'] else 33)
        text(d,(x+150,800),'GE1 接终端'+('；GE2 接访客' if acc=='ACC-WLAN' else '；GE2 接堡垒机' if acc=='NMS-SW' else ''),26)
    text(d,(900,1072),'图中均为实际铜缆链路；并行线表示 LACP 的两条成员链路；核心图标为同一对核心的分区引用。',27)
    im.save(OUT/f'{agg}.png')
im=Image.new('RGB',(1800,1500),'white');d=ImageDraw.Draw(im)
text(d,(900,65),'医院园区网分层逻辑总览',58)
for x,n in [(300,'ISP-R1'),(900,'ISP-R2'),(1500,'HEALTH-R')]:box(d,x,220,cn(n)+'\nAR2220',440,125)
for x in [300,900,1500]:line(d,(x,283),(x,330));line(d,(x,330),(900,330))
box(d,900,400,'外联隔离交换机 · S5700\nVLAN 901 / 902 / 903 独立广播域',1100,120,size=38)
for x,n in [(500,'FW-A'),(1300,'FW-B')]:line(d,(900,460),(x,565));box(d,x,630,cn(n)+' · USG5500\n'+('双机热备：主设备' if n=='FW-A' else '双机热备：备设备'),600,130)
line(d,(800,630),(1000,630),'#8c6b9c',7);text(d,(900,592),'GE6 心跳',27)
box(d,900,885,'双核心骨干 · OSPF 区域 0\n核心交换机一 / 核心交换机二 · S5700\nVRRP + MSTP + 双成员 Eth-Trunk',1360,170,fill='#e7edf5',size=40)
for x in [500,1300]:line(d,(x,695),(x,800))
text(d,(900,1030),'七台汇聚均双上联两台核心，分别承担业务区 ABR；逐端口连接见链路表。',31)
for i,(agg,area,_) in enumerate(INV['groups']):
    row=i//4;col=i%4;x=240+col*440;y=1150+row*170
    box(d,x,y,f'{cn(agg)}\n区域 {area}',420,130,fill='#edf6eb',size=31)
text(d,(900,1450),'非军事区交换机双归属防火墙；18 台接入均有终端；远程医疗保留 医疗专线路由器 ↔ 远程医疗网关 的 IPsec 备用链路。',27)
im.save(OUT/'overview.png')
print('generated',len(list(OUT.glob('*.png'))),'figures')
