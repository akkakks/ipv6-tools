#!/usr/bin/env python
# coding:utf-8

__version__ = '1.0'
__author__ = "phus.lu@gmail.com"

import sys,os, re
import SimpleHTTPServer, SocketServer, socket, ssl

class HTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def address_string(self):
        return '%s:%s' % self.client_address[:2]

class HTTPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    address_family = socket.AF_INET6
    allow_reuse_address = True

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) == 2 else 80
    httpd = HTTPServer(('', port), HTTPRequestHandler)
    print 'serving at', httpd.server_address
    httpd.serve_forever()