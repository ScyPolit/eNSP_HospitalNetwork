from configure_lab import *
def persist(n):
    log=[]
    try:
        with Console(INV['ports'][n],timeout=20) as c:
            for cmd in ['return','system-view','user-interface console 0','screen-length 0','return']:
                log.append(c.cmd(cmd))
            cfg=c.cmd('display current-configuration');(LOG/f'{n}-running-final.txt').write_text(cfg,encoding='utf-8')
            plain=re.sub(r'\x1b\[[0-9;]*[A-Za-z]','',cfg).replace('\r','')
            start=plain.find('\n#');end=plain.rfind('\nreturn')
            if end>start>=0:(CFG/f'{n}-running.cfg').write_text(plain[start+1:end+7]+'\n',encoding='utf-8')
            chunk=c.cmd('save');savelog=chunk
            for _ in range(6):
                if has_prompt(chunk):break
                tail=chunk[-500:].lower()
                if 'file name' in tail or 'filename' in tail:chunk=c.cmd('')
                elif '[y/n]' in tail:chunk=c.cmd('y')
                else:break
                savelog+=chunk
            (LOG/f'{n}-save-final.txt').write_text(savelog,encoding='utf-8')
            success='successfully' in savelog.lower() or 'saved successfully' in savelog.lower()
            return dict(name=n,saved=success,detail=savelog[-350:])
    except Exception as e:return dict(name=n,saved=False,error=repr(e))
if __name__=='__main__':
    allr=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(persist,INV['ports']):allr.append(r);print(json.dumps(r,ensure_ascii=False),flush=True)
    (ROOT/'evidence/persistence.json').write_text(json.dumps(allr,ensure_ascii=False,indent=2),encoding='utf-8')
