#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import socket, SocketServer, select

class PortForwardMixin(object):
    PORT  = 8000
    HOSTS = []

class ConnectionHandler(SocketServer.BaseRequestHandler, PortForwardMixin):

    def log_message(self, message):
        sys.stdout.write('%s:%s -- [%s] %s\n' % (self.client_address[0], self.client_address[1], time.ctime(), message))

    def setup(self):
        remote_host, remote_port = self.HOSTS[int(ord(os.urandom(1))/256.0*len(self.HOSTS))]
        (soc_family, _, _, _, address) = socket.getaddrinfo(remote_host, remote_port)[0]
        self.remote = socket.socket(soc_family)
        self.remote.connect(address[:2])
        self.log_message('Forward to (%r,%r)' % (remote_host, remote_port))

    def handle(self):
        self._read_write(self.request, self.remote)
        #self.log_message('Forward End')

    def finish(self):
        for soc in (self.request, self.remote):
            try:
                soc.close()
            except:
                pass

    def _read_write(self, soc1, soc2):
        time_out_max = 60
        socs = [soc1, soc2]
        count = 0
        while 1:
            count += 1
            (recv, _, error) = select.select(socs, [], socs, 5)
            if error:
                break
            if recv:
                for in_ in recv:
                    data = in_.recv(8192)
                    if in_ is soc1:
                        out = soc2
                    else:
                        out = soc1
                    if data:
                        out.send(data)
                        count = 0
            if count == time_out_max:
                break

if __name__=='__main__':
    if len(sys.argv) == 1:
        print 'usage: portforward.py local remote1 remote2 ...'
        print 'example: portforward.py 0.0.0.0:8000 127.0.0.1:8001 127.0.0.1:8002'
        sys.exit(0)
    local, remotes = sys.argv[1], sys.argv[2:]
    localaddr, _, localport = local.rpartition(':')
    remotehosts = [(x.split(':')[0], int(x.split(':')[1])) for x in remotes]

    PortForwardMixin.PORT = localport
    PortForwardMixin.HOSTS = remotehosts

    if ':' in localaddr:
        SocketServer.TCPServer.address_family = socket.AF_INET6
        server = SocketServer.ThreadingTCPServer((localaddr.strip('[]'), int(localport)), ConnectionHandler)
    else:
        server = SocketServer.ThreadingTCPServer((localaddr, int(localport)), ConnectionHandler)

    sa = server.socket.getsockname()
    print "Serving Socket on", sa[0], "port", sa[1], "..."
    server.serve_forever()
