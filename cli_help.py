from configure_lab import *
def helpcmd(n,prefix,cmd):
    with Console(INV['ports'][n]) as c:
        c.cmd('return')
        for x in prefix:c.cmd(x)
        c.s.sendall((cmd+' ?').encode('ascii'));time.sleep(.2)
        b=b''
        while True:
            try:b+=c.s.recv(40000)
            except socket.timeout:break
        c.s.sendall(b'\x15\r\n');
        try:c.read()
        except:pass
        print(n,cmd,b.decode('utf-8','replace'))
if __name__=='__main__':
    helpcmd('AGG-CLINIC',['system-view'],'traffic-filter')
    helpcmd('FW-A',['system-view','policy interzone local trust inbound','policy 1'],'policy service')
    helpcmd('FW-A',['system-view','nat-policy interzone trust untrust outbound','policy 1'],'policy egress-interface')
