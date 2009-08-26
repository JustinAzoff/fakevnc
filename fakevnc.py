#!/usr/bin/env python

from twisted.internet import protocol, reactor
from twisted.protocols import basic
import struct
import datetime

import logging

def setup_logger():
    x = logging.getLogger("fakevnc")
    x.setLevel(logging.INFO)
    h1 = logging.FileHandler("/var/log/fakevnc/fakevnc.log")
    f = logging.Formatter("%(asctime)s %(message)s", datefmt="%b %d %H:%M:%S")
    h1.setFormatter(f)
    h1.setLevel(logging.INFO)
    x.addHandler(h1)
    return x

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

class VNCProtocol(basic.LineReceiver):
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
        msg = ["fakevnc: TCP Connection from", "fakevnc: VNC Connection from"][self.got_protocol]

        self.factory.logger.info("%s %s" % (msg, self.transport.getPeer().host))
        self.transport.loseConnection()

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
            self.factory.logger.info("fakevnc: VNC Auth attempt from %s" % self.transport.getPeer().host)
            self.go_away() 

class VNCFactory(protocol.ServerFactory):
    protocol = VNCProtocol
    logger = setup_logger()

def main():
    reactor.listenTCP(5900, VNCFactory())
    reactor.run()

if __name__ == "__main__":
    main()
