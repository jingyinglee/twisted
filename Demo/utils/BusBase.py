from twisted.internet.protocol import Protocol
from twisted.internet import reactor, task
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory

from ProtocolUtils import ProtocolUtils, HeartBeatSTime

from LogUtils import LogUtils

class BusProtocol(Protocol):
    def __init__(self,factory):
        self.factory = factory
        self.log = factory.log
        
        tk = task.LoopingCall(self._heartbeat)
        tk.start(HeartBeatSTime,now=False)
   
    def connectionMade(self):
        s = ProtocolUtils.sign_create(self.factory.request)
        
        self.log.msg('BusBase write', request)
        
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
            self.factory.reason = reason
            reactor.stop()
        
    def _heartbeat(self):
        request = {'protocol':'req_heartbeat','from':str(self.factory.__class__)}
       
        s = ProtocolUtils.sign_create(request)
        #self.log.msg('BusBase _heartbeat', s)
        self.transport.write( str(s).encode('utf-8') )    

class BusBase(ClientFactory):
    def __init__(self, request):
        self.success = False
        self.request = request
        self.log = LogUtils(self.__class__, debug=True)
    
    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, addr):
        return BusProtocol(self)

    def clientConnectionLost(self, connector, reason):
        pass
        
    def clientConnectionFailed(self, connector, reason):
        self.log.err('client connection failed. Reason:', reason)
        self.success = False
        self.reason = reason
        #简单客户端，请求一次就断了
        reactor.stop()


def request_callback(request, successCallback, failureCallback=None, ip='localhost'):
    factory = BusBase(request)
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
    
    request_callback(request, 
                     successCallback=lambda x:print('success',x),
                     failureCallback=lambda x:print('faulure',x))
    print('BusBase done')