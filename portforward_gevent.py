#!/usr/bin/env python
# coding:utf-8

import sys, os, re, time
import logging
import gevent.server, gevent.socket

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

class ForwardHandler(object):

    def __init__(self, remote_address, client_socket, address):
        logging.info('client %r connected, try to connect remote %r', address, remote_address)
        remote_socket  = gevent.socket.create_connection(remote_address)
        logging.info('connect remote %r ok, begin forward', remote_address)
        gevent.spawn(self.io_copy, client_socket, remote_socket).start()
        gevent.spawn(self.io_copy, remote_socket, client_socket).start()

    def io_copy(self, sock1, sock2, timeout=None, bufsize=4096):
        try:
            if timeout:
                sock1.settimeout(timeout)
            while 1:
                data = sock1.recv(bufsize)
                if not data:
                    break
                sock2.send(data)
        except Exception:
            logging.exception('io_copy exception')
        finally:
            logging.info('end forward, exit')
            sock1.close()
            sock2.close()

class ForwardServer(gevent.server.StreamServer):

    def __init__(self, remote_address, *args, **kwargs):
        self.remote_address = remote_address
        super(ForwardServer, self).__init__(*args, **kwargs)

    def handle(self, client_socket, address):
        gevent.spawn(ForwardHandler, self.remote_address, client_socket, address)


if __name__=='__main__':
    if len(sys.argv) == 1:
        print 'usage: portforward.py server_address remote_address'
        print 'example: portforward.py 0.0.0.0:80 127.0.0.1:8080'
        sys.exit(0)

    listener = resolve_netloc(sys.argv[1], 80)
    remote_address = resolve_netloc(sys.argv[2], 80)

    server = ForwardServer(remote_address, listener)
    print 'Serving Socket on', listener[0], 'port', listener[1], '...'
    server.serve_forever()
