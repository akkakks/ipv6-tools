title %~nx0
path %~dp0;%PATH%
py26.exe -c "import CGIHTTPServer,SocketServer,socket;SocketServer.ThreadingTCPServer.allow_reuse_address=1;SocketServer.TCPServer.address_family=socket.AF_INET6;CGIHTTPServer.test(ServerClass=SocketServer.ThreadingTCPServer)" 80