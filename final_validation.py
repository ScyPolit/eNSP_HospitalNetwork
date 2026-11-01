from configure_lab import Console,INV,LOG
from native_ui import open_device,pc_command,pcwin
from pathlib import Path
import json,re,concurrent.futures,zipfile
R=Path(__file__).parent
def probe(n):
 try:
  with Console(INV['ports'][n],timeout=8) as c:
   c.cmd('return');c.cmd('screen-length 0 temporary');t=c.cmd('display current-configuration | include sysname');return dict(name=n,ok=('sysname '+n) in t)
 except Exception as e:return dict(name=n,ok=False,error=str(e))
ident=list(concurrent.futures.ThreadPoolExecutor(6).map(probe,INV['ports']))
state={}
for n,cmd in [('CORE-SW1','display ospf peer brief'),('CORE-SW2','display ospf peer brief'),('FW-A','display hrp state'),('FW-B','display hrp state')]:
 with Console(INV['ports'][n]) as c:
  c.cmd('return');c.cmd('screen-length 0 temporary');t=c.cmd(cmd);state[n]=t;(LOG/(n+'-delivered-state.txt')).write_text(t,encoding='utf-8');print(n,'Full',t.count('Full'),flush=True)
tests=[]
for name,ip,allow in [('OPD-PC','10.162.106.10',True),('OPD-PC','203.0.113.10',True),('GUEST-PC','203.0.113.10',True),('GUEST-PC','10.162.106.10',False),('HEALTH-PC','10.162.121.10',True),('BASTION','10.162.99.65',True),('DMZ-WEB','10.162.108.2',True)]:
 open_device(name);cmd=f'ping {ip} -c 2'
 for k in range(2):
  image=pc_command(name,cmd,4);t=(LOG/f'{name}-{cmd.replace(" ","_")}.txt').read_text(encoding='utf-8');part=t[t.rfind('PC>'+cmd):];m=re.findall(r'(\d+) packet\(s\) received',part);rx=int(m[-1]) if m else None
  if rx is not None and ((rx>0)==allow):break
 pcwin(name).close();tests.append(dict(source=name,destination=ip,received=rx,expected=allow,passed=rx is not None and ((rx>0)==allow),image=str(image)));print('FINAL TEST',tests[-1],flush=True)
result=dict(identities=ident,states=state,tests=tests)
(R/'evidence/final-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(x['ok'] for x in ident)
assert all(state[n].count('Full')==14 for n in ['CORE-SW1','CORE-SW2'])
assert 'MASTER' in state['FW-A'] and 'SLAVE' in state['FW-B']
assert all(x['passed'] for x in tests)
print('FINAL VALIDATION PASSED',flush=True)
