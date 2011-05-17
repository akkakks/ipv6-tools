title "mail server" 
start "gmail pop server"      py26.exe portforward.py [::]:25  pop.gmail.com:25
start "gmail smtp server"     py26.exe portforward.py [::]:110 smtp.gmail.com:110
start "gmail pop ssl server"  py26.exe portforward.py [::]:995 pop.gmail.com:995
start "gmail smtp ssl server" py26.exe portforward.py [::]:465 smtp.gmail.com:465