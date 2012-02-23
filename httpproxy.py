#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.0'
__author__ = "phus.lu@gmail.com"

import sys, os, re, time, errno, binascii, zlib
import struct, random, hashlib, ctypes
import fnmatch, base64, logging, ConfigParser
import threading
import socket, ssl, select
import httplib, urllib2, urlparse
import BaseHTTPServer, SocketServer
try:
    import ntlm, ntlm.HTTPNtlmAuthHandler
except ImportError:
    ntlm = None

logging.basicConfig(level=logging.INFO, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

class common(object):
    '''global config module, similar with GoAgent'''
    LISTEN_IP      = '::'
    LISTEN_PORT    = 8080

    PROXY_ENABLE   = 0
    PROXY_HOST     = '10.204.16.7'
    PROXY_PORT     = '80'
    PROXY_USERNAME = 'username'
    PROXY_PASSWROD = 'password'
    PROXY_NTLM     = '\\' in PROXY_USERNAME

    HOSTS = '''\
            203.208.46.1 www.google.com
            203.208.46.1 www.google.com.hk
    '''
    HOSTS_MAP = dict((x.split()[1],x.split()[0]) for x in HOSTS.strip().splitlines())

def socket_create_connection(address, timeout=None, source_address=None):
    host, port = address
    msg = 'getaddrinfo returns an empty list'
    host = common.HOSTS_MAP.get(host) or host
    for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket.socket(af, socktype, proto)
            if isinstance(timeout, (int, float)):
                sock.settimeout(timeout)
            if source_address is not None:
                sock.bind(source_address)
            sock.connect(sa)
            return sock
        except socket.error, msg:
            if sock is not None:
                sock.close()
    raise socket.error, msg
socket.create_connection = socket_create_connection

def socket_forward(local, remote, timeout=60, tick=2, bufsize=8192, maxping=None, maxpong=None):
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
    except Exception, ex:
        logging.warning('socket_forward error=%s', ex)
    finally:
        pass

def build_opener():
    if common.PROXY_ENABLE:
        proxy = '%s:%s@%s:%d'%(common.PROXY_USERNAME, common.PROXY_PASSWROD, common.PROXY_HOST, common.PROXY_PORT)
        handlers = [urllib2.ProxyHandler({'http':proxy,'https':proxy})]
        if common.PROXY_NTLM:
            if ntlm is None:
                logging.critical('You need install python-ntlm to support windows domain proxy! "%s:%s"', common.PROXY_HOST, common.PROXY_PORT)
                sys.exit(-1)
            passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, '%s:%s' % (common.PROXY_HOST, common.PROXY_PORT), common.PROXY_USERNAME, common.PROXY_PASSWROD)
            auth_NTLM = ntlm.HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)
            handlers.append(auth_NTLM)
    else:
        handlers = [urllib2.ProxyHandler({})]
    opener = urllib2.build_opener(*handlers)
    opener.addheaders = []
    return opener

def proxy_auth_header(username, password):
    return 'Proxy-Authorization: Basic %s' + base64.b64encode('%s:%s'%(username, password))

class SimpleProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    opener = build_opener()

    def address_string(self):
        return '%s:%s' % (self.client_address[0], self.client_address[1])

    def send_response(self, code, message=None):
        self.log_request(code)
        message = message or self.responses.get(code, ('SimpleProxyHandler Notify',))[0]
        self.wfile.write('%s %d %s\r\n' % (self.protocol_version, code, message))

    def end_error(self, code, message=None, data=None):
        if not data:
            self.send_error(code, message)
        else:
            self.send_response(code, message)
            self.wfile.write(data)

    def do_CONNECT(self):
        return self.do_CONNECT_Direct()

    def do_CONNECT_Direct(self):
        try:
            logging.debug('SimpleProxyHandler.do_CONNECT_Directt %s' % self.path)
            host, _, port = self.path.rpartition(':')
            if not common.PROXY_ENABLE:
                sock = socket.create_connection((host, int(port)))
                self.log_request(200)
                self.wfile.write('%s 200 Tunnel established\r\n\r\n' % self.protocol_version)
            else:
                sock = socket.create_connection((common.PROXY_HOST, common.PROXY_PORT))
                ip = common.HOSTS_MAP.get(host, host)
                data = '%s %s:%s %s\r\n' % (self.command, ip, port, self.protocol_version)
                data += ''.join('%s: %s\r\n' % (k, self.headers[k]) for k in self.headers if k != 'host')
                if common.PROXY_USERNAME and not common.PROXY_NTLM:
                    data += '%s\r\n' % proxy_auth_header(common.PROXY_USERNAME, common.PROXY_PASSWROD)
                data += '\r\n'
                sock.sendall(data)
            socket_forward(self.connection, sock)
        except:
            logging.exception('GaeProxyHandler.do_CONNECT_Direct Error')
        finally:
            try:
                sock.close()
            except:
                pass

    def do_METHOD(self):
        return self.do_METHOD_Direct()

    def do_METHOD_Direct(self):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(self.path, 'http')
        try:
            host, _, port = netloc.rpartition(':')
            port = int(port)
        except ValueError:
            host = netloc
            port = 80
        try:
            self.log_request()
            if not common.PROXY_ENABLE:
                sock = socket.create_connection((host, port))
                self.headers['connection'] = 'close'
                data = '%s %s %s\r\n'  % (self.command, urlparse.urlunparse(('', '', path, params, query, '')), self.request_version)
                data += ''.join('%s: %s\r\n' % (k, self.headers[k]) for k in self.headers if not k.startswith('proxy-'))
                data += '\r\n'
            else:
                sock = socket.create_connection((common.PROXY_HOST, common.PROXY_PORT))
                host = common.HOSTS_MAP.get(host, host)
                url = urlparse.urlunparse((scheme, host + ('' if port == 80 else ':%d' % port), path, params, query, ''))
                data ='%s %s %s\r\n'  % (self.command, url, self.request_version)
                data += ''.join('%s: %s\r\n' % (k, self.headers[k]) for k in self.headers if k != 'host')
                data += 'Host: %s\r\n' % netloc
                if common.PROXY_USERNAME and not common.PROXY_NTLM:
                    data += '%s\r\n' % proxy_auth_header(common.PROXY_USERNAME, common.PROXY_PASSWROD)
                data += 'Proxy-connection: close\r\n'
                data += '\r\n'

            content_length = int(self.headers.get('content-length', 0))
            if content_length > 0:
                data += self.rfile.read(content_length)
            sock.sendall(data)
            socket_forward(self.connection, sock)
        except Exception, ex:
            logging.exception('GaeProxyHandler.do_GET Error, %s', ex)
        finally:
            try:
                sock.close()
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
    LocalProxyServer.address_family = (socket.AF_INET, socket.AF_INET6)[':' in common.LISTEN_IP]
    httpd = LocalProxyServer((common.LISTEN_IP, common.LISTEN_PORT), SimpleProxyHandler)
    print 'serving at', httpd.server_address
    httpd.serve_forever()
