from pathlib import Path
import json,zipfile,hashlib,shutil
from lxml import etree as E
import pymupdf
R=Path(__file__).parent;P=R/'output/hospital-network';name='report'
src=P/(name+'.docx');old=R/'output/历史版本/用户微调版修改结论之前'/(name+'.docx')
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};w='{'+ns['w']+'}'
with zipfile.ZipFile(old) as a,zipfile.ZipFile(src) as b:
 assert a.namelist()==b.namelist()
 assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['word/document.xml']
 roots=[E.fromstring(z.read('word/document.xml')) for z in [a,b]]
 bodies=[rt.find(w+'body') for rt in roots]
 indexes=[next(i for i,n in enumerate(body) if n.tag==w+'p' and ''.join(n.itertext()).replace(' ','')=='八、实验结论') for body in bodies]
 assert [E.tostring(n) for n in list(bodies[0])[:indexes[0]+1]]==[E.tostring(n) for n in list(bodies[1])[:indexes[1]+1]]
 assert [E.tostring(t) for t in roots[0].findall('.//w:tbl',ns)]==[E.tostring(t) for t in roots[1].findall('.//w:tbl',ns)]
before=pymupdf.open(R/'evidence/render-user-before-conclusion'/(name+'.pdf'));after=pymupdf.open(R/'evidence/render-real-topology'/(name+'.pdf'))
assert len(before)==len(after)==122
changed=[i+1 for i in range(len(before)) if before[i].get_pixmap().samples!=after[i].get_pixmap().samples]
assert changed==[122],changed
after.close();before.close()
print('Latest user formatting preserved; all tables unchanged; only PDF page 122 differs.')
