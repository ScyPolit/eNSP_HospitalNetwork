from native_ui import *
from lab_ui import focus
from capture_ui import save
def ipval(s):
    a=list(map(int,s.split('.')));return (a[0]<<24)|(a[1]<<16)|(a[2]<<8)|a[3]
for dev in INV['devices']:
    if dev['model']=='PC' and (h:=win32gui.FindWindow(None,dev['name'])):win32gui.ShowWindow(h,win32con.SW_HIDE)
focus();x,y=device_point('ACC-WLAN');capture_menu(x,y,'GE0/0/2');open_device('GUEST-PC');w=pcwin('GUEST-PC');r=w.rectangle()
p.click(r.left+70,r.top+62);time.sleep(.2);p.click(r.left+200,r.top+236);p.click(r.left+880,r.top+617);time.sleep(5)
pic=pc_command('GUEST-PC','ipconfig',1)
save('08-DHCP-DORA')
# Restore the documented static address after demonstrating a real DHCP lease.
w.set_focus();r=w.rectangle();p.click(r.left+70,r.top+62);time.sleep(.2);p.click(r.left+80,r.top+236)
cs=[x for x in w.descendants(class_name='SysIPAddress32') if x.is_visible()]
for ctrl,addr in zip(cs,['10.162.116.10','255.255.252.0','10.162.116.1']):win32gui.SendMessage(ctrl.handle,win32con.WM_USER+101,0,ipval(addr))
p.click(r.left+880,r.top+617);time.sleep(.3);pc_command('GUEST-PC','ipconfig',1);w.close();print('DHCP demonstrated and static IP restored')
