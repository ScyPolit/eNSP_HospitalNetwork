from configure_lab import *
for i,n in enumerate(['FW-A','FW-B']):
    lo,hi=(10,19) if i==0 else (20,30)
    c=['system-view','nat-policy interzone trust untrust outbound','undo policy 1','undo policy 3','quit','nat-policy interzone trust isp2 outbound','undo policy 1','quit',
       f'nat address-group 1 12.1.1.{lo} 12.1.1.{hi}',f'nat address-group 2 13.1.1.{lo} 13.1.1.{hi}']
    for z,num in [('untrust',1),('isp2',2)]:c += [f'nat-policy interzone trust {z} outbound','policy 1','policy source 10.162.0.0 0.0.255.255','action source-nat',f'address-group {num}','quit','quit']
    c+=['return'];print(apply(n,c,'nat-disjoint-final'));(CFG/f'{n}-nat-final.txt').write_text('\n'.join(c),encoding='utf-8')
for i in [1,2]:
    net=11+i;c=['system-view']
    for sub,mask in [('8',29),('16',28),('100',32)]:c += [f'undo ip route-static {net}.1.1.{sub} {mask} GigabitEthernet0/0/0 {net}.1.1.1']
    c+=['return','reset arp dynamic'];print(apply(f'ISP-R{i}',c,'remove-pool-routes'))
