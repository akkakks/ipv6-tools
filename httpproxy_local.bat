title "proxy server" 
start polipo.exe proxyPort=8080
py26.exe portforward.py [::]:8080 127.0.0.1:8080