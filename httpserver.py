'''
httpserver.py - CGI HTTP(S) server supporting SSL/IPv6.

- the default port is 80.

usage: python httpserver.py 443 [-ssl] [-6]
'''
import sys,os, re
import CGIHTTPServer, SocketServer, socket, ssl
import tempfile, uuid

SSL_PEM='''\
-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBAL9Bozj3BIjL5Cy8b3rjMT2kPZRychX4wz9bHoIIiKnKo1xXHYjw
g3N9zWM1f1ZzMADwVry1uAInA8q09+7hL20CAwEAAQJACwu2ao7RozjrV64WXimK
6X131P/7GMvCMwGHNIlbozqoOqmZcYrbKaF61l+XuwA2QvTo3ywW1Ivxcyr6TeAr
PQIhAOX+WXT6yiqqwjt08kjBCJyMgfZtdAO6pc/6pKjNWiZfAiEA1OH1iPW/OQe5
tlQXpiRVdLyneNsPygPRJc4Bdwu3hbMCIQDbI5pA56QxOzqOREOGJsb5wrciAfAE
jZbnr72sSN2YqQIgAWFpvzagw9Tp/mWzNY+cwkIK7/yzsIKv04fveH8p9IMCIQCr
td4IiukeUwXmPSvYM4uCE/+J89wEL9qU8Mlc3gDLXA==
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIICDDCCAbYCAQAwDQYJKoZIhvcNAQEEBQAwgZAxCzAJBgNVBAYTAlNFMRIwEAYD
VQQIEwlTdG9ja2hvbG0xDzANBgNVBAcTBkFsdnNqbzEMMAoGA1UEChMDRVRYMQ4w
DAYDVQQLEwVETi9TUDEXMBUGA1UEAxMOSm9ha2ltIEdyZWJlbm8xJTAjBgkqhkiG
9w0BCQEWFmpvY2tlQGVyaXguZXJpY3Nzb24uc2UwHhcNOTcwNzE1MTUzMzQxWhcN
MDMwMjIyMTUzMzQxWjCBkDELMAkGA1UEBhMCU0UxEjAQBgNVBAgTCVN0b2NraG9s
bTEPMA0GA1UEBxMGQWx2c2pvMQwwCgYDVQQKEwNFVFgxDjAMBgNVBAsTBUROL1NQ
MRcwFQYDVQQDEw5Kb2FraW0gR3JlYmVubzElMCMGCSqGSIb3DQEJARYWam9ja2VA
ZXJpeC5lcmljc3Nvbi5zZTBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQC/QaM49wSI
y+QsvG964zE9pD2UcnIV+MM/Wx6CCIipyqNcVx2I8INzfc1jNX9WczAA8Fa8tbgC
JwPKtPfu4S9tAgMBAAEwDQYJKoZIhvcNAQEEBQADQQAmXDY1CyJjzvQZX442kkHG
ic9QFY1UuVfzokzNMwlHYl1Qx9zaodx0cJCrcH5GF9O9LJbhhV77LzoxT1Q5wZp5
-----END CERTIFICATE-----
'''

SSL_PEM_FILENAME = os.path.join(tempfile.gettempdir(), str(uuid.uuid1())+'.pem')
def StreamRequestHandler_setup(self):
    if not os.path.exists(SSL_PEM_FILENAME):
        fpPem = open(SSL_PEM_FILENAME, 'wb')
        fpPem.write(SSL_PEM)
        fpPem.close()
    self.connection = ssl.SSLSocket(self.request, server_side=True, certfile=SSL_PEM_FILENAME)
    self.rfile = self.connection.makefile("rb", self.rbufsize)
    self.wfile = self.connection.makefile("wb", self.wbufsize)

if __name__ == '__main__':
    if '-ssl' in sys.argv:
        SocketServer.StreamRequestHandler.setup = StreamRequestHandler_setup
    if '-6' in sys.argv or '-v6' in sys.argv:
        SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.ThreadingTCPServer.allow_reuse_address = 1
    try:
        port = int([p for p in sys.argv[1:] if not p.startswith('-')][0])
    except:
        port = 80
    httpd = SocketServer.ThreadingTCPServer(('', port), CGIHTTPServer.CGIHTTPRequestHandler)
    sa = httpd.socket.getsockname()
    print "Serving HTTP(S) on", sa[0], "port", sa[1], "..."
    httpd.serve_forever()