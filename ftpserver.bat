title %~nx0
cd /d "%~dp0"
rem py.exe ftpserver.py [::]:21 \\10.204.16.2\Home
py.exe ftpserver.py 0.0.0.0:21 .