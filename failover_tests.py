from configure_lab import *
from native_ui import open_device,pc_command,pcwin
import subprocess,sys
events=[]
def snap(n,tag,cmds):
    subprocess.run([sys.executable,str(ROOT/'scenario_evidence.py'),n,tag,*cmds],check=True)
    return str(ROOT/f'evidence/screenshots/{tag}.png')
def add(desc,title,image):
    events.append(dict(description=desc,title=title,image=image));(ROOT/'evidence/failover-results.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
try:
    print('VRRP switchover',flush=True)
    print(apply('CORE-SW1',['system-view','interface Vlanif4094','shutdown','return'],'vrrp-fault'))
    time.sleep(5)
    im=snap('CORE-SW2','failover-core-vrrp',['display vrrp brief','ping -c 2 10.162.106.10'])
    add('关闭 CORE-SW1 的 Vlanif4094 后，检查 CORE-SW2 的 VRRP 状态与服务器诊断连通性；随后恢复接口。','核心 VRRP 切换',im)
finally:print(apply('CORE-SW1',['system-view','interface Vlanif4094','undo shutdown','return'],'vrrp-restored'))
try:
    print('LACP member failure',flush=True)
    print(apply('CORE-SW1',['system-view','interface GigabitEthernet0/0/23','shutdown','return'],'lacp-fault'));time.sleep(3)
    im=snap('CORE-SW1','failover-lacp',['display eth-trunk 1','ping -c 2 -a 10.162.99.66 10.162.99.67'])
    add('关闭核心互联的 GE0/0/23，保留 GE0/0/24。检查 Eth-Trunk 仍为 up、活动成员降为一条，并从 Vlanif4094 跨聚合链路测试对端地址。','单成员故障时的 LACP 连通性',im)
finally:print(apply('CORE-SW1',['system-view','interface GigabitEthernet0/0/23','undo shutdown','return'],'lacp-restored'))
try:
    print('HRP switchover',flush=True)
    print(apply('FW-A',['system-view','interface GigabitEthernet0/0/3','shutdown','return'],'hrp-fault'));time.sleep(12)
    im=snap('FW-B','failover-hrp',['display hrp state','display hrp interface'])
    add('关闭 FW-A 的一个受 VRRP 组监控的 Trust 接口，等待 VGMP/HRP 重新选举。截图记录 FW-B 的角色；新建终端会话另行验证，不据主备状态推断旧会话无损延续。','防火墙 HRP 主备切换',im)
    open_device('OPD-PC');pc_command('OPD-PC','ping 203.0.113.10 -c 3',6);pcwin('OPD-PC').close()
    im=snap('FW-B','failover-hrp-nat',['display hrp state','display firewall session table verbose'])
    add('切换后从门诊新建公网 ICMP 会话，并在 FW-B 检查实际 NAT 会话和返回计数。','备用防火墙的新建 NAT 会话',im)
finally:print(apply('FW-A',['system-view','interface GigabitEthernet0/0/3','undo shutdown','return'],'hrp-restored'))
print('fault tests finished; HRP preemption can take 30 seconds',flush=True)
