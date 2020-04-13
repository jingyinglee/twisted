from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from twisted.internet.protocol import ClientFactory
from sys import stdout

class Echo(Protocol):
    def dataReceived(self, data):
        stdout.write(data.decode('utf-8'))
        
    def connectionLost(self, reason):
        print('Lost connection.  Reason:', reason)

class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print('client lost connection.  Reason:', reason)
        reactor.stop()
        
    def clientConnectionFailed(self, connector, reason):
        print('client connection failed. Reason:', reason)
        
        

reactor.connectTCP("localhost", 8007, EchoClientFactory())
reactor.run()
stdout.write('client done')