from pathlib import Path
import pymupdf,json,io
from PIL import Image,ImageChops
R=Path(__file__).parent;O=R/'evidence/topology-real';out=R/'evidence/render-real-topology';src=out/'report.pdf'
names=['全网拓扑','医疗专线区','主公网与外联交换区','备用公网区','边界防火墙与双核心区','非军事区','门急诊与药房区','住院病区','医技影像检验区','数据中心与备份区','行政财务与运维区','医疗物联与无线区','分院与远程医疗区']
doc=pymupdf.open(src);found=[]
for i in range(2,len(doc)):
 for im in sorted(doc[i].get_image_info(xrefs=True),key=lambda x:(x['bbox'][1],x['bbox'][0])):
  found.append((i,im))
  if len(found)==13:break
 if len(found)==13:break
assert len(found)==13
audit=[]
for n,(i,im) in zip(names,found):
 f=O/(n+'.png');actual=Image.open(f).convert('RGB');assert abs(actual.width/actual.height-im['width']/im['height'])<.006,(n,im)
 doc[i].replace_image(im['xref'],filename=str(f))
 b=doc.extract_image(im['xref']);decoded=Image.open(io.BytesIO(b['image'])).convert('RGB');assert ImageChops.difference(actual,decoded).getbbox() is None,n
 audit.append(dict(name=n,page=i+1,pixels=list(actual.size),lossless_pixel_match=True))
tmp=out/'无损拓扑图.pdf';doc.save(tmp,garbage=4,deflate=True);doc.close();tmp.replace(src)
doc=pymupdf.open(src)
for i in sorted({i for i,_ in found}):doc[i].get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(out/f'page-{i+1}.png')
(R/'evidence/topology-image-quality.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
print('13 PDF topology images retain exact screenshot pixels')
