from fakevnc import *

from twisted.internet.protocol import Protocol, ClientCreator


class FakeVncMemoryLogBackend:
    implements([IFakeVncBackend])

    def __init__(self):
        self.msgs = []

    def gotTcpConnection(self, host):
        self.msgs.append("fakevnc: TCP Connection from %s" % host)
    def gotVncConnection(self, host):
        self.msgs.append("fakevnc: VNC Connection from %s" % host)
    def gotVncAuthAttempt(self, host):
        self.msgs.append("fakevnc: VNC Auth attempt from %s" % host)


class NoSender(Protocol):
    def connectionMade(self):
        self.transport.loseConnection()

class RFBSender(Protocol):
    def connectionMade(self):
        self.transport.write("RFB 0123\r\n")
        self.transport.loseConnection()

class RFBAuth(Protocol):
    def connectionMade(self):
        self.transport.write("RFB 0123\r\n")
        def auth():
            self.transport.write("X" + "Z" * 16 + "\r\n")
            self.transport.loseConnection()
        reactor.callLater(1, auth)

def test_fakevnc():
    backend = FakeVncMemoryLogBackend()
    reactor.listenTCP(5900, IFakeVncFactory(backend))
    
    def plain_connect():
        c = ClientCreator(reactor, NoSender)
        c.connectTCP("localhost", 5900)

    def rfb_connect():
        c = ClientCreator(reactor, RFBSender)
        c.connectTCP("localhost", 5900)

    def rfb_auth():
        c = ClientCreator(reactor, RFBAuth)
        c.connectTCP("localhost", 5900)

    reactor.callLater(1, plain_connect)
    reactor.callLater(2, rfb_connect)
    reactor.callLater(3, rfb_auth)

    reactor.callLater(5, reactor.stop)
    reactor.run()

    #reactor doesn't support restarting...
    print backend.msgs
    yield case_tcp_connection, backend
    yield case_vnc_connection, backend
    yield case_vnc_auth, backend

def case_tcp_connection(backend):
    """Test that a plain TCP connection is logged"""
    assert 'TCP Connection' in backend.msgs[0]

def case_vnc_connection(backend):
    """Test that a VNC connection is logged"""
    assert 'VNC Connection' in backend.msgs[1]

def case_vnc_auth(backend):
    """Test that a VNC auth attempt is logged"""
    assert 'VNC Auth attempt' in backend.msgs[2]
