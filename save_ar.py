from pathlib import Path
import sys,json
sys.path.insert(0,r'C:\Users\SCY-Polit\.dsh\ungrouped\ENSP-MCP')
from ensp_mcp_server.console import HuaweiConsole
ROOT=Path(__file__).parent;j=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'));pf=ROOT/'evidence/persistence.json';p=json.loads(pf.read_text(encoding='utf-8'))
for n in ['ISP-R1','ISP-R2','HEALTH-R','TELEMED-GW']:
    with HuaweiConsole('127.0.0.1',j['ports'][n],timeout=15) as c:
        c.send_command('return');cfg=c.send_command('display current-configuration');(ROOT/f'evidence/console/{n}-running-final.txt').write_text(cfg,encoding='utf-8');(ROOT/f'output/医院园区网/配置/{n}-running.cfg').write_text(cfg,encoding='utf-8')
        out=c.save_config();(ROOT/f'evidence/console/{n}-save-final.txt').write_text(out,encoding='utf-8');r=next(x for x in p if x['name']==n);r['saved']='successfully' in out.lower();r['detail']=out[-300:];r.pop('error',None);print(n,r['saved'],flush=True)
pf.write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
