from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from twisted.internet.protocol import ClientFactory
from ProtocolUtils import ProtocolUtils

class BusBase(Protocol):
    def __init__(self,factory):
        self.factory = factory
   
    def connectionMade(self):
        s = ProtocolUtils.sign_create(self.factory.request)
        
        #print('BusBase write', request)
        
        self.transport.write( str(s).encode('utf-8') )
        
    def dataReceived(self, data):
        
        s = eval(data.decode('utf-8'))
        if ProtocolUtils.sign_verify(s):
            if 'res_error' == s['protocol']:
                self.factory.success = False
                self.factory.reason = s['data']
            else:
                self.factory.success = True
                self.factory.data = s
        else:
            self.factory.success = False
            self.factory.reason = 'sign_verify failure'
        #简单客户端，请求一次就断开了
        reactor.stop()
        
    def connectionLost(self, reason):
        #一般是被dataReceived中的stop已经给关闭了，所以这里判断下。
        if reactor.running:
            reactor.stop()
        

class BusClientFactory(ClientFactory):
    def __init__(self, request):
        self.success = False
        self.request = request
    
    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, addr):
        return BusBase(self)

    def clientConnectionLost(self, connector, reason):
        pass
        
    def clientConnectionFailed(self, connector, reason):
        #print('client connection failed. Reason:', reason)
        self.success = False
        self.reason = reason
        #简单客户端，请求一次就断了
        reactor.stop()


def request_callback(request, successCallback, failureCallback=None, ip='localhost'):
    factory = BusClientFactory(request)
    reactor.connectTCP(ip, 18000, factory)
    reactor.run()
    #print(reactor.__dict__.keys())
    
    if factory.success:
        successCallback(factory.data)
        return factory.data
    else:
        s = {'protocol':'res_error','data':factory.reason}
        if failureCallback:
            failureCallback(s)
        return s
    

if __name__ == '__main__':
    request = {'protocol':'req_test'}
    
    request_callback(request, successCallback=lambda x:print('success',x), failureCallback=lambda x:print('faulure',x))