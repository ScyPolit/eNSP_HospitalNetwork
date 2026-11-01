import pyautogui as p, time, win32clipboard as cb, sys
from pathlib import Path
from inspect_lab import shot
def paste(text):
    cb.OpenClipboard();cb.EmptyClipboard();cb.SetClipboardText(str(text));cb.CloseClipboard();p.hotkey('ctrl','v');time.sleep(.15)
def focus():
    w=p.getWindowsWithTitle('eNSP')[0]
    if w.isMinimized:w.restore()
    if not w.isMaximized:w.maximize()
    p.press('alt')
    try:w.activate()
    except Exception:pass
    time.sleep(.3)
def open_project(path):
    focus();p.hotkey('ctrl','o');time.sleep(.7);paste(path);p.press('enter');time.sleep(3);shot('project-open')
if __name__=='__main__':
    a=sys.argv[1]
    if a=='open':open_project(sys.argv[2])
    elif a=='shot':shot(sys.argv[2])
    elif a=='start':focus();p.click(826,72);time.sleep(2);shot('start-full')
    elif a=='stop':focus();p.click(872,72);time.sleep(1)
