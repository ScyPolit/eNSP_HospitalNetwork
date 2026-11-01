from pathlib import Path
import zipfile,json,shutil
from lxml import etree as E
R=Path(__file__).parent;p=R/'output/13-2-01-宋长宇/13-2-01-宋长宇.docx'
old='本实验验证了所设计网络在已测场景中的可行性，同时认识到配置正确仍需实际流量验证；真实应用服务、既有会话无损迁移及 DMZ 自动切换仍需进一步测试。'
new='本次实验完成了医院园区网的规划、设备配置、连通性与安全验证及实验资料整理，达到了网络分层部署、业务分区管理和冗余链路验证的实验目标，也提升了我综合运用网络知识解决实际问题的能力。'
with zipfile.ZipFile(p) as z:infos=z.infolist();parts={i.filename:z.read(i.filename) for i in infos}
root=E.fromstring(parts['word/document.xml']);ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
matches=[t for t in root.findall('.//w:t',ns) if t.text and old in t.text];assert len(matches)==1
matches[0].text=matches[0].text.replace(old,new);updated=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
tmp=p.with_name('结论修改临时.docx')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for i in infos:z.writestr(i,updated if i.filename=='word/document.xml' else parts[i.filename])
tmp.replace(p);shutil.copy2(p,R/'output/13-2-01-宋长宇.docx')
a=R/'evidence/user-conclusion-edit.json';j=json.loads(a.read_text(encoding='utf8'));j['conclusion']=matches[0].text;a.write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf8')
print('Conclusion now summarizes completed work and learning outcomes.')
