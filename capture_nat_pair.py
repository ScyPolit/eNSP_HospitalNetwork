from native_ui import *
from capture_ui import save
from lab_ui import focus
import shutil
for d in INV['devices']:
    if d['model']=='PC' and (h:=win32gui.FindWindow(None,d['name'])):win32gui.ShowWindow(h,win32con.SW_HIDE)
focus();x,y=device_point('ACC-OPD');capture_menu(x,y,'GE0/0/1');shutil.copyfile(ROOT/'evidence/capture-active.json',ROOT/'evidence/capture-inside.json')
focus();x,y=device_point('WAN-L2');capture_menu(x,y,'GE0/0/1')
open_device('OPD-PC');pc_command('OPD-PC','ping 203.0.113.10 -c 3',6);pc_command('OPD-PC','ping 203.0.113.10 -c 2',4);pcwin('OPD-PC').close()
save('09-NAT-final-outside');shutil.copyfile(ROOT/'evidence/capture-inside.json',ROOT/'evidence/capture-active.json');save('10-NAT-final-inside')
