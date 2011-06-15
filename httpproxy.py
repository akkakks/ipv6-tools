#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = 'beta'
__author__ =  'phus.lu@gmail.com'

import sys, os, re, time
import errno, zlib, struct, binascii
import logging
import httplib, urllib2, urlparse, socket, select
import BaseHTTPServer, SocketServer
import threading, Queue

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
        raise

class SimpleProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def address_string(self):
        return '%s:%s' % self.client_address[:2]

    def send_response(self, code, message=None):
        self.log_request(code)
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = 'SimpleProxyHandler Notify'
        if self.request_version != 'HTTP/0.9':
            self.wfile.write('%s %d %s\r\n' % (self.protocol_version, code, message))

    def end_error(self, code, message=None, data=None):
        if not data:
            self.send_error(code, message)
        else:
            self.send_response(code, message)
            self.wfile.write(data)
        self.connection.close()

    def finish(self):
        try:
            self.wfile.close()
            self.rfile.close()
        except socket.error, (err, _):
            # Connection closed by browser
            if err == 10053 or err == errno.EPIPE:
                self.log_message('socket.error: [%s] "Software caused connection abort"', err)
            else:
                raise

    def do_CONNECT(self):
        try:
            logging.info('CONNECT %s' % self.path)
            host, port = resolve_netloc(self.path, 443)
            soc = socket.create_connection((host, port))
            self.log_request(200)
            self.wfile.write('%s 200 Connection established\r\n' % self.protocol_version)
            self.wfile.write('Proxy-agent: %s\r\n\r\n' % self.version_string())
            socket_forward(self.connection, soc, timeout=300)
        except Exception, ex:
            logging.exception('SimpleProxyHandler.do_CONNECT Error, %s', ex)
            self.send_error(502, 'SimpleProxyHandler.do_CONNECT Error (%s)' % ex)
        finally:
            for conn in [self.connection, soc]:
                try:
                    conn.close()
                except:
                    pass

    def do_METHOD(self):
        try:
            logging.info('%s %r' % (self.command, self.path))
            scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.path, 'http')
            host, port = resolve_netloc(netloc, 80)
            soc = socket.create_connection((host, port))
            data = '%s %s %s\r\n'  % (self.command, urlparse.urlunparse(('', '', path, params, query, '')), self.request_version)
            data += ''.join('%s: %s\r\n' % (k, self.headers[k]) for k in self.headers if not k.lower().startswith('proxy-'))
            data += 'Connection: close\r\n'
            data += '\r\n'
            if self.command == 'POST':
                data += self.rfile.read()
            soc.send(data)
            socket_forward(self.connection, soc, timeout=300)
        except Exception, ex:
            logging.exception('SimpleProxyHandler.do_GET Error, %s', ex)
            self.send_error(502, 'SimpleProxyHandler.do_GET Error (%s)' % ex)
        finally:
            for conn in [self.connection, soc]:
                try:
                    conn.close()
                except:
                    pass

    do_GET = do_METHOD
    do_POST = do_METHOD
    do_PUT = do_METHOD
    do_DELETE = do_METHOD

class LocalProxyServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'usage: httpproxy.py ip [port]'
        print 'example: httpproxy.py [::]:8080'
        sys.exit(0)
    address = resolve_netloc(sys.argv[1], 8080)
    if ':' in address[0]:
        SocketServer.TCPServer.address_family = socket.AF_INET6
    server = SocketServer.ThreadingTCPServer(address, SimpleProxyHandler)
    sa = server.socket.getsockname()
    print "Serving Socket on", sa[0], "port", sa[1], "..."
    server.serve_forever()
