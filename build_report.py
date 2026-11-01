from pathlib import Path
from copy import deepcopy
import json,re,zipfile,hashlib
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).parent;OUT=ROOT/'output';SRC=ROOT/'01-2-01-宋长宇.docx';INV=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'))
doc=Document(SRC);old=doc.paragraphs[-1];old._element.getparent().remove(old._element)
settings=doc.settings.element
if settings.find(qn('w:doNotAutoCompressPictures')) is None:settings.append(OxmlElement('w:doNotAutoCompressPictures'))
s=doc.sections[-1];s.page_width=Cm(21);s.page_height=Cm(29.7);s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.5)
FIG=0;TAB=0
def fmt_run(r,size=12,bold=False,cn='宋体',en='Times New Roman'):
    r.font.name=en;r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=RGBColor(0,0,0)
    fonts=r._element.get_or_add_rPr().get_or_add_rFonts();fonts.set(qn('w:eastAsia'),cn);fonts.set(qn('w:ascii'),en);fonts.set(qn('w:hAnsi'),en)
def para(t='',kind='body'):
    p=doc.add_paragraph();f=p.paragraph_format;f.line_spacing=1.5;f.space_before=Pt(0);f.space_after=Pt(0);f.first_line_indent=Pt(24);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
    if kind.startswith('h'):
        level=int(kind[1:]);f.first_line_indent=Pt(0 if level<3 else 24);p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        before,after={1:(6,6),2:(4,4),3:(3,2),4:(2,2),5:(2,2)}[level];f.space_before=Pt(before);f.space_after=Pt(after);f.keep_with_next=True;f.page_break_before=False
    r=p.add_run(t);fmt_run(r,bold=kind.startswith('h'));return p
def cap(t):
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.2;p.paragraph_format.space_after=Pt(4);fmt_run(p.add_run(t),10.5,cn='黑体');return p
def figure(path,title,width=16):
    global FIG
    path=Path(path)
    if not path.exists():return
    FIG+=1;p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(4);p.paragraph_format.line_spacing=1
    p.add_run().add_picture(str(path),width=Cm(width));cap(f'图 {FIG} {title}')
def shade(cell,color):
    pr=cell._tc.get_or_add_tcPr();el=OxmlElement('w:shd');el.set(qn('w:fill'),color);pr.append(el)
def borders(table,three=True):
    pr=table._tbl.tblPr;el=OxmlElement('w:tblBorders')
    for k in ['top','left','bottom','right','insideH','insideV']:
        v=OxmlElement('w:'+k);v.set(qn('w:val'),'single' if three and k in ['top','bottom'] else 'nil');v.set(qn('w:sz'),'10');v.set(qn('w:color'),'000000');el.append(v)
    pr.append(el)
def table(title,heads,rows):
    global TAB
    TAB+=1;c=cap(f'表 {TAB} {title}');c.paragraph_format.keep_with_next=True
    t=doc.add_table(rows=1,cols=len(heads));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False;borders(t)
    for cell,h in zip(t.rows[0].cells,heads):cell.text=str(h)
    for i,row in enumerate(rows):
        cells=t.add_row().cells
        for cell,value in zip(cells,row):
            cell.text=str(value)
            if i%2:shade(cell,'F2F2F2')
    for ri,row in enumerate(t.rows):
        for cell in row.cells:
            cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER if ri==0 else WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.15;p.paragraph_format.space_after=Pt(3)
                for r in p.runs:fmt_run(r,bold=ri==0)
            if ri==0:
                tc=cell._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders');bt=OxmlElement('w:bottom');bt.set(qn('w:val'),'single');bt.set(qn('w:sz'),'6');b.append(bt);tc.append(b)
        trpr=row._tr.get_or_add_trPr();ns=OxmlElement('w:cantSplit');trpr.append(ns)
        if ri==0:trpr.append(OxmlElement('w:tblHeader'))
    return t
def compact_code(text):
    return '\n'.join(line for line in text.replace('\r','').splitlines() if line.strip() and set(line.strip())!={'#'})

def code(title,lines):
    t=doc.add_table(rows=2,cols=1);t.alignment=WD_TABLE_ALIGNMENT.CENTER;borders(t,False)
    for i,text in enumerate([title,compact_code(lines if isinstance(lines,str) else '\n'.join(lines))]):
        cell=t.cell(i,0);shade(cell,'BFBFBF' if i==0 else 'F2F2F2');cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;p=cell.paragraphs[0];p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.0;p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(3)
        fmt_run(p.add_run(text),11 if i==0 else 10,i==0,cn='宋体',en='Consolas')
        t.rows[i]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
    t.cell(0,0).paragraphs[0].paragraph_format.keep_with_next=True

FULL_CONFIG_AUDIT=[]
def full_code(name,title):
    source=ROOT/'output/医院园区网/配置'/f'{name}-running.cfg'
    raw=source.read_text(encoding='utf-8').replace('\r','').rstrip('\n')
    text=compact_code(raw)
    assert re.search(r'(?m)^\s*sysname\s+'+re.escape(name)+r'\s*$',text),name
    assert text.rstrip().endswith('return'),name
    t=doc.add_table(rows=2,cols=1);t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False;t.columns[0].width=Cm(16);borders(t,False)
    for i in [0,1]:shade(t.cell(i,0),'BFBFBF' if i==0 else 'F2F2F2')
    cell=t.cell(0,0);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;p=cell.paragraphs[0];p.alignment=WD_ALIGN_PARAGRAPH.LEFT;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(3);p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=True;fmt_run(p.add_run(title),11,True,cn='宋体',en='Consolas')
    pr=t.rows[0]._tr.get_or_add_trPr();pr.append(OxmlElement('w:tblHeader'));pr.append(OxmlElement('w:cantSplit'))
    cell=t.cell(1,0);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.TOP
    for i,line in enumerate(text.split('\n')):
        p=cell.paragraphs[0] if i==0 else cell.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.LEFT;f=p.paragraph_format;f.first_line_indent=Pt(0);f.space_before=f.space_after=Pt(0);f.line_spacing=1;f.keep_with_next=False;f.keep_together=True;f.widow_control=False;fmt_run(p.add_run(line),10,cn='宋体',en='Consolas')
    assert '\n'.join(p.text for p in cell.paragraphs)==text,name
    FULL_CONFIG_AUDIT.append(dict(name=name,title=title,source=str(source),lines=len(text.splitlines()),original_lines=len(raw.splitlines()),removed_separator_or_blank_lines=len(raw.splitlines())-len(text.splitlines()),sha256=hashlib.sha256(text.encode('utf-8')).hexdigest()))
def page():doc.add_page_break()

para('医院园区网设计与实战','h1').alignment=WD_ALIGN_PARAGRAPH.CENTER
para('一、项目目标与实验环境','h1')
para('本项目面向医院园区，搭建覆盖门诊、住院、医技、数据中心、行政办公、医疗物联网、访客无线及分院远程医疗的分层网络。实验在经典 eNSP 中部署双公网出口、医保卫健专线、HRP 双防火墙、双核心及七个业务汇聚，通过真实终端流量验证路由、冗余和访问隔离。')
para('依据实验指导书第 13 项“园区网设计与实战”，综合应用 VLAN、VLANIF、Trunk、OSPF、Eth-Trunk、MSTP、VRRP、NAT、DHCP、ACL 与 IPsec。所有配置、控制台截图及抓包均以本次运行的工程为对象。')
table('实验环境与规模',['项目','实测环境或规模'],[
 ['仿真平台','eNSP V1.3.00.100；VirtualBox 5.2.26'],['设备镜像','S5700、AR2220、USG5500'],['抓包工具','Wireshark/TShark 4.6.4'],['设备数量','58 台：34 台网络设备与 24 个终端节点'],['网络设备','28 台交换机、4 台路由器、2 台防火墙'],['物理连接','92 条实际铜缆链路；接入及核心互联采用双成员 LACP'],['学生地址标识','物联网 24-2 班，班内小号 01；10.162.(101+n).0 网段']])
para('二、业务需求与访问边界','h1')
para('（一）业务与可靠性要求','h2')
para('临床终端访问指定业务服务器，普通科室之间默认隔离；医保卫健专线只访问前置业务及远程会诊；访客通过 NAT 访问公网，不能进入院内网。数据中心、备份、设备管理与普通终端分区部署，网络设备管理入口限制至堡垒机。')
para('冗余链路覆盖双运营商、双防火墙、双核心、各汇聚的两条骨干上联，以及各接入交换机到所属汇聚的两条 LACP 成员。汇聚自身采用单机，故本实验消除链路及核心、边界的部分单点，但不把汇聚单机表述为设备级冗余。')
para('（二）安全策略执行位置','h2')
para('边界防火墙控制公网、DMZ 与医疗专线的南北向流量。院内跨 VLAN 流量经汇聚和 Area 0 转发，未必经过防火墙，因此在汇聚绑定按 VLAN 生效的入方向 ACL，控制普通业务、访客、物联网与管理区的东西向访问。')
table('最小访问策略',['来源','允许对象','默认禁止对象'],[
 ['公网','已发布的 DMZ HTTP 映射','普通终端、数据中心、管理网'],['临床与办公','指定 HIS 的 TCP/443；显式开放诊断 ICMP；必要公网','其他科室、备份、数据库和设备管理'],['DMZ','指定 Web 到指定 HIS 的 TCP/443','其他数据中心及 Trust、Management'],['访客','DHCP、本网关诊断及公网 NAT','10/8、172.16/12、192.168/16'],['医疗专线','指定前置机及远程会诊终端','办公、IoT、管理和任意服务器'],['IoT / CCTV','指定平台或 NVR 的必要端口与诊断地址','普通办公、管理及其他服务器'],['Management','运维终端到堡垒机；堡垒机到管理地址','普通终端绕过堡垒机']])
para('三、网络与地址规划','h1')
para('（一）分层结构与完整性','h2')
para('完整工程保留原逻辑中的七台汇聚与十八台接入，未沿用交接时的十五台设备缩减工程。WAN-L2 是辅助二层设备，使用 VLAN 901、902、903 分别提供双 ISP 和医疗专线的共享外联网段，三个广播域彼此隔离。每台接入交换机至少连接一个实际终端。')
page();figure(ROOT/'evidence/topology-real/全网拓扑.png','eNSP 全网实际拓扑截图（原生高倍率分段截图拼接）')
para('正文中的拓扑图全部来自当前 eNSP 工程的真实界面。将画布放大至软件支持的最大倍率：总览按滚动位置分段截屏并按原始像素位置拼接，其余十二张分区图均由单张实际屏幕截图直接裁切。未重绘设备、链路或文字，也未用插值放大替代清晰度；DOCX 关闭自动图片压缩，PDF 中的拓扑图采用无损图片嵌入。原始屏幕截图与截图来源记录随工程归档。')
para('总览用于查看 58 台设备与十三个彩色分区的整体关系；由于 A4 页面宽度有限，IP、网关和设备名称请结合后面的放大实景图阅读。全尺寸总览保留约 4700 像素宽度，可在 PDF 中继续放大。实际接口的完整连接关系见链路清单。')
page();figure(ROOT/'evidence/topology-real/医疗专线区.png','医疗专线区的 eNSP 放大实景截图')
figure(ROOT/'evidence/topology-real/主公网与外联交换区.png','主公网与外联隔离交换机的 eNSP 放大实景截图')
page();figure(ROOT/'evidence/topology-real/备用公网区.png','备用公网的 eNSP 放大实景截图')
figure(ROOT/'evidence/topology-real/边界防火墙与双核心区.png','边界防火墙与双核心的 eNSP 放大实景截图')
page();figure(ROOT/'evidence/topology-real/非军事区.png','非军事区的 eNSP 放大实景截图',width=12)
para('（二）班级地址替换与 VLAN 规划','h2')
para('依指导书的班级与小号替换规则，第二字节采用 160+2=162，起始第三字节采用 100+01=101。前七个业务网段按 101—107 顺序配置，扩展区继续使用独立、不重叠的网段；员工无线和访客网按实际容量划分 /23 与 /22。骨干统一使用 10.162.99.0/24 的细分子网。')
names={10:'门诊',20:'住院护理',30:'影像检验',40:'行政财务',50:'分院',60:'业务服务器',61:'备份灾备',80:'急诊手术',90:'药房物资',100:'医疗物联网',110:'安防监控',120:'员工无线',140:'访客无线',160:'运维管理'}
rows=[]
for v,d in sorted(INV['vlans'].items(),key=lambda x:int(x[0])):
    prefix=23 if int(v)==120 else 22 if int(v)==140 else 24;rows.append([v+' '+names[int(v)],f'10.162.{d["sub"]}.0/{prefix}',f'10.162.{d["sub"]}.1',str(d['area'])])
rows.insert(7,['70 DMZ','10.162.108.0/24','当前 .2；虚拟组 .1','FW / Area 0'])
table('VLAN、网段、网关与区域',['VLAN / 业务','IPv4 网段','网关','Area'],rows)
table('外联与骨干地址',['链路','网段','实际分配'],[
 ['ISP1','12.1.1.0/24','ISP .254；FW-A .2、FW-B .3；VRRP .1'],['ISP2','13.1.1.0/24','ISP .254；FW-A .2、FW-B .3；VRRP .1'],['医疗专线','192.0.2.0/24','HEALTH .254；FW-A .2、FW-B .3；VRRP .1'],['Trust 900','10.162.99.0/27','FW .2/.3，虚拟 .1；核心 .4/.5'],['Trust 901','10.162.99.32/27','FW .34/.35，虚拟 .33；核心 .36/.37'],['核心对等','10.162.99.64/27','核心 .66/.67，VRRP .65'],['核心1到汇聚','10.162.99.(96+4n)/30','n=0—6；核心网络号+1，汇聚+2'],['核心2到汇聚','10.162.99.(124+4n)/30','n=0—6；核心网络号+1，汇聚+2'],['HRP 心跳','172.31.255.0/30','FW-A .1，FW-B .2；GE0/0/6'],['IPsec 底层','198.18.0.0/30','HEALTH .1，TELEMED .2；GE0/0/2']])
para('（三）OSPF 与网关位置','h2')
para('两台核心只加入 Area 0；七台汇聚的上联属于 Area 0，业务 VLANIF 加入 Area 10、20、30、40、50，形成 ABR。业务网关均位于对应汇聚，核心的 VRRP 地址 10.162.99.65 用于骨干对等管理诊断，不重复承载业务 VLAN 的 .1 网关。防火墙向骨干发布外部默认路由，业务终端侧 OSPF 接口设置为 silent-interface。')
para('医疗专线相邻路由器采用 FW 接口实地址 192.0.2.2/.3 作为主备下一跳，以 NQA 探测主设备虚拟地址的可达性。这样避开本镜像实测出现的虚拟 MAC 收包异常，同时保留 HRP、VRRP 角色和备用路由。DMZ 终端当前采用 FW-A 实地址 10.162.108.2 作为默认网关，虚拟组 .1 保留；DMZ 端到端自动切换未作为通过项。')
table('终端实际地址与默认网关',['终端','IPv4 地址','默认网关'],[[d.get('display_name',d['name'])+'（'+d['name']+'）',d['ip'],d['gw']] for d in INV['devices'] if d['model']=='PC'])
regions={'AGG-CLINIC':'门急诊与药房区','AGG-INPATIENT':'住院病区','AGG-MEDTECH':'医技影像检验区','AGG-DC':'数据中心与备份区','AGG-OFFICE':'行政财务与运维区','AGG-IOT':'医疗物联与无线区','AGG-BRANCH':'分院与远程医疗区'}
for agg,area,_ in INV['groups']:
    page();region=regions[agg];para(region+'实际拓扑','h3');figure(ROOT/f'evidence/topology-real/{region}.png',region+'的 eNSP 放大实景截图',width=12)
para('四、实施过程与逐设备配置','h1')
para('（一）建立工程和部署顺序','h2')
para('先在 eNSP 新建独立工程，放置外联路由器、双防火墙、双核心、七台汇聚和十八台接入，再按设备链路表连接 92 条链路。依次启动设备、划分 VLAN 与链路聚合、配置 VLANIF、建立 OSPF、配置边界策略与 NAT，最后设置终端并验证。控制台通过设备实际 TCP 控制端口连接，截图中的命令与输出均来自运行设备。')
para('以下按设备逐一列出最终完整配置，包括默认接口、系统默认段落及所有业务规则；不使用省略号或“其余同上”替代任何设备配置。为节约篇幅，代码删除设备导出时独占一行的井号分隔符及空行，命令内容、缩进和密码密文中的有效字符完整保留。代码采用两行一列表格，标题栏在跨页时重复，代码区允许跨页。显示、测试及故障恢复命令另列在验证节。终端通过图形界面设置地址，其全部输入值已列于终端地址表。')
para('（二）边界、核心与各业务设备','h2')
order=list(INV['ports'])
for idx,n in enumerate(order,1):
    d=next(x for x in INV['devices'] if x['name']==n);para(f'{idx}. {d.get("display_name",n)}（{n}，{d["model"]}）','h3')
    if n.startswith('FW-'):
        desc='配置四类边界接口及心跳接口，将接口加入安全域；设置 VRRP 主备组、组播 HRP 心跳、OSPF 与默认路由，最后加入逐条放行的安全策略和源 NAT。两台防火墙使用互不重叠的 NAT 子池，合计覆盖运营商规定的 .10—.30 范围。'
        lines=['interface GigabitEthernet0/0/6',f'ip address 172.31.255.{1 if n=="FW-A" else 2} 255.255.255.252','quit','hrp interface GigabitEthernet0/0/6','hrp enable']
    elif n.startswith('CORE-'):
        desc='建立核心互联 Eth-Trunk1，加入 GE0/0/23、GE0/0/24 两个成员，承载骨干 VLAN。配置核心 VRRP 和 MSTP 主备角色，各业务汇聚上联分别使用独立 /30，OSPF 仅声明 Area 0。'
        lines=['interface Eth-Trunk1','mode lacp-static','port link-type trunk','port trunk allow-pass vlan 900 901 4094','quit']
    elif n.startswith('AGG-'):
        area=next(a for x,a,_ in INV['groups'] if x==n);v=next(v for v,x in INV['vlans'].items() if x['agg']==n)
        desc=f'配置两条独立骨干上联，业务 VLANIF 放在 Area {area}，本机作为 Area 0/{area} ABR。接入双链路加入各自 Eth-Trunk；业务接口提供 DHCP，并按 VLAN 绑定 ACL，避免把过滤规则误施加至骨干。'
        lines=[f'interface Vlanif{v}',f'ip address 10.162.{INV["vlans"][v]["sub"]}.1 {INV["vlans"][v]["mask"]}','dhcp select interface','quit',f'traffic-filter vlan {v} inbound acl {3000+int(v)}'] if int(v) not in [60,61] else [f'interface Vlanif{v}',f'ip address 10.162.{INV["vlans"][v]["sub"]}.1 255.255.255.0','dhcp select interface','quit','ospf 1']
    elif d['model']=='AR2220':
        desc='按实际接口配置 IPv4 地址与路由。ISP 侧提供公网测试网段，HEALTH-R 承载医疗专线及 IPsec 对端，TELEMED-GW 承载会诊终端并通过静态路由和链路探测选择主备路径。'
        ip={'ISP-R1':'12.1.1.254','ISP-R2':'13.1.1.254','HEALTH-R':'192.0.2.254','TELEMED-GW':'10.162.105.20'}[n]
        lines=['interface GigabitEthernet0/0/0',f'ip address {ip} 255.255.255.0','quit','display ip interface brief']
    elif n in ['WAN-L2','DMZ-SW']:
        desc='将实际连接端口加入相应二层 VLAN。WAN-L2 将两家运营商及医疗专线分离；DMZ-SW 提供双防火墙共享的 DMZ 广播域。受本次镜像虚拟 MAC 转发兼容性影响，DMZ 终端实际默认网关使用 FW-A 的 .2 地址，保留 .1 虚拟组用于角色检查。'
        lines=['interface GigabitEthernet0/0/1','port link-type access','port default vlan '+('901' if n=='WAN-L2' else '70'),'quit']
    else:
        desc='把两条上联加入 Eth-Trunk1 并采用 LACP 静态模式，Trunk 仅放行所属业务 VLAN；GE0/0/1 接实际终端，配置为 Access。无线与管理接入另使用 GE0/0/2 承载访客或堡垒机。'
        lines=['interface Eth-Trunk1','mode lacp-static','port link-type trunk','quit','display eth-trunk 1']
    para(desc);full_code(n,d.get('display_name',n)+'（'+n+'）完整配置');figure(ROOT/f'evidence/screenshots/{n}-CLI.png',d.get('display_name',n)+'（'+n+'）的实时配置与运行状态')
    checks=['display current-configuration']
    if n.startswith('FW-'):checks+=['display hrp state','display hrp interface','display firewall session table verbose']
    elif n.startswith('CORE-'):checks+=['display vrrp brief','display ospf peer brief','display eth-trunk 1','display ip routing-table']
    elif n.startswith('AGG-'):checks+=['display ospf peer brief','display eth-trunk 1','display ip routing-table','display ip pool']
    elif d['model']=='AR2220':
        checks+=['display ip interface brief','display ip routing-table']
        if n in ['HEALTH-R','TELEMED-GW']:checks+=['display ipsec sa']
    elif n in ['WAN-L2','DMZ-SW']:checks+=['display port vlan']
    else:checks+=['display eth-trunk 1','display current-configuration interface GigabitEthernet0/0/1']
    code(n+' 配置与状态检查命令',checks)
para('（三）终端、DHCP 与安全过滤','h2')
para('终端按地址表输入静态地址、掩码和网关，先验证本网关与业务服务器，再测试禁止访问的目标。汇聚同时启用 DHCP 接口地址池，排除 .2—.49 的静态地址区间；网关 .1 自动保留，不能再次放入排除地址范围。DHCP 获取过程及地址池状态以验证节的实际证据为准。')
para('在访客终端实际切换 DHCP，取得 10.162.119.254/22，默认网关 10.162.116.1；Wireshark 保存完整 Discover、Offer、Request、ACK。验证后恢复规划静态地址 10.162.116.10。')
figure(ROOT/'evidence/live/GUEST-PC-ipconfig.png','访客 DHCP 租约与恢复静态地址的检查')
code('访客 VLAN 140 的关键规则',['acl number 3140',' rule 5 permit udp source-port eq bootpc destination-port eq bootps',' rule 10 permit icmp destination 10.162.116.1 0',' rule 15 deny ip destination 10.0.0.0 0.255.255.255',' rule 20 deny ip destination 172.16.0.0 0.15.255.255',' rule 25 deny ip destination 192.168.0.0 0.0.255.255',' rule 30 permit ip','traffic-filter vlan 140 inbound acl 3140'])
para('（四）IPsec 备用通道','h2')
para('HEALTH-R 与 TELEMED-GW 的 GE0/0/2 构成 198.18.0.0/30 底层。两端使用匹配的 IKE 提议、对等体、预共享密钥与 IPsec 提议，保护 172.20.1.0/24 和 10.162.121.0/24 之间的流量。该镜像实际支持 AES-256、SHA-1 与 DH group14；主路径经医疗专线及园区骨干，备用路径由静态路由和 NQA 控制。')
code('IPsec 绑定与路由示例',['ipsec policy HOSP 10 isakmp',' security acl 3500',' ike-peer HOSP',' proposal HOSP','interface GigabitEthernet0/0/2',' ipsec policy HOSP'])
para('保存设备配置后再次停止并启动工程，核对 34 台网络设备的系统标识均保持正确；两台核心各有 14 个 Full 状态的 OSPF 邻居，防火墙维持主、备角色。另复核门诊业务、公网 NAT、访客隔离、医疗会诊、堡垒机及 DMZ 实地址网关等 7 项场景，均符合预期；首次 ARP 解析引起的个别超时保留在原始输出中。')
para('五、连通性与安全验证','h1')
mp=ROOT/'evidence/test-matrix.json';tests=json.loads(mp.read_text(encoding='utf-8')) if mp.exists() else []
if tests:
    passed=sum(x['passed'] for x in tests);para(f'以下为本次逐终端发送 ICMP 的结果，共记录 {len(tests)} 个测试场景，其中 {passed} 项符合预期。每个场景的原始终端输出与对应截图单独保存，接收到的报文数按终端统计记录。禁止项同时结合入口抓包和 ACL 配置定位，不把不存在路由导致的超时单独视为隔离证明。')
    table('端到端 ICMP 测试矩阵',['来源与测试','目的地址','预期 / 实测'],[[x['source']+'\n'+x['description'],x['destination'],('允许' if x['expected'] else '禁止')+f' / 收到 {x["received"]} 包\n'+('符合预期' if x['passed'] else '待排查')] for x in tests])
    para('以下逐终端列出矩阵对应的全部测试命令。在 eNSP 对应 PC 的命令行窗口执行；禁止访问项预期超时。测试包数以原始记录为准。')
    for src in dict.fromkeys(x['source'] for x in tests):
        commands=['ipconfig']
        for x in tests:
            if x['source']==src:
                match=re.search(r'_-c_(\d+)',x.get('evidence',''))
                commands.append('ping '+x['destination']+' -c '+(match.group(1) if match else '2'))
        code(src+' 全部终端检查与测试命令',commands)
    selected=[('GUEST-PC','10.162.106.10'),('GUEST-PC','203.0.113.10'),('OPD-PC','10.162.106.10'),('OPD-PC','10.162.104.10'),('HEALTH-PC','10.162.121.10'),('BRANCH-PC','10.162.106.10'),('BASTION','10.162.99.65')]
    for src,dst in selected:
        found=next((x for x in tests if x['source']==src and x['destination']==dst),None)
        if found:figure(found['image'],found['description']+' 的终端测试')
para('ICMP 只能验证诊断流量和部分隔离行为。TCP/443、TCP/80、设备管理协议及指定平台业务端口的规则，应分别通过应用连接或专门构造的相应协议流量验证；未产生此类业务流量的项目不据此宣称应用测试通过。')
events=ROOT/'evidence/failover-results.json'
if events.exists():
    para('（一）冗余与备用链路测试','h2');ev=json.loads(events.read_text(encoding='utf-8'))
    for x in ev:
        para(x['description']);
        if x.get('image'):figure(x['image'],x['title'])
    para('（二）故障注入与恢复的完整操作命令','h2')
    para('以下命令按标题中的设备分别执行，每项测试完成后立即恢复原接口。交换机接口关闭后至少等待 15 秒再执行恢复；防火墙角色切换等待约 12 秒，恢复后等待约 30 秒观察抢占。等待及切换窗口属于人工操作，不作为设备命令输入。')
    for title,commands in [
        ('CORE-SW1：核心 VRRP 故障注入',['system-view','interface Vlanif4094','shutdown','return']),
        ('CORE-SW2：查看接管与业务连通',['display vrrp brief','ping -c 2 10.162.106.10']),
        ('CORE-SW1：恢复核心 VRRP 接口',['system-view','interface Vlanif4094','undo shutdown','return']),
        ('CORE-SW1：聚合单成员关闭与检查',['system-view','interface GigabitEthernet0/0/23','shutdown','return','display eth-trunk 1','ping -c 2 -a 10.162.99.66 10.162.99.67']),
        ('CORE-SW1：恢复聚合成员',['system-view','interface GigabitEthernet0/0/23','undo shutdown','return','display eth-trunk 1']),
        ('FW-A：关闭内联接口触发主备切换',['system-view','interface GigabitEthernet0/0/3','shutdown','return']),
        ('FW-B：确认接管',['display hrp state','display hrp interface']),
        ('OPD-PC：建立切换后的新公网会话',['ping 203.0.113.10 -c 3']),
        ('FW-B：查看新会话转换',['display firewall session table verbose']),
        ('FW-A：恢复原主设备接口',['system-view','interface GigabitEthernet0/0/3','undo shutdown','return','display hrp state']),
        ('HEALTH-R：关闭医疗专线主接口',['system-view','interface GigabitEthernet0/0/0','shutdown','return']),
        ('HEALTH-PC：触发备用加密流量',['ping 10.162.121.10 -c 3']),
        ('HEALTH-R：检查备用路由及加密 SA',['display ip routing-table 10.162.121.10','display ipsec sa']),
        ('HEALTH-R：恢复医疗专线',['system-view','interface GigabitEthernet0/0/0','undo shutdown','return']),
        ('AGG-CLINIC：关闭主核心上联并检查路由',['system-view','interface GigabitEthernet0/0/23','shutdown','return','display ip routing-table 10.162.106.10']),
        ('OPD-PC：检查经备用核心的业务连通',['ping 10.162.106.10 -c 3']),
        ('AGG-CLINIC：恢复主核心上联',['system-view','interface GigabitEthernet0/0/23','undo shutdown','return','display ospf peer brief'])
    ]:code(title,commands)
para('六、Wireshark 抓包与分析','h1')
para('从 eNSP 的设备右键“数据抓包”选择具体接口，由 Wireshark 通过标准输入接收该仿真链路的真实以太网帧，停止后保存为 pcapng。使用具体链路而非仅抓取 Host-only 外层 UDP，可直接分析 OSPF、VRRP、ICMP、NAT 和 ESP。截图保留过滤器、报文列表和报文详情。')
cp=ROOT/'evidence/capture-manifest.json';captures=json.loads(cp.read_text(encoding='utf-8')) if cp.exists() else []
for i,x in enumerate(captures,1):
    para(f'（{["一","二","三","四","五","六","七","八"][i-1]}）{x["title"]}','h2');para(x['analysis']);code('Wireshark 显示过滤器',x['filter']);figure(x['image'],x['title']+' 的 Wireshark 界面')
    para('抓包文件：'+Path(x['file']).name+'。')
para('七、问题处理与结果边界','h1')
para('1. 设备接口映射必须服从实际镜像。旧工程把部分 S5700 端口写为 Ethernet，本次按实际 GE 接口重新建立连接表，并在控制台核对接口名称、链路状态和 VLAN。','h3')
para('2. 双防火墙的心跳接口使用当前镜像可运行的组播 HRP 配置。早先指定 remote 地址时出现 peerdown 和双主，修正后以 MASTER/SLAVE、心跳 running 与抓包通告共同确认。','h3')
para('3. 该交换机镜像将 VLANIF 下的 traffic-filter 解析为全局过滤，会误伤骨干流量。本次改用全局视图中的 traffic-filter vlan <VLAN> inbound acl <编号>，使过滤范围明确落到业务 VLAN。','h3')
para('4. 同网段 NAT 地址池在两台旧版防火墙上可能产生竞争 ARP。本次为主备设备划分互不重叠的子池，完整覆盖 .10—.30；控制台会话表及公网往返抓包用于核对实际源地址转换。新会话恢复与已有会话无损延续属于不同验收项，后者不能仅凭 HRP 主备状态推断。','h3')
para('5. 终端初次访问会触发 ARP 解析、MAC 学习及路由收敛，可能出现首包超时。测试保留首次输出，预热后复测；失败案例不直接改写成零丢包。','h3')
para('6. 实验过程中客户端曾异常退出，随后重新打开独立工程并重新下发、检查配置。交付以最后保存的工程、启动配置及最终验证为依据，早期未保存的状态不作为重启复现的证明。','h3')
para('7. 本次通过链路抓包确认旧版 USG5500 的虚拟 MAC 收包存在兼容性限制。医疗专线使用 NQA 与接口实地址下一跳解决主备转发，DMZ 使用当前主设备实地址网关。HRP 角色切换和公网新建会话均已验证，但不把它们扩展表述为 DMZ 自动切换或既有应用会话无损迁移。','h3')
para('8. 冷启动时发现独立 /30 上联仍受默认 MSTP 实例控制，汇聚到第二核心的端口被置为 DISCARDING，造成该方向 OSPF 邻居缺失。对核心—汇聚的独立三层点到点承载端口设置 stp disable；核心互联与接入聚合仍保留生成树。修正后两条上联邻居均达到 Full，并实际关闭门诊汇聚的主核心上联，核对经第二核心到达业务服务器后恢复。','h3')
code('独立三层骨干端口的生成树处理',['system-view','interface GigabitEthernet0/0/24','stp disable','quit','return'])
figure(ROOT/'evidence/screenshots/routed-uplink-corrected.png','独立三层上联修正后的生成树与双核心 OSPF 邻居')
para('八、实验结论','h1')
para('本项目将医院园区业务映射到双边界、双核心、七汇聚与十八接入的实际工程，建立了分层寻址、跨区域 OSPF、链路聚合及分区访问控制。网络连通、安全隔离与备用路径的结论分别对应控制台、终端和抓包证据；端口规则、应用服务以及会话连续性按实际测试范围表述。')
para('完整配置清单、92 条设备链路表、原始控制台输出与 pcapng 随工程一并归档。拓扑中的所有物理链路采用仿真铜缆，不把线条加粗误标为实际光纤；LACP 成员关系和 IPsec 逻辑保护关系均单独说明。')
OUT.mkdir(exist_ok=True);tmp=OUT/'report-generated.docx';doc.save(tmp)
# Preserve all original package parts except the edited document and image relationships.
final=OUT/'13-2-01-宋长宇.docx'
with zipfile.ZipFile(SRC) as zin,zipfile.ZipFile(tmp) as gen,zipfile.ZipFile(final,'w',zipfile.ZIP_DEFLATED) as z:
    replace={'word/document.xml','word/_rels/document.xml.rels','word/settings.xml','[Content_Types].xml'}
    for item in zin.infolist():z.writestr(item,gen.read(item.filename) if item.filename in replace else zin.read(item.filename))
    oldparts=set(zin.namelist())
    for name in gen.namelist():
        if name not in oldparts:z.writestr(name,gen.read(name))
qa={'reference_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'figures':FIG,'tables':TAB,'devices':len(order),'test_cases':len(tests),'full_device_configs':len(FULL_CONFIG_AUDIT),'full_config_lines':sum(x['lines'] for x in FULL_CONFIG_AUDIT),'output':str(final)}
(ROOT/'evidence/full-config-report-audit.json').write_text(json.dumps(FULL_CONFIG_AUDIT,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'evidence/report-build.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(qa,ensure_ascii=False))
