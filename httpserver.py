'''
httpserver.py - Simple HTTP(S) server supporting SSL/IPv6.

- the default port is 80.

usage: python httpserver.py 443 [-ssl] [-6]
'''
import sys,os, re
import SimpleHTTPServer, SocketServer, socket, ssl

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

class HTTPSMixIn:
    def setup(self):
        SSL_PEM_FILENAME = os.path.splitext(__file__)[0] + '.pem'
        self.connection = ssl.SSLSocket(self.request, server_side=True, certfile=SSL_PEM_FILENAME)
        self.rfile = self.connection.makefile("rb", self.rbufsize)
        self.wfile = self.connection.makefile("wb", self.wbufsize)

class SimpleHTTPSRequestHandler(HTTPSMixIn, SimpleHTTPServer.SimpleHTTPRequestHandler):
    pass

if __name__ == '__main__':
    RequestHandler = SimpleHTTPServer.SimpleHTTPRequestHandler
    if '-ssl' in sys.argv:
        RequestHandler = SimpleHTTPSRequestHandler
        sys.argv.remove('-ssl')
    address = resolve_netloc(sys.argv[1])
    SocketServer.ThreadingTCPServer.allow_reuse_address = 1
    SocketServer.TCPServer.address_family = socket.AF_INET6 if ':' in address[0] else socket.AF_INET
    httpd = SocketServer.ThreadingTCPServer(address, RequestHandler)
    print "Serving HTTP(S) on", address[0], "port", address[1], "..."
    httpd.serve_forever()