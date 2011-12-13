#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.0'
__author__ = "phus.lu@gmail.com(Phus Lu)"

__import__('sys').dont_write_bytecode = 1

import sys, os, re
import SimpleHTTPServer, SocketServer, socket, ssl
import logging
import ftpserver

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

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

def socket_forward(local, remote, timeout=60, tick=2, bufsize=8192, maxping=None, maxpong=None, idlecall=None):
    timecount = timeout
    try:
        while 1:
            timecount -= tick
            if timecount <= 0:
                break
            (ins, _, errors) = select.select([local, remote], [], [local, remote], tick)
            if errors:
                break
            if ins:
                for sock in ins:
                    data = sock.recv(bufsize)
                    if data:
                        if sock is local:
                            remote.sendall(data)
                            timecount = maxping or timeout
                        else:
                            local.sendall(data)
                            timecount = maxpong or timeout
                    else:
                        return
            else:
                if idlecall:
                    try:
                        idlecall()
                    except Exception, e:
                        logging.warning('socket_forward idlecall fail:%s', e)
                    finally:
                        idlecall = None
    except Exception, ex:
        logging.warning('socket_forward error=%s', ex)
        raise
    finally:
        if idlecall:
            idlecall()

class HTTPRequestHandler(HTTPSMixIn, SimpleHTTPServer.SimpleHTTPRequestHandler):

    def address_string(self):
        return '%s:%s' % (self.client_address[0], self.client_address[1])


class HTTPSRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):

    def address_string(self):
        return '%s:%s' % (self.client_address[0], self.client_address[1])

    def setup(self):
        SSL_PEM_FILENAME = os.path.splitext(__file__)[0] + '.pem'
        self.connection = ssl.SSLSocket(self.request, server_side=True, certfile=SSL_PEM_FILENAME)
        self.rfile = self.connection.makefile("rb", self.rbufsize)
        self.wfile = self.connection.makefile("wb", self.wbufsize)

class HTTPServer(SimpleHTTPServer.BaseHTTPServer):
    pass

class TCPForwardHandler(SocketServer.BaseRequestHandler):

    address = ('127.0.0.1', 8080)

    def log_message(self, message):
        host, port = self.client_address[:2]
        host = '[%s]' % host if ':' in host else host
        logging.info('%s:%s -- [%s] %s\n' % (host, port, time.ctime(), message))

    def setup(self):
        host, port = self.address
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

class TCPServer(SocketServer.ThreadingTCPServer):
    pass

class FTPHandler(ftpserver.FTPHandler):

    def __init__(self, *args, **kwargs):
        ftpserver.FTPHandler.__init__(self, *args, **kwargs)
        #self.authorizer.add_anonymous()

class FTPServer(ftpserver.FTPServer):

    def __init__(self, *args, **kwargs):
        ftpserver.FTPServer.__init__(self, *args, **kwargs)

def main():
    pass

if __name__ == '__main__':
   try:
       main()
   except KeyboardInterrupt:
       pass