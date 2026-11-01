from pathlib import Path
import json,re,xml.etree.ElementTree as E
R=Path(__file__).parent
j=json.loads((R/'lab_inventory.json').read_text(encoding='utf-8'));D={d['name']:d for d in j['devices']}
p=R/'output/hospital-network/工程/hospital-network.topo'
s=(R/'evidence/layout-utf8-backup.topo').read_text(encoding='utf-8-sig');s=re.sub('encoding="[^"]+"','encoding="utf-8"',s,count=1);root=E.fromstring(s)
names={'WAN-L2':'外联隔离交换机','ISP-R1':'主运营商路由器','ISP-R2':'备运营商路由器','HEALTH-R':'医疗专线路由器','PUBLIC-WEB':'主公网测试终端','PUBLIC-BACKUP':'备公网测试终端','HEALTH-PC':'医疗专线终端','FW-A':'主防火墙','FW-B':'备防火墙','CORE-SW1':'核心交换机一','CORE-SW2':'核心交换机二','DMZ-SW':'非军事区交换机','DMZ-WEB':'非军事区服务终端','AGG-CLINIC':'门急诊汇聚','ACC-OPD':'门诊接入','OPD-PC':'门诊终端','ACC-ER':'急诊接入','ER-PC':'急诊终端','ACC-PHARM':'药房接入','PHARM-PC':'药房终端','AGG-INPATIENT':'住院部汇聚','ACC-WARD-A':'病区一接入','WARD-A-PC':'病区一终端','ACC-WARD-B':'病区二接入','WARD-B-PC':'病区二终端','AGG-MEDTECH':'医技科汇聚','ACC-PACS':'影像科接入','PACS-PC':'影像科终端','ACC-LAB':'检验科接入','LAB-PC':'检验科终端','AGG-DC':'数据中心汇聚','DC-SW-A':'业务服务器接入','DC-SW-B':'影像服务器接入','BACKUP-SW':'备份服务器接入','HIS-SRV':'医院业务服务终端','PACS-SRV':'影像服务终端','BACKUP-SRV':'备份服务终端','AGG-OFFICE':'办公运维汇聚','ACC-ADMIN':'行政接入','ADMIN-PC':'行政终端','ACC-FIN':'财务接入','FIN-PC':'财务终端','NMS-SW':'运维接入','NMS-PC':'网管终端','BASTION':'运维堡垒机','AGG-IOT':'物联无线汇聚','ACC-IOT':'医疗物联接入','IOT-PC':'医疗物联终端','ACC-CCTV':'视频监控接入','CCTV-PC':'视频监控终端','ACC-WLAN':'无线网络接入','STAFF-PC':'员工无线终端','GUEST-PC':'访客无线终端','AGG-BRANCH':'分院汇聚','BRANCH-SW':'分院接入','BRANCH-PC':'分院终端','TELEMED-GW':'远程医疗网关','TELEMED-PC':'远程会诊终端'}
def pos(n,x,y):D[n].update(x=x,y=y,display_name=names[n])
for n,x,y in [('HEALTH-PC',70,100),('HEALTH-R',300,170),('ISP-R1',740,160),('PUBLIC-WEB',740,55),('ISP-R2',1500,160),('PUBLIC-BACKUP',1500,55),('WAN-L2',1120,235),('FW-A',1000,365),('FW-B',1420,365),('CORE-SW1',1050,555),('CORE-SW2',1410,555),('DMZ-SW',2280,400),('DMZ-WEB',2280,100)]:pos(n,x,y)
order=['AGG-BRANCH','AGG-CLINIC','AGG-INPATIENT','AGG-MEDTECH','AGG-DC','AGG-OFFICE','AGG-IOT']
groups={g[0]:g for g in j['groups']}
for i,n in enumerate(order):
 x=20+i*365;agg,area,accs=groups[n];pos(n,x+150,770)
 xs=[x+65] if len(accs)==1 else [x+65,x+240] if len(accs)==2 else [x+25,x+145,x+265]
 for (acc,v,sub,hn),xx in zip(accs,xs):pos(acc,xx,965);pos(hn,xx,1080)
 if n=='AGG-BRANCH':pos('TELEMED-GW',x+265,965);pos('TELEMED-PC',x+265,1180)
 if n=='AGG-OFFICE':pos('BASTION',x+265,1200)
 if n=='AGG-IOT':pos('GUEST-PC',x+265,1200)
tips=root.find('txttips');tips.clear();sh=root.find('shapes');sh.clear()
def bgr(h):r,g,b=bytes.fromhex(h);return r+(g<<8)+(b<<16)
def region(x,y,w,h,color):E.SubElement(sh,'shape',type='1',filloption='1',color=str(bgr(color)),upleftcorner=f'{x},{y}',width=str(w),height=str(h),startpt='0,0',endpt='0,0',borderStyle='0',borderWidth='2')
def txt(x,y,w,text,size=110,bold=False,color=-16777216):
 E.SubElement(tips,'txttip',left=str(x),top=str(y),right=str(x+w),bottom=str(y+max(24,len(text.splitlines())*20)),content=text.replace('\n','\r\n'),fontname='微软雅黑',fontstyle='1' if bold else '0',editsize=str(size),txtcolor=str(color),txtbkcolor='-1',charset='134')
for x,y,w,h,c,title in [(20,20,500,300,'E8F4FE','医疗专线与远程会诊'),(550,20,1230,300,'FFF1D6','双运营商互联网出口'),(900,335,660,155,'FDE5E8','边界安全区：双机热备'),(900,505,660,155,'E2EDFF','双核心骨干区：区域 0'),(2100,20,465,640,'E8F6E9','非军事区：对外服务')]:
 region(x,y,w,h,c);txt(x+12,y+10,w-24,title,140,True)
titles=['分院与远程医疗区','门急诊与药房区','住院病区','医技影像检验区','数据中心与备份区','行政财务与运维区','医疗物联与无线区']
colors=['E9F4FF','FFF0E5','EAF6EC','F1EAFE','E4F6F5','FFF5CE','FCE9F1']
footers=['虚拟局域网 50：10.162.105.0/24\n网关：10.162.105.1\n会诊网关：10.162.121.1/24', '虚拟局域网 10 / 80 / 90\n网关：10.162.101.1 / 109.1 / 110.1\n以上缩写均以 10.162 为前缀', '虚拟局域网 20\n网段：10.162.102.0/24\n网关：10.162.102.1', '虚拟局域网 30\n网段：10.162.103.0/24\n网关：10.162.103.1', '虚拟局域网 60 / 61\n网关：10.162.106.1 / 107.1\n以上缩写均以 10.162 为前缀', '虚拟局域网 40 / 160\n网关：10.162.104.1 / 120.1\n以上缩写均以 10.162 为前缀', '虚拟局域网 100 / 110 / 120 / 140\n网关尾段：111.1 / 112.1\n114.1（/23）/ 116.1（/22）']
for i,n in enumerate(order):
 x=20+i*365;region(x,710,355,640,colors[i]);txt(x+12,722,335,titles[i],140,True);txt(x+12,858,335,f'路由区域 {groups[n][1]}；双上联核心\n接入上联：两条千兆链路聚合',105);txt(x+12,1275,335,footers[i],100)
for d in j['devices']:
 if d.get('ip'):
  txt(d['x']-10,d['y']+84,160,d['ip'],100)
txt(55,252,450,'医疗网：172.20.1.0/24；网关 172.20.1.1\n专线侧：192.0.2.254/24',105)
txt(570,265,455,'主出口：12.1.1.254/24\n主公网网关：203.0.113.1',100)
txt(1320,265,450,'备出口：13.1.1.254/24\n备公网网关：203.0.114.1',100)
txt(1120,430,300,'心跳：172.31.255.1 / .2',105)
txt(1050,635,500,'核心互联：10.162.99.66 / .67；虚拟地址 .65',100)
txt(2140,260,410,'虚拟局域网 70：10.162.108.0/24\n服务终端网关：10.162.108.2\n虚拟地址 .1 保留；容灾待验证',110)
txt(2140,540,410,'双归属防火墙：千兆口 23 / 24\n服务终端：千兆口 1',110)
region(1650,350,410,305,'F1F3F5');txt(1665,365,380,'读图说明与骨干寻址',140,True)
txt(1665,407,380,'58 台设备 · 92 条实际铜缆链路\n并行线：两成员链路聚合\n业务网关均为对应网段的 .1\n物联区网关前缀均为 10.162\n核心—汇聚：10.162.99.96—151，/30\n主信任网关：10.162.99.1/27\n备信任网关：10.162.99.33/27\n远程加密链路：198.18.0.0/30',105)
txt(32,420,700,'远程医疗加密备用链路（沿左侧）\n医疗专线侧 198.18.0.1 ↔ 分院侧 198.18.0.2',110)
byid={d['id'].upper():d for d in j['devices']}
for dev in root.find('devices'):
 d=byid[dev.get('id').upper()];x,y=d['x'],d['y'];dev.set('name',d['display_name']);dev.set('cx',str(x));dev.set('cy',str(y));dev.set('edit_left',str(x));dev.set('edit_top',str(y+62))
for line in root.find('lines'):
 a=byid[line.get('srcDeviceID').upper()];b=byid[line.get('destDeviceID').upper()]
 for pair in line:
  for prefix in ['src','tar']:
   pair.set(prefix+'BoundRectIsMoved','0');pair.set(prefix+'BoundRect_X',str((a['x']+b['x'])/2));pair.set(prefix+'BoundRect_Y',str((a['y']+b['y'])/2));pair.set(prefix+'Offset_X','0');pair.set(prefix+'Offset_Y','0')
E.indent(root);p.write_bytes(('<?xml version="1.0" encoding="UNICODE" ?>\n'+E.tostring(root,encoding='unicode')).encode('gbk',errors='xmlcharrefreplace'))
(R/'lab_inventory.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print(p,'regions',len(sh),'labels',len(tips))
