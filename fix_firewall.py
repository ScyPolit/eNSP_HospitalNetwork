from configure_lab import *
c=['system-view','ip service-set OSPF type object','service protocol 89','quit']
for dr in ['inbound','outbound']:
    c += [f'policy interzone local trust {dr}','policy 1','policy service service-set OSPF','quit','quit']
c += ['nat-policy interzone trust untrust outbound','undo policy 2','quit',
      'firewall zone untrust','undo add interface GigabitEthernet0/0/1','quit',
      'firewall zone name isp2','set priority 10','add interface GigabitEthernet0/0/1','quit',
      'policy interzone trust isp2 outbound','policy 1','policy source 10.162.0.0 0.0.255.255','action permit','quit','quit',
      'nat-policy interzone trust isp2 outbound','policy 1','policy source 10.162.0.0 0.0.255.255','action source-nat','address-group 2','quit','quit',
      'hrp ospf-cost adjust-enable','ip route-static 203.0.114.0 24 13.1.1.254','return']
print(apply('FW-A',c,'compatibility-fix'))
(CFG/'FW-A-compatibility-fix.txt').write_text('\n'.join(c),encoding='utf-8')
