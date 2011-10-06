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

def io_copy(sock1, sock2, timeout=None, bufsize=4096):
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
        logging.info('end forward, closed')
        try:
            sock1.close()
        except:
            pass
        try:
            sock2.close()
        except:
            pass

def forward(client_socket, address):
    remote_address = resolve_netloc(os.environ['remote_address'], 8080)
    logging.info('client %r connected, try to connect remote %r', address, remote_address)
    remote_socket  = gevent.socket.create_connection(remote_address)
    logging.info('connect remote %r ok, begin forward', remote_address)
    gevent.spawn(io_copy, client_socket, remote_socket).start()
    gevent.spawn(io_copy, remote_socket, client_socket).start()

if __name__=='__main__':
    if len(sys.argv) == 1:
        print 'usage: portforward.py server_address remote_address'
        print 'example: portforward.py 0.0.0.0:80 127.0.0.1:8080'
        sys.exit(0)

    listener = resolve_netloc(sys.argv[1], 80)
    os.environ['remote_address'] = sys.argv[2]

    server = gevent.server.StreamServer(listener, forward)
    print 'Serving Socket on', listener[0], 'port', listener[1], '...'
    server.serve_forever()
