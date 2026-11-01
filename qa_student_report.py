from pathlib import Path
import json,re,zipfile
from docx import Document
from PIL import Image,ImageDraw
import pymupdf
R=Path(__file__).parent;P=R/'output/13-2-01-宋长宇';name='13-2-01-宋长宇'
d=Document(P/(name+'.docx'));pdf=pymupdf.open(R/'evidence/render-real-topology'/(name+'.pdf'))
baseline=pymupdf.open(R/'evidence/render-user-before-conclusion'/(name+'.pdf'))
for i in range(2):assert pdf[i].get_pixmap().samples==baseline[i].get_pixmap().samples
audit=json.loads((R/'evidence/full-config-report-audit.json').read_text(encoding='utf8'));proof=[]
compact=lambda s:re.sub(r'\s+','',s)
for a in audit:
 t=next(t for t in d.tables if t.cell(0,0).text==a['title'])
 raw=Path(a['source']).read_text(encoding='utf8').replace('\r','');source='\n'.join(s for s in raw.splitlines() if s.strip() and set(s.strip())!={'#'})
 assert '\n'.join(p.text for p in t.cell(1,0).paragraphs)==source
 pages=[i for i,p in enumerate(pdf) if a['title'] in p.get_text()]
 rendered=''.join(pdf[i].get_text().replace(a['title'],'') for i in pages)
 assert compact(source) in compact(rendered),a['name']
 proof.append(dict(name=a['name'],complete_code=True,pages=[i+1 for i in pages]))
O=R/'evidence/student-voice-qa';O.mkdir(exist_ok=True)
for start in range(0,len(pdf),20):
 im=Image.new('RGB',(1500,2250),'#ccc');dr=ImageDraw.Draw(im)
 for i in range(start,min(start+20,len(pdf))):
  thumb=Image.open(R/f'evidence/render-real-topology/page-{i+1}.png').convert('RGB');thumb.thumbnail((365,420));col=(i-start)%4;row=(i-start)//4;im.paste(thumb,(col*375+(375-thumb.width)//2,row*450+24));dr.text((col*375+8,row*450+5),str(i+1),fill='black')
 im.save(O/f'contact-{start+1:03}.jpg',quality=90)
result=dict(pages=len(pdf),first_two_pages_unchanged=True,full_devices=len(proof),full_config_lines=sum(a['lines'] for a in audit),devices=proof)
(R/'evidence/student-report-qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('All 34 device configurations complete in DOCX and PDF; template first two pages unchanged; pages:',len(pdf))
