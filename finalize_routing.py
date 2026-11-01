from configure_lab import *
for i in [1,2]:
    net=11+i;c=['system-view']
    for suffix,mask in [('8',29),('16',28),('100',32)]:
        c += [f'undo ip route-static {net}.1.1.{suffix} {mask} {net}.1.1.1',f'ip route-static {net}.1.1.{suffix} {mask} GigabitEthernet0/0/0 {net}.1.1.1']
    c+=['return']
    print(apply(f'ISP-R{i}',c,'nat-routes-final'))
    (CFG/f'ISP-R{i}-nat-routes.txt').write_text('\n'.join(c),encoding='utf-8')
