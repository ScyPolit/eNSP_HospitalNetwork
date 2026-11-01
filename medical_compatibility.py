from configure_lab import *
# Probe virtual-IP ownership through the actual interface MAC, avoiding the
# USG5500 simulator's virtual-MAC receive limitation seen in the capture.
for n in ['FW-A','FW-B']:
    c=['system-view','policy interzone local medical inbound','policy 1','policy source 192.0.2.254 0','policy destination 192.0.2.1 0','policy service service-set icmp','action permit','quit','quit','return']
    print(apply(n,c,'medical-vip-probe'))
c=['system-view','ip route-static 192.0.2.1 32 GigabitEthernet0/0/0 192.0.2.2',
   'nqa test-instance hospital fwa','test-type icmp','destination-address ipv4 192.0.2.1','source-address ipv4 192.0.2.254','frequency 5','probe-count 2','timeout 1','start now','quit']
for dest in ['10.162.106.0','10.162.121.0']:
    c += [f'undo ip route-static {dest} 24 192.0.2.1',f'ip route-static {dest} 24 GigabitEthernet0/0/0 192.0.2.2 track nqa hospital fwa',f'ip route-static {dest} 24 GigabitEthernet0/0/0 192.0.2.3 preference 80']
c+=['return'];print(apply('HEALTH-R',c,'medical-physical-nexthop'))
(CFG/'HEALTH-R-medical-compatibility.txt').write_text('\n'.join(c),encoding='utf-8')
