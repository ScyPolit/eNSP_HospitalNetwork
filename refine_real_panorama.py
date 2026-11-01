from pathlib import Path
from PIL import Image
import json
O=Path(__file__).parent/'evidence/topology-real';R=Path(__file__).parent
m=json.loads((O/'截图来源.json').read_text(encoding='utf8'));pan=Image.new('RGB',m['panorama_size'],'white');scale=m['scale']
for t in m['tiles']:
 x,y=t['panorama_origin'];left,top,w,h=t['viewport'];im=Image.open(R/t['file']);pan.paste(im.crop((left+10,top+10,left+w-10,top+h-10)),(x+10,y+10))
pan.save(O/'全网拓扑-原生高倍率实景拼接.png')
boxes={'全网拓扑':(10,10,2580,1360),'医疗专线区':(10,10,530,330),'主公网与外联交换区':(540,10,1260,330),'备用公网区':(1260,10,1790,330),'边界防火墙与双核心区':(880,325,1600,675),'非军事区':(2090,10,2580,675)}
for i,n in enumerate(['分院与远程医疗区','门急诊与药房区','住院病区','医技影像检验区','数据中心与备份区','行政财务与运维区','医疗物联与无线区']):boxes[n]=(10+i*365,700,385+i*365,1360)
for n,b in boxes.items():pan.crop(tuple(round(v*scale) for v in b)).save(O/(n+'.png'))
m['viewport_border_excluded_px']=10;m['region_files']={n+'.png':dict(document_rectangle=b,pixel_size=list(Image.open(O/(n+'.png')).size)) for n,b in boxes.items()}
(O/'截图来源.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
print('Real-screen crops',len(boxes))
