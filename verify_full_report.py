from pathlib import Path
import json,re,zipfile,collections
from docx import Document
from PIL import Image,ImageDraw,ImageChops
import pymupdf
R=Path(__file__).parent
audit=json.loads((R/'evidence/full-config-report-audit.json').read_text(encoding='utf8'))
inv=json.loads((R/'lab_inventory.json').read_text(encoding='utf8'))
doc=Document(R/'output/hospital-network.docx')
pdf=pymupdf.open(R/'evidence/render-real-topology/report.pdf')
records=[]
for x in audit:
    tables=[t for t in doc.tables if t.cell(0,0).text==x['title']]
    assert len(tables)==1,x['name']
    t=tables[0];assert len(t.rows)==2 and len(t.columns)==1
    code='\n'.join(p.text for p in t.cell(1,0).paragraphs)
    source=Path(x['source']).read_text(encoding='utf8').replace('\r','').rstrip('\n')
    compact_source='\n'.join(line for line in source.splitlines() if line.strip() and set(line.strip())!={'#'})
    assert code==compact_source,x['name']
    device=next(d for d in inv['devices'] if d['name']==x['name'])
    folder=R/'output/hospital-network/工程'/device['id']
    f=next(iter(folder.glob('vrpcfg.zip')),None) or next(folder.glob('flash.efz'))
    if zipfile.is_zipfile(f):
        with zipfile.ZipFile(f) as z:saved=z.read(next(n for n in z.namelist() if n.endswith('vrpcfg.cfg'))).decode('utf8',errors='replace')
    else:
        saved=f.read_bytes().decode('utf8',errors='replace').split('#*****BEGIN****public****#',1)[1].split('#-----END----#',1)[0]
    def commands(s):return collections.Counter(line.strip() for line in s.replace('\x00','').splitlines() if line.strip() and not line.strip().startswith(('#','[')))
    assert commands(source)==commands(saved),x['name']
    pages=[i+1 for i,p in enumerate(pdf) if x['title'] in p.get_text()]
    assert pages,x['name']
    rendered=''.join(pdf[i-1].get_text().replace(x['title'],'') for i in pages)
    compact=lambda s:re.sub(r'\s+','',s)
    assert compact(compact_source) in compact(rendered),x['name']
    records.append(dict(name=x['name'],lines=x['lines'],original_lines=x['original_lines'],removed_separator_or_blank_lines=x['removed_separator_or_blank_lines'],docx_matches_source_without_separators=True,pdf_complete_in_order=True,startup_command_match=True,pages=pages))
template=pymupdf.open(R/'evidence/template-render/report.pdf')
for i in range(2):assert pdf[i].get_pixmap().samples==template[i].get_pixmap().samples
with zipfile.ZipFile(R/'report-template.docx') as a,zipfile.ZipFile(R/'output/hospital-network.docx') as b:assert a.read('word/styles.xml')==b.read('word/styles.xml')
O=R/'evidence/full-code-qa';O.mkdir(exist_ok=True)
for start in range(0,len(pdf),20):
    sheet=Image.new('RGB',(1500,5*450),'#ccc');draw=ImageDraw.Draw(sheet)
    for k in range(start,min(start+20,len(pdf))):
        im=Image.open(R/f'evidence/render-real-topology/page-{k+1}.png').convert('RGB');im.thumbnail((365,420))
        col=(k-start)%4;row=(k-start)//4;sheet.paste(im,(col*375+(375-im.width)//2,row*450+24));draw.text((col*375+8,row*450+5),str(k+1),fill='black')
    sheet.save(O/f'contact-{start+1:03}.jpg',quality=90)
result=dict(pages=len(pdf),full_devices=len(records),full_lines=sum(x['lines'] for x in records),first_two_pages_pixel_match=True,template_styles_unchanged=True,devices=records)
(R/'evidence/full-config-completeness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False))
