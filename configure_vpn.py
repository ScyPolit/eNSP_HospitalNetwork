from configure_lab import *
for n,local,remote,src,dst in [('HEALTH-R','198.18.0.1','198.18.0.2','172.20.1.0','10.162.121.0'),('TELEMED-GW','198.18.0.2','198.18.0.1','10.162.121.0','172.20.1.0')]:
    c=['system-view','acl number 3500',f'rule 5 permit ip source {src} 0.0.0.255 destination {dst} 0.0.0.255','quit',
       'ike proposal 10','encryption-algorithm aes-cbc-256','authentication-algorithm sha1','dh group14','quit',
       'ike peer HOSP v1','pre-shared-key cipher Hospital-Lab-2026','ike-proposal 10',f'remote-address {remote}','quit',
       'ipsec proposal HOSP','esp encryption-algorithm aes-256','esp authentication-algorithm sha1','quit',
       'ipsec policy HOSP 10 isakmp','security acl 3500','ike-peer HOSP','proposal HOSP','quit',
       'interface GigabitEthernet0/0/2','ipsec policy HOSP','quit']
    if n=='HEALTH-R':c+=['ip route-static 10.162.121.0 24 198.18.0.2 preference 100']
    else:
        c += ['ip route-static 172.20.1.1 32 10.162.105.1','nqa test-instance hospital primary','test-type icmp','destination-address ipv4 172.20.1.1','source-address ipv4 10.162.121.1','frequency 5','probe-count 2','timeout 1','start now','quit',
              'ip route-static 172.20.1.0 24 10.162.105.1 track nqa hospital primary','ip route-static 172.20.1.0 24 198.18.0.1 preference 100']
    c+=['return'];print(apply(n,c,'ipsec-config'));(CFG/f'{n}-IPsec.txt').write_text('\n'.join(c),encoding='utf-8')
