from pathlib import Path
import json,time
import pyautogui as p
import win32gui,win32con
from lab_ui import paste
ROOT=Path(__file__).parent;CAP=ROOT/'evidence/pcaps';OUT=ROOT/'evidence/screenshots';OUT.mkdir(exist_ok=True)
items=[
 ('01-HRP-heartbeat.pcapng','HRP 心跳链路通告','vrrp','心跳接口的抓包包含发往 224.0.0.18 的通告，与双防火墙的 MASTER/SLAVE、心跳 running 状态共同核对。该镜像在心跳链路上使用 VRRP 格式承载相关通告。'),
 ('06-Core-VRRP-OSPF-LACP.pcapng','OSPF Hello 与链路状态更新','ospf.msg == 4','核心互联抓包保存了 OSPF Hello 和故障操作触发的链路状态更新。图中筛选 LSU（类型 4），再结合邻居表、LSDB 和路由表验证链路状态传播；不以单个 Hello 报文代替邻接 Full 状态。'),
 ('06-Core-VRRP-OSPF-LACP.pcapng','核心 VRRP 通告与切换','vrrp','捕获核心冗余链路上的 VRRP 通告。关闭主核心 Vlanif4094 后，对照备核心转为 Master 的控制台输出与通告源变化，核对虚拟网关 10.162.99.65 的接管。'),
 ('10-NAT-final-inside.pcapng','NAT 转换前的私网报文','icmp','在 ACC-OPD 接入端口捕获门诊流量，源地址为 10.162.101.10，目的地址为公网测试终端 203.0.113.10，同时存在返回报文。该文件与外侧抓包来自同一组终端测试。'),
 ('09-NAT-final-outside.pcapng','NAT 转换后的公网报文','icmp','在 WAN-L2 到 ISP1 的端口捕获同组流量，外发源地址替换为公网池地址 12.1.1.19，返回报文目的地址也为该公网地址。与内侧文件及防火墙会话表核对 PAT，而非只依据终端能够 ping 通判断 NAT。'),
 ('04-Guest-ACL-verified.pcapng','访客访问院内网的禁止场景','icmp && ip.dst == 10.162.106.10','访客入口抓包确认终端实际发送了到 HIS 的请求。结合该终端公网复测成功、门诊访问 HIS 成功及 VLAN 140 的入方向拒绝规则，定位院内访问隔离；抓包无响应本身不单独构成 ACL 生效证明。'),
 ('07-IPsec-backup.pcapng','IPsec 备用链路的 ESP 报文','esp','断开医疗专线主接口后，底层链路出现 198.18.0.1 与 198.18.0.2 之间的双向 ESP。终端收到会诊回复、备用路由生效且 IPsec SA 的收发序列计数增加，共同证明实际流量进入备用通道。'),
 ('08-DHCP-DORA.pcapng','DHCP 地址获取的四次交互','dhcp','访客接入口依次出现 Discover、Offer、Request、ACK（消息类型 1、2、3、5）。Offer/ACK 的 yiaddr 为 10.162.119.254，网关属于 VLAN 140 的 10.162.116.1；演示完成后终端恢复规划静态地址 10.162.116.10。')]
wins=[w for w in p.getAllWindows() if '10-NAT-final-inside.pcapng' in w.title];w=wins[0]
w.restore();w.resizeTo(1400,1100);w.moveTo(540,120);p.press('alt')
try:w.activate()
except Exception:pass
win32gui.SetWindowPos(w._hWnd,win32con.HWND_TOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
for _ in range(3):p.hotkey('ctrl','+');time.sleep(.15)
manifest=[]
for idx,(fn,title,flt,analysis) in enumerate(items,1):
    path=CAP/fn
    if not path.exists():raise FileNotFoundError(path)
    p.hotkey('ctrl','o');time.sleep(.4);paste(path);p.press('enter')
    for _ in range(60):
        if fn in win32gui.GetWindowText(w._hWnd):break
        time.sleep(.2)
    time.sleep(.5);r=win32gui.GetWindowRect(w._hWnd);x,y=r[:2]
    p.click(x+300,y+110);p.hotkey('ctrl','a');paste(flt);p.press('enter');time.sleep(.4)
    p.click(x+420,y+173);p.press('home');time.sleep(.2)
    p.click(x+300,y+650);p.press('end');p.press('right');time.sleep(.3)
    image=OUT/f'Wireshark-{idx:02}.png';p.screenshot(region=(x,y,r[2]-x,r[3]-y)).save(image)
    manifest.append(dict(file=str(path),title=title,filter=flt,analysis=analysis,image=str(image)))
    (ROOT/'evidence/capture-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print(idx,title,flush=True)
win32gui.SetWindowPos(w._hWnd,win32con.HWND_NOTOPMOST,0,0,0,0,win32con.SWP_NOMOVE|win32con.SWP_NOSIZE)
