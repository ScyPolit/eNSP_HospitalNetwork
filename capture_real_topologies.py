"""Lossless panorama from actual eNSP viewport screenshots, without redrawing."""
from pathlib import Path
import time,json,math
import pyautogui as p
import native_ui as ui
import win32gui,win32con
from PIL import Image,ImageChops
from lab_ui import focus

R=Path(__file__).parent;O=R/'evidence/topology-real';RAW=O/'原始屏幕截图';RAW.mkdir(parents=True,exist_ok=True)
focus();p.click(412,72);p.moveTo(1800,500);p.dragTo(1820,520,.15);p.click(780,72)
for _ in range(4):p.click(688,72);time.sleep(.08)
p.moveTo(20,18);time.sleep(.25)
h=ui.canvas();rect=win32gui.GetWindowRect(h);z=1.1**4;scale=z*1.25
assert abs((win32gui.GetScrollInfo(h,0)[2]+1)/3000-z)<.002
vw,vh=2280,1200;left,top=rect[0]+5,rect[1]+5
W=math.ceil(2590*scale/5)*5;H=math.ceil(1365*scale/5)*5
xs=list(range(0,W-vw,2000))+[W-vw];ys=list(range(0,H-vh,1000))+[H-vh]
pan=Image.new('RGB',(W,H),'white');manifest=[];checks=[];lastrow={}
for row,y in enumerate(ys):
 for col,x in enumerate(xs):
  sx,sy=int(x/1.25),int(y/1.25)
  win32gui.SendMessage(h,win32con.WM_HSCROLL,win32con.SB_THUMBTRACK|(sx<<16),0)
  win32gui.SendMessage(h,win32con.WM_VSCROLL,win32con.SB_THUMBTRACK|(sy<<16),0)
  assert win32gui.GetScrollInfo(h,0)[4]==sx
  assert win32gui.GetScrollInfo(h,1)[4]==sy
  win32gui.RedrawWindow(h,None,None,win32con.RDW_INVALIDATE|win32con.RDW_UPDATENOW)
  time.sleep(.17)
  full=p.screenshot();f=RAW/f'屏幕-{row+1}-{col+1}.png';full.save(f)
  tile=full.crop((left,top,left+vw,top+vh))
  if col:
   overlap=xs[col-1]+vw-x
   a=previous.crop((vw-overlap,0,vw,vh));b=tile.crop((0,0,overlap,vh));diff=ImageChops.difference(a,b)
   import numpy as np
   aa=np.asarray(a);bb=np.asarray(b);match=float((aa==bb).all(axis=2).mean());checks.append(match)
  pan.paste(tile.crop((10,10,vw-10,vh-10)),(x+10,y+10));previous=tile
  manifest.append(dict(file=str(f.relative_to(R)),scroll=[sx,sy],panorama_origin=[x,y],viewport=[left,top,vw,vh]))
 print('captured row',row+1,flush=True)
pan.save(O/'全网拓扑-原生高倍率实景拼接.png')
def crop(name,box):
 b=tuple(round(v*scale) for v in box);pan.crop(b).save(O/(name+'.png'))
crop('全网拓扑',(10,10,2580,1360))
crop('医疗专线区',(10,10,530,330))
crop('主公网与外联交换区',(540,10,1260,330))
crop('备用公网区',(1260,10,1790,330))
crop('边界防火墙与双核心区',(880,325,1600,675))
crop('非军事区',(2090,10,2580,675))
names=['分院与远程医疗区','门急诊与药房区','住院病区','医技影像检验区','数据中心与备份区','行政财务与运维区','医疗物联与无线区']
for i,n in enumerate(names):crop(n,(10+i*365,700,385+i*365,1360))
(O/'截图来源.json').write_text(json.dumps(dict(software='eNSP V1.3.00.100',zoom=z,scale=scale,panorama_size=[W,H],method='实际屏幕截图按滚动位移无缩放拼接；未重绘、未锐化、未生成文字',horizontal_overlap_exact_pixel_ratios=checks,tiles=manifest),ensure_ascii=False,indent=2),encoding='utf-8')
print('Panorama',W,H,'overlap min',min(checks),flush=True)
# Restore the user's one-screen overview after capturing.
p.click(780,72)
for _ in range(4):p.click(736,72);time.sleep(.08)
win32gui.SendMessage(h,win32con.WM_HSCROLL,win32con.SB_TOP,0)
win32gui.SendMessage(h,win32con.WM_VSCROLL,win32con.SB_TOP,0)
p.moveTo(20,18)
