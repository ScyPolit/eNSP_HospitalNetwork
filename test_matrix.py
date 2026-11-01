from native_ui import *
import re
CASES={
 'GUEST-PC':[('10.162.106.10',False,'访客到 HIS'),('10.162.104.10',False,'访客到办公'),('10.162.120.10',False,'访客到管理'),('203.0.113.10',True,'访客经 NAT 上网')],
 'OPD-PC':[('10.162.106.10',True,'门诊到 HIS'),('10.162.104.10',False,'门诊到行政'),('10.162.107.10',False,'普通终端到备份'),('10.162.99.65',False,'普通终端到设备管理'),('203.0.113.10',True,'门诊经 NAT 上网'),('203.0.114.10',True,'门诊经备用 ISP 上网')],
 'DMZ-WEB':[('10.162.106.10',False,'DMZ 到 HIS 的非白名单 ICMP'),('10.162.104.10',False,'DMZ 到普通终端'),('10.162.120.10',False,'DMZ 到管理')],
 'HEALTH-PC':[('10.162.106.10',True,'医疗专线到前置机诊断地址'),('10.162.104.10',False,'医疗专线到办公'),('10.162.111.10',False,'医疗专线到物联网'),('10.162.120.10',False,'医疗专线到管理'),('10.162.121.10',True,'医疗专线到远程会诊')],
 'IOT-PC':[('10.162.106.10',True,'IoT 到指定平台诊断地址'),('10.162.104.10',False,'IoT 到办公'),('10.162.120.10',False,'IoT 到管理')],
 'CCTV-PC':[('10.162.106.11',True,'安防到指定 NVR 诊断地址'),('10.162.104.10',False,'安防到办公')],
 'BRANCH-PC':[('10.162.106.10',True,'分院到 HIS'),('10.162.104.10',False,'分院到普通办公'),('203.0.113.10',False,'分院终端不直连公网')],
 'NMS-PC':[('10.162.120.20',True,'运维终端到堡垒机'),('10.162.99.65',False,'运维终端不能绕过堡垒机')],
 'BASTION':[('10.162.99.65',True,'堡垒机到设备管理诊断地址')]
}
out=ROOT/'evidence'/'test-matrix.json';results=json.loads(out.read_text(encoding='utf-8')) if out.exists() else []
for name,cases in CASES.items():
    try:
        pending=[x for x in cases if not any(r['source']==name and r['destination']==x[0] and r['passed'] for r in results)]
        if not pending:continue
        h=win32gui.FindWindow(None,name)
        if not h or not win32gui.IsWindowVisible(h):open_device(name)
        for ip,allow,desc in pending:
            cmd=f'ping {ip} -c 2';pic=pc_command(name,cmd,4)
            file=ROOT/'evidence'/'console'/f'{name}-{cmd.replace(" ","_")}.txt'
            text=file.read_text(encoding='utf-8').replace('\r','');part=text[text.rfind('PC>'+cmd):]
            received=re.findall(r'(\d+) packet\(s\) received',part);rx=int(received[-1]) if received else None
            if allow and rx==0:
                pic=pc_command(name,cmd,4);text=file.read_text(encoding='utf-8').replace('\r','');part=text[text.rfind('PC>'+cmd):];received=re.findall(r'(\d+) packet\(s\) received',part);rx=int(received[-1]) if received else None
            r=dict(source=name,destination=ip,expected=allow,received=rx,passed=(rx is not None and ((rx>0)==allow)),description=desc,image=str(pic),evidence=str(file))
            results=[old for old in results if not (old['source']==name and old['destination']==ip)]
            results.append(r);out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',json.dumps(r,ensure_ascii=False),flush=True)
        pcwin(name).close()
    except Exception as e:print('ERROR',name,repr(e),flush=True)
