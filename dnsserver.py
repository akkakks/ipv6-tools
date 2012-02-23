#!/usr/bin/env python
# coding:utf-8

__version__ = '1.0'
__author__ = "phus.lu@gmail.com"

import sys, os, re, time
import logging
import glob
import gevent.server
import ipaddr
from dnslib import DNSRecord, DNSHeader, QTYPE, CNAME, RR, A

logging.basicConfig(level=0, format='%(levelname)s - - %(asctime)s %(message)s', datefmt='[%d/%b/%Y %H:%M:%S]')

IP = '::1'
TXT = 'dnsserver.py'

class AAAA(A):

    @classmethod
    def parse(cls,buffer,length):
        data = str(ipaddr.IPAddress(ipaddr.Bytes(buffer.get(length))))
        return cls(data)

    def pack(self,buffer):
        buffer.append(ipaddr.IPAddress(self.data).packed)

class DNSServer(gevent.server.DatagramServer):
    def handle(self, data, address):
        logging.info('receive data size=%r from %r', len(data), address)
        request = DNSRecord.parse(data)
        reply = DNSRecord(DNSHeader(id=request.header.id,qr=1,aa=1,ra=1),q=request.q)
        qname = request.q.qname
        qtype = request.q.qtype
        if qtype == QTYPE.A:
            reply.add_answer(RR(qname,qtype,rdata=A(IP)))
        elif qtype == QTYPE.AAAA:
            reply.add_answer(RR(qname,qtype,rdata=AAAA(IP)))
        elif qtype == QTYPE['*']:
            reply.add_answer(RR(qname,QTYPE.A,rdata=A(IP)))
            reply.add_answer(RR(qname,QTYPE.MX,rdata=MX(IP)))
            reply.add_answer(RR(qname,QTYPE.TXT,rdata=TXT(TXT)))
        else:
            reply.add_answer(RR(qname,QTYPE.CNAME,rdata=CNAME(TXT)))
        self.sendto(reply.pack(), address)

def main():
    server = DNSServer(('', 53))
    logging.info('serving at %r', server.address)
    server.family
    server.serve_forever()

if __name__ == '__main__':
    main()
