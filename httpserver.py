'''
httpserver.py - Simple HTTP(S) server supporting SSL/IPv6.

- the default port is 80.

usage: python httpserver.py 443 [-ssl] [-6]
'''
import sys,os, re
import SimpleHTTPServer, SocketServer, socket, ssl

class HTTPSMixIn:
    def setup(self):
        SSL_PEM_FILENAME = os.path.splitext(__file__)[0] + '.pem'
        self.connection = ssl.SSLSocket(self.request, server_side=True, certfile=SSL_PEM_FILENAME)
        self.rfile = self.connection.makefile("rb", self.rbufsize)
        self.wfile = self.connection.makefile("wb", self.wbufsize)

class SimpleHTTPSRequestHandler(HTTPSMixIn, SimpleHTTPServer.SimpleHTTPRequestHandler):
    pass

if __name__ == '__main__':
    RequestHandler = SimpleHTTPSRequestHandler if '-ssl' in sys.argv else SimpleHTTPServer.SimpleHTTPRequestHandler
    SocketServer.TCPServer.address_family = socket.AF_INET6 if '-6' in sys.argv else socket.AF_INET
    SocketServer.ThreadingTCPServer.allow_reuse_address = 1
    try:
        port = int([p for p in sys.argv[1:] if not p.startswith('-')][0])
    except:
        port = 80
    httpd = SocketServer.ThreadingTCPServer(('', port), RequestHandler)
    sa = httpd.socket.getsockname()
    print "Serving HTTP(S) on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()