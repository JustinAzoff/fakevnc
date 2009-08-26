#!/usr/bin/env python

from twisted.internet import protocol, reactor
from twisted.protocols import basic
from zope.interface import Interface, implements
from twisted.python import components

import struct
import datetime

import logging


def pack32(n):
    return struct.pack("!i", n)
def unpack32(n):
    return struct.unpack("!i", n)

def unpack8(n):
    return struct.unpack("!B", n)[0]


rfbVncAuthFailed = 1
rfbSecTypeVncAuth = 2

CHALLENGESIZE=16

def random_challenge():
    return open("/dev/urandom").read(CHALLENGESIZE)

class FakeVNCProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.state = "init"
        self.got_protocol = False
        self.transport.write("RFB 003.003\n")
        self.setRawMode()
        reactor.callLater(5, self.do_close)

    def connectionLost(self, reason):
        self.do_close()

    def do_close(self):
        if self.state == "closed":
            return
        func = [self.gotTcpConnection, self.gotVncConnection][self.got_protocol]
        func()
        self.transport.loseConnection()
        self.state="closed"

    def send_32(self, n):
        self.transport.write(pack32(n))

    def sendstring(self, s):
        self.send_32(len(s))
        self.transport.write(s)

    def lineReceived(self, line):
        self.factory.logger.debug("Line: %r" % line)

    def go_away(self):
        self.send_32(rfbVncAuthFailed)
        self.sendstring("Authentication failure")
        self.transport.loseConnection()
        self.state="closed"


    def rawDataReceived(self, bytes):
        #print 'got', repr(bytes)
        if self.state == "init" and 'RFB' not in bytes:
            self.transport.loseConnection()
        if 'RFB ' in bytes:
            self.got_protocol = True
            self.state = "sent_challenge"
            self.send_32(rfbSecTypeVncAuth)
            self.transport.write(random_challenge())
            return
        #client sends 1 byte to ack the auth types, and then the 16 byte
        #challenge response
        if self.state == "sent_challenge" and len(bytes) > 6:
            self.gotVncAuthAttempt()
            self.go_away() 

    def gotTcpConnection(self):
        host = self.transport.getPeer().host
        self.factory.gotTcpConnection(host)
    def gotVncConnection(self):
        host = self.transport.getPeer().host
        self.factory.gotVncConnection(host)
    def gotVncAuthAttempt(self):
        host = self.transport.getPeer().host
        self.factory.gotVncAuthAttempt(host)

class IFakeVncFactory(Interface):

    def gotTcpConnection(self, host):
        """log a tcp connection"""
    def gotVncConnection(self, host):
        """log a vnc connection"""
    def gotVncAuthAttempt(self, host):
        """log a vnc auth attempt"""

    def buildProtocol(addr):
        """Return a protocol returning a string"""

class IFakeVncBackend(Interface):
    def gotTcpConnection(self, host):
        """log a tcp connection"""
    def gotVncConnection(self, host):
        """log a vnc connection"""
    def gotVncAuthAttempt(self, host):
        """log a vnc auth attempt"""

class FakeVncFactoryFromService(protocol.ServerFactory):
    implements(IFakeVncFactory)
    protocol = FakeVNCProtocol

    def __init__(self, service):
        self.service = service

    def gotTcpConnection(self, host):
        """log a tcp connection"""
        return self.service.gotTcpConnection(host)
    def gotVncConnection(self, host):
        """log a vnc connection"""
        return self.service.gotVncConnection(host)
    def gotVncAuthAttempt(self, host):
        """log a vnc auth attempt"""
        return self.service.gotVncAuthAttempt(host)

components.registerAdapter(FakeVncFactoryFromService,
                           IFakeVncBackend,
                           IFakeVncFactory)


class FakeVncLogBackend:
    implements([IFakeVncBackend])

    def __init__(self, filename):
        x = logging.getLogger("fakevnc")
        x.setLevel(logging.INFO)
        h1 = logging.FileHandler(filename)
        f = logging.Formatter("%(asctime)s %(message)s", datefmt="%b %d %H:%M:%S")
        h1.setFormatter(f)
        h1.setLevel(logging.INFO)
        x.addHandler(h1)
        self.logger = x

    def gotTcpConnection(self, host):
        self.logger.info("fakevnc: TCP Connection from %s" % host)
    def gotVncConnection(self, host):
        self.logger.info("fakevnc: VNC Connection from %s" % host)
    def gotVncAuthAttempt(self, host):
        self.logger.info("fakevnc: VNC Auth attempt from %s" % host)

def main():
    backend = FakeVncLogBackend("/var/log/fakevnc/fakevnc.log")
    #application = service.Application('fakevnc')
    #serviceCollection = service.IServiceCollection(application)
    #internet.TCPServer(5900, IFakeVncFactory(backend)
    #               ).setServiceParent(serviceCollection)
    reactor.listenTCP(5900, IFakeVncFactory(backend))
    reactor.run()

if __name__ == "__main__":
    main()
