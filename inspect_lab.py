from pathlib import Path
import socket, concurrent.futures, json, time
import pyautogui as pg

ROOT=Path(__file__).parent
def shot(name):
    p=ROOT/'evidence'/'live';p.mkdir(parents=True,exist_ok=True)
    im=pg.screenshot(); im.save(p/(name+'.png')); im.resize((1280,720)).save(p/(name+'-preview.png'))
def probe(port):
    s=socket.socket();s.settimeout(2)
    try:
        s.connect(('127.0.0.1',port));s.sendall(b'\r\n');return [port,repr(s.recv(4000))]
    except Exception as e:return [port,str(e)]
    finally:s.close()
if __name__=='__main__':
    print(json.dumps(list(concurrent.futures.ThreadPoolExecutor().map(probe,range(2000,2008))),ensure_ascii=False,indent=2))
    shot('boot-state')
