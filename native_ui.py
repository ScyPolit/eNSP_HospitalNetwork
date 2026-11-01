import ctypes,time,json,sys
from pathlib import Path
import pyautogui as p
from pywinauto import Desktop
ctypes.windll.user32.SetThreadDpiAwarenessContext(ctypes.c_void_p(-4))
import win32gui,win32con
ROOT=Path(__file__).parent
INV=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'))
def canvas():
    result=[]
    def enum(hwnd,_):
        if win32gui.GetClassName(hwnd)=='AfxFrameOrView80su':result.append(hwnd)
    win32gui.EnumChildWindows(win32gui.FindWindow(None,'eNSP_Client'),enum,None)
    return result[0]
def device_point(name):
    d=next(d for d in INV['devices'] if d['name']==name);h=canvas()
    rect=win32gui.GetWindowRect(h);z=win32gui.GetScrollInfo(h,0)[2]/2999
    ox=rect[0]+5+32*z;oy=rect[1]+5+32*z;scale=1.25*z
    for bar,msg,pos in [(0,win32con.WM_HSCROLL,max(0,int((ox+scale*d['x']-1500)/1.25))),(1,win32con.WM_VSCROLL,max(0,int((oy+scale*d['y']-700)/1.25)))]:
        win32gui.SendMessage(h,msg,win32con.SB_TOP,0)
        info=win32gui.GetScrollInfo(h,bar);pos=min(pos,info[2]-info[3]+1)
        win32gui.SendMessage(h,msg,win32con.SB_LINEDOWN,0);step=win32gui.GetScrollInfo(h,bar)[4];win32gui.SendMessage(h,msg,win32con.SB_TOP,0)
        for _ in range(max(0,round(pos/max(1,step)))):win32gui.SendMessage(h,msg,win32con.SB_LINEDOWN,0)
    time.sleep(.15)
    sx=win32gui.GetScrollInfo(h,0)[4];sy=win32gui.GetScrollInfo(h,1)[4]
    return round(ox+scale*d['x']-sx*1.25),round(oy+scale*d['y']-sy*1.25)
def open_device(name):
    from lab_ui import focus
    title=next((d.get('display_name',name) for d in INV['devices'] if d['name']==name),name)
    h=win32gui.FindWindow(None,title)
    if h:
        win32gui.ShowWindow(h,win32con.SW_SHOWNORMAL)
        p.press('alt')
        try:win32gui.SetForegroundWindow(h)
        except Exception:pass
        time.sleep(.3);print(name,'opened native window');return
    focus();x,y=device_point(name);p.doubleClick(x,y,interval=.13);time.sleep(.3)
    print(name,x,y)
def pcwin(name):return Desktop(backend='win32').window(title=next((d.get('display_name',name) for d in INV['devices'] if d['name']==name),name))
def pc_command(name,command,seconds=5):
    w=pcwin(name);w.set_focus();r=w.rectangle();p.click(r.left+177,r.top+62);time.sleep(.2)
    rich=[x for x in w.descendants(class_name='RichEdit20A') if x.is_visible()][0]
    rich.set_focus();p.write(command,.01);p.press('enter');time.sleep(seconds)
    text=rich.window_text()
    if not text.rstrip().endswith('PC>'):p.hotkey('ctrl','c');time.sleep(.2)
    text=rich.window_text();(ROOT/'evidence'/'console'/f'{name}-{command.replace(" ","_")}.txt').write_text(text,encoding='utf-8')
    r=w.rectangle();im=p.screenshot(region=(r.left,r.top,r.width(),r.height()));out=ROOT/'evidence'/'live'/f'{name}-{command.replace(" ","_")}.png';im.save(out)
    print(text[text.rfind('PC>'+command):][-1400:]);return out
def capture_menu(x,y,iface,_retry=True):
    old={w._hWnd for w in p.getAllWindows()}
    p.click(x,y,button='right');time.sleep(.2)
    menus=[w for w in Desktop(backend='win32').windows() if w.class_name()=='#32768']
    menu=menus[0].menu();item=[i for i in menu.items() if i.text()=='数据抓包'][0]
    r=item.rectangle();p.click(round((r.left+r.right)*.625),round((r.top+r.bottom)*.625));time.sleep(.3)
    menus=[w for w in Desktop(backend='win32').windows() if w.class_name()=='#32768']
    for w in menus:
        for i in w.menu().items():
            if i.text().replace(' ','')==iface.replace(' ',''):
                r=i.rectangle();p.click(round((r.left+r.right)*.625),round((r.top+r.bottom)*.625))
                for _ in range(30):
                    time.sleep(.3)
                    ws=[w for w in p.getAllWindows() if w._hWnd not in old and ('Wireshark' in w.title or 'Capturing from' in w.title)]
                    if ws:
                        (ROOT/'evidence'/'capture-active.json').write_text(json.dumps({'hwnd':ws[0]._hWnd}),encoding='utf-8');return
                if _retry:return capture_menu(x,y,iface,False)
                raise RuntimeError('No new Wireshark capture window appeared')
    raise ValueError([(i.text(),str(i.rectangle())) for w in menus for i in w.menu().items()])
if __name__=='__main__':
    if sys.argv[1]=='pc':pc_command(sys.argv[2],sys.argv[3],float(sys.argv[4]) if len(sys.argv)>4 else 5)
    elif sys.argv[1]=='capture':capture_menu(int(sys.argv[2]),int(sys.argv[3]),sys.argv[4])
    elif sys.argv[1]=='open':open_device(sys.argv[2])
    elif sys.argv[1]=='scrollinfo':
        root=win32gui.FindWindow(None,'eNSP_Client')
        def enum(hwnd,_):
            for b in [0,1]:
                try:
                    s=win32gui.GetScrollInfo(hwnd,b)
                    if s[2]>0:print(hwnd,win32gui.GetClassName(hwnd),b,s,win32gui.GetWindowRect(hwnd))
                except:pass
        win32gui.EnumChildWindows(root,enum,None)
