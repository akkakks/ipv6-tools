start "dnsserver" py.exe dnsserver.py
start "httpserver" py.exe httpserver.py
start "ftpserver" py.exe ftpserver.py -i "::" -w -d .
start "httpproxy" py.exe httpproxy.py