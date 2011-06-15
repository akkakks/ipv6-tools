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
            host, _, port = self.path.rpartition(':')
            soc = socket.create_connection((host, port))
            self.log_request(200)
            self.wfile.write('%s 200 Connection established\r\n' % self.protocol_version)
            self.wfile.write('Proxy-agent: %s\r\n\r\n' % self.version_string())
            self._read_write(self.connection, soc)
        except Exception, ex:
            logging.exception('SimpleProxyHandler.do_CONNECT Error, %s', ex)
            self.send_error(502, 'SimpleProxyHandler.do_CONNECT Error (%s)' % ex)
        finally:
            for conn in [self.connection, soc]:
                try:
                    conn.close()
                except:
                    pass

    def resolve_netloc(self, netloc, defaultport=80):
        if netloc.find(':') > netloc.find(']'):
            host, _, port = netloc.rpartition(':')
            return host, int(port)
        else:
            return netloc, defaultport

    def do_METHOD(self):
        try:
            logging.info('%s %r' % (self.command, self.path))
            scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.path, 'http')
            host, port = self.resolve_netloc(netloc)
            soc = socket.create_connection((host, port))
            data = '%s %s %s\r\n'  % (self.command, urlparse.urlunparse(('', '', path, params, query, '')), self.request_version)
            data += ''.join('%s: %s\r\n' % (k, self.headers[k]) for k in self.headers if not k.lower().startswith('proxy-'))
            data += 'Connection: close\r\n'
            data += '\r\n'
            if self.command == 'POST':
                data += self.rfile.read()
            soc.send(data)
            self._read_write(self.connection, soc)
        except Exception, ex:
            logging.exception('SimpleProxyHandler.do_GET Error, %s', ex)
            self.send_error(502, 'SimpleProxyHandler.do_GET Error (%s)' % ex)
        finally:
            for conn in [self.connection, soc]:
                try:
                    conn.close()
                except:
                    pass

    def _read_write(self, local, remote):
        DIRECT_KEEPLIVE = 60
        DIRECT_TICK = 2
        count = DIRECT_KEEPLIVE // DIRECT_TICK
        while 1:
            count -= 1
            (ins, _, errors) = select.select([local, remote], [], [local, remote], DIRECT_TICK)
            if errors:
                break
            if ins:
                for sock in ins:
                    data = sock.recv(8192)
                    if data:
                        if sock is local:
                            remote.send(data)
                            # if packets lost in 20 secs, maybe ssl connection was dropped by GFW
                            count = 10
                        else:
                            local.send(data)
                            count = DIRECT_KEEPLIVE // DIRECT_TICK
            if count == 0:
                break

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
        print 'example: httpproxy.py :: 8080'
        sys.exit(0)
    listen_ip = sys.argv[1]
    listen_port = int(sys.argv[2]) if len(sys.argv) == 3 else 8080
    if ':' in listen_ip:
        SocketServer.TCPServer.address_family = socket.AF_INET6
        server = SocketServer.ThreadingTCPServer((listen_ip.strip('[]'), listen_port), SimpleProxyHandler)
    else:
        server = SocketServer.ThreadingTCPServer((listen_ip, listen_port), SimpleProxyHandler)
    sa = server.socket.getsockname()
    print "Serving Socket on", sa[0], "port", sa[1], "..."
    server.serve_forever()
