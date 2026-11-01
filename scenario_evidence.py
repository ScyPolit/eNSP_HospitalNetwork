from configure_lab import *
import tkinter as tk,pyautogui as pg,sys
n,tag=sys.argv[1:3];cmds=sys.argv[3:];out=[]
root=tk.Tk();root.title(n+' | live verification');root.geometry('1100x900+700+100');root.attributes('-topmost',True)
box=tk.Text(root,bg='#101820',fg='#e3f1ea',font=('Consolas',12),wrap='char',padx=16,pady=16);box.pack(fill='both',expand=True);root.update()
with Console(INV['ports'][n],timeout=20) as c:
    c.cmd('return')
    for cmd in cmds:
        t=c.cmd(cmd);out.append(t);s=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',t).replace('\r','');s=re.sub(r'\n\n+','\n',s);box.insert('end',s+'\n');root.update()
box.see('1.0');root.update();time.sleep(.2)
pg.screenshot(region=(root.winfo_rootx(),root.winfo_rooty(),root.winfo_width(),root.winfo_height())).save(ROOT/f'evidence/screenshots/{tag}.png')
(LOG/f'{tag}.txt').write_text('\n'.join(out),encoding='utf-8');root.destroy();print(tag)
