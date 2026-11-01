from configure_lab import *
def collect(n):
    m=next(d['model'] for d in INV['devices'] if d['name']==n)
    cmds=['display current-configuration','display interface brief','display ip routing-table']
    if m=='S5700':cmds+=['display port vlan','display eth-trunk','display stp brief']
    if n.startswith('CORE-'):cmds+=['display vrrp brief','display ospf peer brief','display ospf abr-asbr','display ip routing-table 0.0.0.0']
    elif n.startswith('AGG-'):cmds+=['display ospf peer brief','display ospf brief','display acl all']
    elif m=='USG5500':cmds+=['display hrp state','display hrp interface','display hrp group','display ospf peer','display firewall session table verbose','display nat-policy all']
    r=apply(n,cmds,'final-state')
    # Save inside each actual device; confirm native prompts.
    try:
        with Console(INV['ports'][n]) as c:
            c.cmd('return');out=c.cmd('save')
            for _ in range(4):
                tail=out.splitlines()[-1] if out.splitlines() else ''
                if '[y/n]' in tail.lower():out+=c.cmd('y')
                elif 'file name' in tail.lower() or 'filename' in tail.lower():out+=c.cmd('')
                else:break
            (LOG/f'{n}-save.txt').write_text(out,encoding='utf-8')
    except Exception as e:r['save_error']=str(e)
    return r
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        for r in ex.map(collect,INV['ports']):print(json.dumps(r,ensure_ascii=False),flush=True)
