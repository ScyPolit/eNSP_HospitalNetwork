from pathlib import Path
import sys, json, concurrent.futures, argparse, time
sys.path.insert(0,r'C:\Users\SCY-Polit\.dsh\ungrouped\ENSP-MCP')
from ensp_mcp_server.console import HuaweiConsole
ROOT=Path(__file__).parent
LOG=ROOT/'evidence'/'console';LOG.mkdir(parents=True,exist_ok=True)
def run(name,port,cmds,tag='config',timeout=8):
    out=[]
    try:
        with HuaweiConsole('127.0.0.1',port,timeout=timeout) as c:
            for cmd in cmds:
                result=c.send_command(cmd)
                out.append(f'>>> {cmd}\n{result}\n')
    except Exception as e:out.append('EXCEPTION '+str(e))
    result='\n'.join(out)
    (LOG/f'{name}-{tag}.txt').write_text(result,encoding='utf-8')
    errors=[x for x in result.splitlines() if any(s in x for s in ['Error:', 'Unrecognized', 'Incomplete', 'Wrong parameter','EXCEPTION'])]
    return {'name':name,'commands':len(out),'errors':errors}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('port',type=int);ap.add_argument('commands',nargs='+');a=ap.parse_args()
    print(run(a.name,a.port,a.commands,tag='probe'))
    print((LOG/f'{a.name}-probe.txt').read_text(encoding='utf-8'))
