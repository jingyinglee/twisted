from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from utils.ProtocolUtils import ProtocolUtils

class Echo(Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        
        #s = "Welcome! There are currently %d open connections.\n" %(self.factory.numProtocols,)
        #self.transport.write(s.encode('utf-8'))

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1

    def dataReceived(self, data):
        s = eval(data.decode('utf-8'))
        s['ext'] = self.factory.numProtocols
        
        if not ProtocolUtils.sign_verify(s):
            s = {'protocol':'res_error','data':'sign_verify failure'}
            
        s = ProtocolUtils.sign_create(s)
        self.transport.write(str(s).encode('utf-8'))
        
class EchoFactory(Factory):
    def __init__(self):
        self.numProtocols = 0
    def buildProtocol(self, addr):
        return Echo(self)



# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 18000)
#endpoint.listen(QOTDFactory())
endpoint.listen(EchoFactory())
reactor.run()        
stdout.write('service done')