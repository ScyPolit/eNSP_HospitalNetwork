from pathlib import Path
import math,time,json
import pyautogui as p,win32gui,win32con
import native_ui as ui
from lab_ui import focus
R=Path(__file__).parent;O=R/'evidence/topology-real';RAW=O/'原始屏幕截图';m=json.loads((O/'截图来源.json').read_text(encoding='utf8'))
focus();p.click(780,72)
for _ in range(4):p.click(688,72);time.sleep(.08)
p.moveTo(20,18);h=ui.canvas();r=win32gui.GetWindowRect(h);left,top=r[0]+5,r[1]+5;scale=(1.1**4)*1.25
boxes={'医疗专线区':(10,10,530,330),'主公网与外联交换区':(540,10,1260,330),'备用公网区':(1260,10,1790,330),'边界防火墙与双核心区':(880,325,1600,675),'非军事区':(2100,20,2565,660)}
for i,n in enumerate(['分院与远程医疗区','门急诊与药房区','住院病区','医技影像检验区','数据中心与备份区','行政财务与运维区','医疗物联与无线区']):boxes[n]=(12+i*365,710,377+i*365,1350)
for n,b in boxes.items():
 x0,y0,x1,y1=[v*scale for v in b];w,hg=x1-x0,y1-y0
 sx=round(((x0+x1)/2-1140)/1.25/4)*4;sy=round(((y0+y1)/2-600)/1.25/4)*4
 sx=max(0,min(sx,math.floor((win32gui.GetScrollInfo(h,0)[2]-1826+1)/4)*4));sy=max(0,min(sy,math.floor((win32gui.GetScrollInfo(h,1)[2]-963+1)/4)*4))
 win32gui.SendMessage(h,win32con.WM_HSCROLL,win32con.SB_THUMBTRACK|(sx<<16),0);win32gui.SendMessage(h,win32con.WM_VSCROLL,win32con.SB_THUMBTRACK|(sy<<16),0)
 win32gui.RedrawWindow(h,None,None,win32con.RDW_INVALIDATE|win32con.RDW_UPDATENOW);time.sleep(.16)
 check=p.screenshot()
 safe=None
 for yy in range(top+40,top+1160,45):
  for xx in range(left+40,left+2240,45):
   if check.crop((xx-12,yy-12,xx+12,yy+12)).convert('RGB').getextrema()==((255,255),(255,255),(255,255)):safe=(xx,yy);break
  if safe:break
 if safe:
  p.moveTo(*safe);p.dragRel(5,5,.12);time.sleep(.05);p.moveTo(20,18);time.sleep(.12)
 full=p.screenshot();source=RAW/('单区-'+n+'.png');full.save(source)
 crop=(round(left+x0-1.25*sx),round(top+y0-1.25*sy),round(left+x1-1.25*sx),round(top+y1-1.25*sy))
 assert crop[0]>=left+10 and crop[1]>=top+10 and crop[2]<=left+2280-10 and crop[3]<=top+1200-10,(n,crop)
 out=full.crop(crop);out.save(O/(n+'.png'));m['region_files'][n+'.png']=dict(source_screen=str(source.relative_to(O)),crop_pixels=crop,pixel_size=list(out.size),method='单张实际屏幕截图直接裁切，无拼接、无重绘、无插值放大')
 print(n,out.size,flush=True)
(O/'截图来源.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
p.click(780,72)
for _ in range(4):p.click(736,72);time.sleep(.08)
win32gui.SendMessage(h,win32con.WM_HSCROLL,win32con.SB_TOP,0);win32gui.SendMessage(h,win32con.WM_VSCROLL,win32con.SB_TOP,0);p.moveTo(20,18)
