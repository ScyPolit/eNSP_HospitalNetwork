from pathlib import Path
import json,shutil,csv,zipfile,hashlib,re
import pymupdf
R=Path(__file__).parent;P=R/'output/13-2-01-宋长宇';P.mkdir(exist_ok=True)
j=json.loads((R/'lab_inventory.json').read_text(encoding='utf-8'));D={d['name']:d for d in j['devices']}
build_info=json.loads((R/'evidence/report-build.json').read_text(encoding='utf8'))
def copy(src,dst):
 dst=Path(dst);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
copy(R/'output/13-2-01-宋长宇.docx',P/'13-2-01-宋长宇.docx')
pdf=pymupdf.open(R/'evidence/render-real-topology/13-2-01-宋长宇.pdf');pdf.xref_set_key(pdf.pdf_catalog(),'OpenAction',f'[{pdf.page_xref(0)} 0 R /XYZ null null 1.2]');pdf.save(P/'13-2-01-宋长宇.pdf',garbage=4,deflate=True);pages=len(pdf);pdf.close()
for f in (R/'output/医院园区网/配置').glob('*-running.cfg'):copy(f,P/'配置'/f.name)
for f in (R/'evidence/screenshots').glob('*.png'):copy(f,P/'证据/控制台与抓包界面'/f.name)
for f in (R/'evidence/diagrams').glob('*.png'):
 obsolete=P/'拓扑图/分区详图'/f.name
 if obsolete.is_file():obsolete.unlink()
for f in (R/'evidence/topology-real').rglob('*'):
 if f.is_file():copy(f,P/'拓扑图/真实截图'/f.relative_to(R/'evidence/topology-real'))
copy(R/'evidence/topology-real/全网拓扑.png',P/'拓扑图/医院园区网-高清真实拓扑.png')
copy(R/'evidence/topology-image-quality.json',P/'验收记录/拓扑图片无损核对.json')
copy(R/'evidence/screenshots/医院园区网-一屏中文分区拓扑.png',P/'拓扑图/医院园区网-一屏中文分区拓扑.png')
copy(R/'evidence/screenshots/eNSP完整窗口.png',P/'拓扑图/eNSP完整窗口.png')
manifest=json.loads((R/'evidence/capture-manifest.json').read_text(encoding='utf8'))
for x in manifest:copy(x['file'],P/'证据/原始抓包'/Path(x['file']).name)
tests=json.loads((R/'evidence/test-matrix.json').read_text(encoding='utf8'));events=json.loads((R/'evidence/failover-results.json').read_text(encoding='utf8'));final=json.loads((R/'evidence/final-validation.json').read_text(encoding='utf8'))
for x in tests+events+final['tests']:
 if x.get('image') and Path(x['image']).exists():copy(x['image'],P/'证据/终端与故障切换'/Path(x['image']).name)
for f in (R/'evidence/console').glob('*.txt'):copy(f,P/'证据/原始控制台记录'/f.name)
for f in ['test-matrix.json','failover-results.json','final-validation.json','persistence.json','report-build.json','capture-manifest.json','backup-core-test.json','full-config-report-audit.json','full-config-completeness.json']:copy(R/'evidence'/f,P/'验收记录'/f)
backup=json.loads((R/'evidence/backup-core-test.json').read_text(encoding='utf8'))
if Path(backup['image']).exists():copy(backup['image'],P/'证据/终端与故障切换'/Path(backup['image']).name)
# Package evidence references remain usable after extracting on another computer.
def portable(value):
 if isinstance(value,list):return [portable(x) for x in value]
 if isinstance(value,dict):return {k:portable(v) for k,v in value.items()}
 if isinstance(value,str) and (':\\' in value or ':/' in value):
  base=Path(value).name
  matches=[x for x in P.rglob(base) if x.is_file()]
  if matches:return matches[0].relative_to(P).as_posix()
 return value
for f in (P/'验收记录').glob('*.json'):
 value=json.loads(f.read_text(encoding='utf8'));f.write_text(json.dumps(portable(value),ensure_ascii=False,indent=2),encoding='utf8')
copy(R/'lab_inventory.json',P/'验收记录/设备与链路原始清单.json')
def csvout(name,heads,rows):
 with (P/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(heads);w.writerows(rows)
csvout('设备清单.csv',['中文设备名','系统标识','型号','控制台端口','终端地址','默认网关'],[[d['display_name'],d['name'],d['model'],d.get('port',''),d.get('ip',''),d.get('gw','')] for d in j['devices']])
def iface(n,i):return 'GE0/0/'+str(i+1 if D[n]['model'] in ['S5700','PC'] else i)
def role(s):
 for a,b in [('Public HTTP/ICMP','主公网测试'),('Backup public','备用公网测试'),('Medical external','医疗专线外部网络'),('HRP heartbeat','双机热备心跳'),('Published DMZ service','非军事区服务终端'),('DMZ standby','非军事区备用接入'),('Management bastion','运维堡垒机接入'),('IPsec underlay','加密通道底层'),('Telemed inside','远程医疗院内侧'),('Telemedicine LAN','远程会诊局域网'),('Area0 P2P','区域零点到点'),('Access','业务接入'),('Guest','访客接入'),('Trust','信任区'),('DMZ','非军事区'),('WAN','外联'),('LACP','链路聚合'),('member','成员')]:s=s.replace(a,b)
 return s
csvout('链路清单.csv',['序号','源设备','源系统标识','源接口','目的设备','目的系统标识','目的接口','链路用途'],[[i,D[l['a']]['display_name'],l['a'],iface(l['a'],l['ai']),D[l['b']]['display_name'],l['b'],iface(l['b'],l['bi']),role(l['role'])] for i,l in enumerate(j['links'],1)])
csvout('测试结果.csv',['序号','场景','源终端','目的地址','预期','实收包数','结论'],[[i,t['description'],D[t['source']]['display_name'],t['destination'],'允许' if t['expected'] else '禁止',t['received'],'通过' if t['passed'] else '未通过'] for i,t in enumerate(tests,1)])
readme=f'''医院园区网 eNSP 实验交付说明

一、打开工程
打开“工程\\13-2-01-宋长宇.topo”。必须保留旁边的 34 个设备编号文件夹，不能只复制 .topo 文件。
平台为经典 eNSP 1.3.00.100、VirtualBox 5.2.26；使用本机已注册的 S5700、AR2220、USG5500 镜像。
工程中 58 台设备、92 条铜缆链路；设备中文显示名与 CLI 的英文系统标识对应关系见“设备清单.csv”。
当前电脑已按一屏总览调整。若重新打开后缩放被客户端重置，请点击工具栏“缩小”约五次；总览图同时提供全尺寸 PNG。
全选设备后启动，待 OSPF、HRP 和链路聚合收敛。停机前先在设备中 save，再在 eNSP 中保存工程，确保启动配置导出到设备文件夹。

二、图纸与报告
“拓扑图”包含一屏总览及十三张真实拓扑截图。报告正文全部使用当前 eNSP 界面截图，原绘制示意图已替换。
软件最大缩放倍率下获取屏幕像素；总览通过九张屏幕截图按滚动位置拼接，其余十二张均为单张截图直接裁切。七个业务区各占一页。
高清总览宽约 4700 像素；保留无损 PNG，DOCX 关闭自动图片压缩，PDF 中十三张拓扑图已逐像素核对。未重绘或生成设备、链路和文字。
“真实截图\\原始屏幕截图”及“截图来源.json”保留取图来源，便于核查。
十三个浅色块划分外联、安全、核心、业务区及读图说明；24 个终端旁标注实际 IP，区域内注明 VLAN、网关、掩码及关键骨干地址。
所有图中物理连接均为仿真铜缆。两条聚合成员具有相同设备端点，eNSP 会将其绘在相同走向上；双核心上联在核心附近保留必要交叉。
报告 DOCX/PDF 共 {pages} 页，从模板第三页开始填写；原前两页保留。包括逐设备实时控制台、真实终端测试、故障切换及 Wireshark 三窗格截图。
报告正文逐台粘贴全部 34 台网络设备的最终完整配置，共 {build_info['full_config_lines']} 行，已去除独占一行的井号分隔符及空行；命令和密码密文有效字符保留，不以关键片段替代。原始配置文件保留设备导出格式。另列逐设备检查命令、全部 30 项终端测试命令，以及故障注入与恢复命令。

三、验收结果
原验收矩阵 30/30 场景通过；另有重启后的 7 项连通和隔离复核通过。
34 台网络设备的启动后系统标识全部核对；两台核心各有 14 个 Full OSPF 邻居，防火墙主备为 MASTER/SLAVE。
主汇聚上联关闭时，门诊经备用核心到 HIS 的 3 包测试全部回复，随后恢复。
“配置”包含 34 份最终实际运行配置；“证据”提供原始抓包、控制台记录及截图；逐端口连接以“链路清单.csv”为准。

四、实际验证边界
服务器使用 eNSP 终端代表，未部署真实 HTTP/HTTPS/数据库应用；端口策略配置不等于应用服务测试通过。
已验证防火墙切换后新建 NAT 会话恢复，未证明既有业务会话无损迁移。
受当前 USG5500 镜像虚拟 MAC 收包兼容性影响，非军事区服务终端使用 10.162.108.2 实地址网关；其端到端自动主备切换仍待验证。
医疗专线使用接口实地址主备下一跳和 NQA；远程会诊 IPsec 备用链路有真实 ESP 抓包。
'''
(P/'使用说明.txt').write_text(readme,encoding='utf-8-sig')
files=[]
for f in sorted(P.rglob('*')):
 if f.is_file() and f.name!='SHA256SUMS.txt':files.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(P).as_posix()}')
(P/'SHA256SUMS.txt').write_text('\n'.join(files)+'\n',encoding='utf-8')
z=R/'output/13-2-01-宋长宇.zip'
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as q:
 for f in P.rglob('*'):
  if f.is_file():q.write(f,Path(P.name)/f.relative_to(P))
print(json.dumps(dict(directory=str(P),zip=str(z),pages=pages,files=len(files)),ensure_ascii=False))
