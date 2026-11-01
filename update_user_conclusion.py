from pathlib import Path
from copy import deepcopy
import zipfile,shutil,json,hashlib
from lxml import etree as E
R=Path(__file__).parent
src=R/'output/hospital-network/report.docx'
backup=R/'output/历史版本/用户微调版修改结论之前';backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(src,backup/src.name)
pdf=src.with_suffix('.pdf')
if pdf.exists():shutil.copy2(pdf,backup/pdf.name)
text='通过本次医院园区网实验，我完成了由双出口、双防火墙、双核心、七台汇聚及十八台接入交换机构成的网络部署，将 58 台设备和 92 条物理链路组织为层次清晰、业务分区明确的园区网络。实验综合运用 VLAN、OSPF、链路聚合、VRRP、HRP、DHCP、ACL、NAT 与 IPsec，实现了业务互通、分区访问控制及部分故障场景下的备用路径转发。30 项连通性与隔离测试及重启后的 7 项复核均符合预期，并通过真实控制台输出和 Wireshark 抓包相互印证。在排查接口映射、生成树阻塞、ACL 生效范围和虚拟 MAC 兼容性等问题的过程中，我进一步理解了二层交换、三层路由与安全策略之间的关系，掌握了按链路、地址、路由和策略逐层定位故障的方法。本实验验证了所设计网络在已测场景中的可行性，同时认识到配置正确仍需实际流量验证；真实应用服务、既有会话无损迁移及 DMZ 自动切换仍需进一步测试。'
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};w='{'+ns['w']+'}'
with zipfile.ZipFile(src) as z:
    original={i.filename:z.read(i.filename) for i in z.infolist()};infos=z.infolist()
root=E.fromstring(original['word/document.xml']);body=root.find(w+'body')
paras=body.findall(w+'p');head=next(p for p in paras if ''.join(p.itertext()).replace(' ','')=='八、实验结论')
following=[]
for node in list(body)[list(body).index(head)+1:]:
    if node.tag==w+'p' and ''.join(node.itertext()).strip():following.append(node)
assert len(following)==2
p=following[0];ppr=p.find(w+'pPr');run=p.find(w+'r');rpr=deepcopy(run.find(w+'rPr')) if run is not None and run.find(w+'rPr') is not None else None
for node in list(p):
    if node is not ppr:p.remove(node)
r=E.SubElement(p,w+'r')
if rpr is not None:r.append(rpr)
t=E.SubElement(r,w+'t');t.text=text
body.remove(following[1])
updated=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
temp=src.with_name('结论修改临时.docx')
with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as z:
    for i in infos:z.writestr(i,updated if i.filename=='word/document.xml' else original[i.filename])
temp.replace(src)
with zipfile.ZipFile(src) as z:
    changed=[n for n in original if z.read(n)!=original[n]]
assert changed==['word/document.xml']
baseline=E.fromstring(original['word/document.xml']);bp=baseline.find(w+'body');hp=next(p for p in bp.findall(w+'p') if ''.join(p.itertext()).replace(' ','')=='八、实验结论')
assert [E.tostring(n) for n in list(bp)[:list(bp).index(hp)+1]]==[E.tostring(n) for n in list(body)[:list(body).index(head)+1]]
shutil.copy2(src,R/'output/hospital-network.docx')
audit=dict(source=str(src),backup=str(backup/src.name),changed_parts=changed,preceding_body_unchanged=True,all_other_package_parts_unchanged=True,conclusion=text)
(R/'evidence/user-conclusion-edit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print('Only two conclusion paragraphs replaced with one summary paragraph; all other package parts and preceding content unchanged.')
