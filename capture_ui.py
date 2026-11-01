from pathlib import Path
import time,sys,json
import pyautogui as p
from lab_ui import paste,focus
from inspect_lab import shot
ROOT=Path(__file__).parent;CAP=ROOT/'evidence'/'pcaps';CAP.mkdir(parents=True,exist_ok=True)
def ws_focus():
    wins=[w for w in p.getAllWindows() if 'Wireshark' in w.title or 'Capturing from' in w.title or '.pcap' in w.title]
    active=[w for w in wins if 'Capturing from' in w.title]
    h=ROOT/'evidence'/'capture-active.json'
    tracked=[w for w in wins if h.exists() and w._hWnd==json.loads(h.read_text(encoding='utf-8'))['hwnd']]
    w=(tracked or active or wins)[0];p.press('alt')
    try:w.activate()
    except Exception:pass
    w.maximize();time.sleep(.3)
    return w
def save(name):
    w=ws_focus()
    if 'Capturing' in w.title:p.hotkey('ctrl','e');time.sleep(.6)
    p.hotkey('ctrl','shift','s');time.sleep(.7);paste(CAP/(name+'.pcapng'));p.press('enter');time.sleep(1.2)
    shot('ws-'+name)
    for _ in range(30):
        if (CAP/(name+'.pcapng')).exists():break
        time.sleep(.3)
    if not (CAP/(name+'.pcapng')).exists():raise RuntimeError('Capture file was not saved: '+name)
def filtershot(name,flt):
    ws_focus();p.click(450,110);p.hotkey('ctrl','a');paste(flt);p.press('enter');time.sleep(.5);p.click(450,170);time.sleep(.3);shot('ws-'+name)
if __name__=='__main__':
    if sys.argv[1]=='save':save(sys.argv[2])
    elif sys.argv[1]=='filter':filtershot(sys.argv[2],sys.argv[3])
