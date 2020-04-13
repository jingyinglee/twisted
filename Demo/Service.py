from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

class Echo(Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        
        s = "Welcome! There are currently %d open connections.\n" %(self.factory.numProtocols,)
        
        self.transport.write(s.encode('utf-8'))

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1

    def dataReceived(self, data):
        self.transport.write(data)    
        
class EchoFactory(Factory):
    def __init__(self):
        self.numProtocols = 0
    def buildProtocol(self, addr):
        return Echo(self)

        
class QOTD(Protocol):

    def connectionMade(self):
        self.transport.write("An apple a day keeps the doctor away\r\n".encode('utf-8'))
        self.transport.loseConnection()
        
class QOTDFactory(Factory):
    def buildProtocol(self, addr):
        return QOTD()

# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
#endpoint.listen(QOTDFactory())
endpoint.listen(EchoFactory())
reactor.run()        
stdout.write('service done')