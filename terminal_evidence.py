from configure_lab import *
import tkinter as tk
import pyautogui as pg
import re,sys
OUT=ROOT/'evidence'/'screenshots';OUT.mkdir(parents=True,exist_ok=True)
def clean(t):
    t=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',t).replace('\r','').replace('\x00','')
    t=re.sub(r'\n\n+','\n',t)
    return t.strip()
def commands(n):
    if n.startswith('FW-'):return ['display current-configuration interface GigabitEthernet0/0/6','display hrp state','display hrp interface']
    if n.startswith('CORE-'):return ['display current-configuration interface Eth-Trunk1','display vrrp brief','display eth-trunk 1 | include Selected']
    if n.startswith('AGG-'):
        v=next(v for v,d in INV['vlans'].items() if d['agg']==n)
        return [f'display current-configuration interface Vlanif{v}','display ospf peer brief','display eth-trunk 1 | include Selected']
    if n in ['ISP-R1','ISP-R2','HEALTH-R','TELEMED-GW']:return ['display current-configuration interface GigabitEthernet0/0/0','display ip interface brief']
    if n in ['WAN-L2','DMZ-SW']:return ['display current-configuration interface GigabitEthernet0/0/1','display port vlan | include GE0/0']
    return ['display current-configuration interface Eth-Trunk1','display eth-trunk 1 | include Selected','display current-configuration interface GigabitEthernet0/0/1']
root=tk.Tk();root.geometry('1100x850+700+180');root.configure(bg='#102237');root.attributes('-topmost',True)
label=tk.Label(root,text='',bg='#102237',fg='white',font=('Microsoft YaHei',12),anchor='w');label.pack(fill='x',padx=15,pady=8)
box=tk.Text(root,bg='#101820',fg='#e3f1ea',insertbackground='white',font=('Consolas',12),wrap='char',bd=0,padx=16,pady=10);box.pack(fill='both',expand=True)
root.update()
for n,port in INV['ports'].items():
    if len(sys.argv)>1 and n not in sys.argv[1:]:continue
    try:
        title=next(d.get('display_name',n) for d in INV['devices'] if d['name']==n)
        root.title(f'eNSP Live Console | {n} | 127.0.0.1:{port}');label.configure(text=f'{title}（{n}）    TCP 127.0.0.1:{port}    实时设备控制台')
        box.delete('1.0','end');box.insert('end',f'Connected to eNSP device {n}\n')
        logs=[]
        with Console(port) as c:
            c.cmd('return')
            for cmd in commands(n):
                out=c.cmd(cmd);logs.append(out);box.insert('end',clean(out)+'\n');root.update()
        box.see('1.0');root.update();time.sleep(.15)
        linecount=int(box.index('end-1c').split('.')[0]);height=min(1000,max(350,100+linecount*22));root.geometry(f'1100x{height}+700+120');root.update();time.sleep(.15)
        x=root.winfo_rootx();y=root.winfo_rooty();w=root.winfo_width();h=root.winfo_height()
        pg.screenshot(region=(x,y,w,h)).save(OUT/f'{n}-CLI.png')
        (LOG/f'{n}-screen-session.txt').write_text('\n'.join(logs),encoding='utf-8')
        print(n,'screenshot',linecount,flush=True)
    except Exception as e:print(n,'ERROR',repr(e),flush=True)
root.destroy()
