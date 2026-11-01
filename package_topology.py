from pathlib import Path
import json,shutil,xml.etree.ElementTree as ET,re,csv,hashlib
ROOT=Path(__file__).parent;src=ROOT/'output/医院园区网';dst=ROOT/'output/hospital-network/工程';dst.mkdir(parents=True,exist_ok=True)
j=json.loads((ROOT/'evidence/layout-proposed.json').read_text(encoding='utf-8'));pos={d['name']:d for d in j['devices']}
file=src/'hospital-network.topo';raw=file.read_bytes();s=raw.decode('utf-16') if raw[:2] in [b'\xff\xfe',b'\xfe\xff'] else raw.decode('utf-8-sig');s=re.sub(r'encoding="[^"]+"','encoding="utf-8"',s,count=1);tree=ET.fromstring(s)
for dev in tree.find('devices'):
    d=pos[dev.get('name')];x,y=d['x'],d['y'];dev.set('cx',f'{x:.6f}');dev.set('cy',f'{y:.6f}');dev.set('edit_left',str(x+27));dev.set('edit_top',str(y+54))
    if d['model']=='PC':
        st=dev.get('settings','');m=re.search(r'-simpc_gateway\s+(\S+)',st)
        if m and m.group(1)!=d['gw']:raise ValueError(f"PC gateway mismatch: {d['name']} {m.group(1)} != {d['gw']}")
    if 'port' in d:
        folder=src/d['id']
        if not folder.exists() or not any(folder.iterdir()):raise ValueError('Missing device configuration '+d['name'])
        shutil.copytree(folder,dst/d['id'],dirs_exist_ok=True)
byid={d['id']:d for d in j['devices']}
for line in tree.find('lines'):
    a=byid[line.get('srcDeviceID').upper()];b=byid[line.get('destDeviceID').upper()]
    for pair in line:
        for prefix in ['src','tar']:
            pair.set(prefix+'BoundRectIsMoved','0');pair.set(prefix+'BoundRect_X',str((a['x']+b['x'])/2));pair.set(prefix+'BoundRect_Y',str((a['y']+b['y'])/2));pair.set(prefix+'Offset_X','0');pair.set(prefix+'Offset_Y','0')
tips=tree.find('txttips')
if tips is not None:tips.clear()
else:tips=ET.SubElement(tree,'txttips')
ET.SubElement(tips,'txttip',left='900',top='20',right='1900',bottom='60',content='Hospital Campus | 58 devices / 92 GE copper links | LACP: 2 members per trunk',fontname='Consolas',fontstyle='0',editsize='110',txtcolor='-16777216',txtbkcolor='-1',charset='1')
ET.indent(tree)
out=dst/'hospital-network.topo';out.write_text('<?xml version="1.0" encoding="UNICODE" ?>\n'+ET.tostring(tree,encoding='unicode'),encoding='utf-8')
(ROOT/'lab_inventory.json').write_text(json.dumps(j,ensure_ascii=False,indent=2),encoding='utf-8')
print(out);print('startup folders',len([d for d in dst.iterdir() if d.is_dir()]))
