#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import socket, SocketServer, select
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

def random_choice(seq):
    if len(seq) <= 1:
        return seq[0]
    else:
        return seq[int(ord(os.urandom(1))/256.0*len(seq))]

def resolve_netloc(netloc, defaultport=80):
    if netloc.rfind(':') > netloc.rfind(']'):
        host, _, port = netloc.rpartition(':')
        port = int(port)
    else:
        host = netloc
        port = defaultport
    if host[0] == '[':
        host = host.strip('[]')
    return host, port

def socket_forward(local, remote, timeout=60, tick=2, maxping=None, maxpong=None):
    count = timeout // tick
    try:
        while 1:
            count -= 1
            (ins, _, errors) = select.select([local, remote], [], [local, remote], tick)
            if errors:
                break
            if ins:
                for sock in ins:
                    data = sock.recv(8192)
                    if data:
                        if sock is local:
                            remote.send(data)
                            count = maxping or timeout // tick
                        else:
                            local.send(data)
                            count = maxpong or timeout // tick
            if count == 0:
                break
    except Exception, ex:
        logging.warning('socket_forward error=%s', ex)

class ForwardHandler(SocketServer.BaseRequestHandler):

    HOSTS = []

    def log_message(self, message):
        host, port = self.client_address[:2]
        host = '[%s]' % host if ':' in host else host
        sys.stdout.write('%s:%s -- [%s] %s\n' % (host, port, time.ctime(), message))

    def setup(self):
        host, port = random_choice(self.HOSTS)
        self.remote = socket.create_connection((host, port))
        self.log_message('Forward to (%r,%r)' % (host, port))

    def handle(self):
        socket_forward(self.request, self.remote, timeout=300)

    def finish(self):
        for soc in (self.request, self.remote):
            try:
                soc.close()
            except:
                pass

if __name__=='__main__':
    if len(sys.argv) == 1:
        print 'usage: portforward.py local remote1 remote2 ...'
        print 'example: portforward.py 0.0.0.0:8080 127.0.0.1:8001 127.0.0.1:8002'
        sys.exit(0)

    address = resolve_netloc(sys.argv[1], 8080)
    hosts = [resolve_netloc(x, 8080) for x in sys.argv[2:]]

    ForwardHandler.HOSTS = hosts

    if ':' in address[0]:
        SocketServer.TCPServer.address_family = socket.AF_INET6
    server = SocketServer.ThreadingTCPServer(address, ForwardHandler)
    sa = server.socket.getsockname()
    print "Serving Socket on", sa[0], "port", sa[1], "..."
    server.serve_forever()
