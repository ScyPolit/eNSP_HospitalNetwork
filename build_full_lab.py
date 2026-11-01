from pathlib import Path
import uuid,json,csv,xml.etree.ElementTree as ET
ROOT=Path(__file__).parent
OUT=ROOT/'output'/'医院园区网';OUT.mkdir(parents=True,exist_ok=True)
D=[];L=[];ports={};nextport=2100
def dev(n,m,x,y,ip=None,gw=None):
    global nextport
    d=dict(name=n,model=m,x=x,y=y,id=str(uuid.uuid5(uuid.NAMESPACE_DNS,'hospital-campus-20261030-'+n)).upper())
    if ip:d.update(ip=ip,gw=gw)
    if m!='PC':d['port']=nextport;ports[n]=nextport;nextport+=1
    D.append(d)
def link(a,ai,b,bi,role):L.append(dict(a=a,ai=ai,b=b,bi=bi,role=role))
def pc(n,x,y,ip,gw):dev(n,'PC',x,y,ip,gw)

# Full physical inventory; WAN-L2 provides three isolated shared WAN segments.
dev('WAN-L2','S5700',170,300)
for i,n in enumerate(['ISP-R1','ISP-R2','HEALTH-R']):dev(n,'AR2220',70+260*i,70)
pc('PUBLIC-WEB',60,-65,'203.0.113.10','203.0.113.1')
pc('PUBLIC-BACKUP',320,-65,'203.0.114.10','203.0.114.1')
pc('HEALTH-PC',580,-65,'172.20.1.10','172.20.1.1')
link('ISP-R1',1,'PUBLIC-WEB',0,'Public HTTP/ICMP');link('ISP-R2',1,'PUBLIC-BACKUP',0,'Backup public')
link('HEALTH-R',1,'HEALTH-PC',0,'Medical external')
for i,n in enumerate(['ISP-R1','ISP-R2','HEALTH-R']):link(n,0,'WAN-L2',i,'WAN VLAN '+str(901+i))
dev('FW-A','USG5500',470,300);dev('FW-B','USG5500',770,300)
for fidx,f in enumerate(['FW-A','FW-B']):
    for i in range(3):link(f,i,'WAN-L2',3+fidx*3+i,'WAN '+str(901+i))
link('FW-A',6,'FW-B',6,'HRP heartbeat')
dev('CORE-SW1','S5700',400,600);dev('CORE-SW2','S5700',1240,600)
link('FW-A',3,'CORE-SW1',0,'Trust VLAN 900');link('FW-B',3,'CORE-SW2',0,'Trust VLAN 900')
link('FW-A',4,'CORE-SW2',1,'Trust VLAN 901');link('FW-B',4,'CORE-SW1',1,'Trust VLAN 901')
link('CORE-SW1',22,'CORE-SW2',22,'LACP member 1');link('CORE-SW1',23,'CORE-SW2',23,'LACP member 2')
dev('DMZ-SW','S5700',1040,300);pc('DMZ-WEB',1200,180,'10.162.108.10','10.162.108.1')
link('FW-A',5,'DMZ-SW',22,'DMZ VLAN 70');link('FW-B',5,'DMZ-SW',23,'DMZ standby')
link('DMZ-SW',0,'DMZ-WEB',0,'Published DMZ service')
groups=[
 ('AGG-CLINIC',10,[('ACC-OPD',10,101,'OPD-PC'),('ACC-ER',80,109,'ER-PC'),('ACC-PHARM',90,110,'PHARM-PC')]),
 ('AGG-INPATIENT',20,[('ACC-WARD-A',20,102,'WARD-A-PC'),('ACC-WARD-B',20,102,'WARD-B-PC')]),
 ('AGG-MEDTECH',20,[('ACC-PACS',30,103,'PACS-PC'),('ACC-LAB',30,103,'LAB-PC')]),
 ('AGG-DC',30,[('DC-SW-A',60,106,'HIS-SRV'),('DC-SW-B',60,106,'PACS-SRV'),('BACKUP-SW',61,107,'BACKUP-SRV')]),
 ('AGG-OFFICE',40,[('ACC-ADMIN',40,104,'ADMIN-PC'),('ACC-FIN',40,104,'FIN-PC'),('NMS-SW',160,120,'NMS-PC')]),
 ('AGG-IOT',40,[('ACC-IOT',100,111,'IOT-PC'),('ACC-CCTV',110,112,'CCTV-PC'),('ACC-WLAN',120,114,'STAFF-PC')]),
 ('AGG-BRANCH',50,[('BRANCH-SW',50,105,'BRANCH-PC')])]
vlans={};endpoint_oct={}
for i,(agg,area,access) in enumerate(groups):
    y=820+i*300;dev(agg,'S5700',820,y)
    link('CORE-SW1',2+i,agg,22,'Area0 P2P VLAN '+str(1101+i))
    link('CORE-SW2',2+i,agg,23,'Area0 P2P VLAN '+str(1201+i))
    for j,(acc,v,sub,host) in enumerate(access):
        x=1040+j*270;dev(acc,'S5700',x,y+100)
        link(agg,2*j,acc,22,'LACP '+str(v)+' member1');link(agg,2*j+1,acc,23,'LACP '+str(v)+' member2')
        endpoint_oct[sub]=endpoint_oct.get(sub,9)+1;ip=f'10.162.{sub}.{endpoint_oct[sub]}'
        pc(host,x,y+220,ip,f'10.162.{sub}.1');link(acc,0,host,0,'Access VLAN '+str(v))
        vlans[str(v)]=dict(sub=sub,area=area,agg=agg,mask='255.255.254.0' if v==120 else '255.255.255.0')
        if acc=='ACC-WLAN':
            pc('GUEST-PC',x+140,y+220,'10.162.116.10','10.162.116.1');link(acc,1,'GUEST-PC',0,'Guest VLAN 140')
            vlans['140']=dict(sub=116,area=40,agg=agg,mask='255.255.252.0')
        if acc=='NMS-SW':
            pc('BASTION',x+130,y+220,'10.162.120.20','10.162.120.1');link(acc,1,'BASTION',0,'Management bastion')
dev('TELEMED-GW','AR2220',1440,820+6*300+100)
pc('TELEMED-PC',1440,820+6*300+220,'10.162.121.10','10.162.121.1')
link('AGG-BRANCH',2,'TELEMED-GW',0,'Telemed inside VLAN50')
link('TELEMED-GW',1,'TELEMED-PC',0,'Telemedicine LAN')
link('HEALTH-R',2,'TELEMED-GW',2,'IPsec underlay 198.18.0.0/30')
models={d['name']:d['model'] for d in D};ids={d['name']:d['id'] for d in D}
def ifname(n,i):return ('Ethernet0/0/1' if models[n]=='PC' else 'GigabitEthernet0/0/'+str(i+1 if models[n]=='S5700' else i))
root=ET.Element('topo',version='1.3.00.100');ds=ET.SubElement(root,'devices')
for idx,d in enumerate(D):
    n=d['name'];m=d['model'];x=d['x'];y=d['y'];settings=''
    if m=='PC':
        mask='255.255.252.0' if n=='GUEST-PC' else '255.255.254.0' if n=='STAFF-PC' else '255.255.255.0'
        settings=f" -simpc_ip {d['ip']} -simpc_mask {mask} -simpc_gateway {d['gw']} -simpc_mac 54-89-98-26-{idx:02X}-10 -simpc_mc_dstip 0.0.0.0 -simpc_mc_dstmac 00-00-00-00-00-00 -simpc_dns1 0.0.0.0 -simpc_dns2 0.0.0.0 -simpc_ipv6 :: -simpc_prefix 128 -simpc_gatewayv6 :: -simpc_dhcp_state 0 -simpc_dhcpv6_state 0 -simpc_dns_auto_state 0 "
    devxml=ET.SubElement(ds,'dev',id=d['id'],name=n,poe='0',model=m,settings=settings,system_mac='',com_port=str(d.get('port',0)),bootmode='1',cx=str(x),cy=str(y),edit_left=str(x+27),edit_top=str(y+54))
    slot=ET.SubElement(devxml,'slot',number='slot17',isMainBoard='1')
    ET.SubElement(slot,'interface',sztype='Ethernet',interfacename='GE',count=str({'PC':1,'S5700':24,'AR2220':3,'USG5500':9}[m]))
ls=ET.SubElement(root,'lines')
for l in L:
    line=ET.SubElement(ls,'line',srcDeviceID=ids[l['a']],destDeviceID=ids[l['b']])
    ET.SubElement(line,'interfacePair',lineName='Copper',srcIndex=str(l['ai']),tarIndex=str(l['bi']),srcBoundRectIsMoved='0',srcBoundRect_X='0',srcBoundRect_Y='0',srcOffset_X='0',srcOffset_Y='0',tarBoundRectIsMoved='0',tarBoundRect_X='0',tarBoundRect_Y='0',tarOffset_X='0',tarOffset_Y='0')
ET.SubElement(root,'shapes');tips=ET.SubElement(root,'txttips')
for i,(agg,area,_) in enumerate(groups):ET.SubElement(tips,'txttip',left='240',top=str(820+i*300+130),right='750',bottom=str(820+i*300+150),content=f'{agg} | Area {area} | dual uplinks + LACP access',fontname='Consolas',fontstyle='0',editsize='100',txtcolor='-16777216',txtbkcolor='-1',charset='1')
ET.indent(root)
(OUT/'医院园区网-2-01-宋长宇.topo').write_text('<?xml version="1.0" encoding="UNICODE" ?>\n'+ET.tostring(root,encoding='unicode'),encoding='utf-8')
(ROOT/'lab_inventory.json').write_text(json.dumps(dict(devices=D,links=L,ports=ports,vlans=vlans,groups=groups),ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'设备链路与接口.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['序号','设备A','接口A','设备B','接口B','用途'])
    for i,l in enumerate(L,1):w.writerow([i,l['a'],ifname(l['a'],l['ai']),l['b'],ifname(l['b'],l['bi']),l['role']])
print('devices',len(D),'infrastructure',len(ports),'links',len(L));print(OUT)
