#!/usr/bin/env python
# coding:utf-8

import sys, os
sys.dont_write_bytecode = True
sys.path += ['.', os.path.dirname(getattr(sys, 'executable', sys.argv[0]))]

import sys, os, re, time
import errno, zlib, struct, binascii
import logging
import httplib, urllib2, urlparse, socket, select
import BaseHTTPServer, SocketServer, SimpleHTTPServer, CGIHTTPServer
import asynchat, asyncore
import StringIO
import random
import ConfigParser
import ssl
import ctypes
import threading, Queue
import traceback
import tarfile, zipfile, gzip
import glob

sys.argv.pop(0)
if sys.argv[0] == '-c':
    sys.argv.pop(0)
    exec(sys.argv[0])
elif os.path.isfile(sys.argv[0]):
    sys.argv[0] = os.path.abspath(sys.argv[0])
    __file__ = sys.argv[0]
    execfile(sys.argv[0])
else:
    raise RuntimeError(u'Unkown command %r' % sys.argv)