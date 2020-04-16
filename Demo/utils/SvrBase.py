from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from twisted.internet.protocol import ClientFactory
from ProtocolUtils import ProtocolUtils

class SvrBase(Protocol):
    def __init__(self,factory):
        self.factory = factory
        
    def getClassName(self):
        cls = self.__class__
        #<class '__main__.SvrAdb'>
        name = str(cls)
        return name[(name.find(".")+1):name.rfind("'")]        

   
    def connectionMade(self):
        #注册协议
        request = {'protocol':'req_registprotocols','from':str(self.__class__)}
        request['protocols'] = tuple(self.factory.processes.keys())        
        
        s = ProtocolUtils.sign_create(request)
        
        #print('SvrBase write', request)
        
        self.transport.write( str(s).encode('utf-8') )
        
    def dataReceived(self, data):
        
        req = eval(data.decode('utf-8'))
        s = req
        if ProtocolUtils.sign_verify(s):
            if s['protocol'] in self.factory.processes:
                res = self.factory.processes[s['protocol']](s)
                s = res
            else:
                s ={'protocol':'res_error','data':'%s not exist'%s['protocol']}
        else:
            s ={'protocol':'res_error','data':'sign_verify failure'}
        
        #让代理能确认该回复是谁的消息
        s['proxy'] = req['proxy']
        
        s = ProtocolUtils.sign_create(s)
        self.transport.write( str(s).encode('utf-8') )
        
    def connectionLost(self, reason):
        pass
        

class SvrClientFactory(ClientFactory):
    def __init__(self):
        self.processes = {}
    
    '''
    子类调用的业务接口:获取注册的协议内容 ('req_redistool',self._func_)
    其函数类型是 def _request_*(self, data): pass
    '''
    def _add_protocols(self, req, pro):
        self.processes[req] = pro
        return   
    
    def startedConnecting(self, connector):
        pass

    def buildProtocol(self, addr):
        return SvrBase(self)

    def clientConnectionLost(self, connector, reason):
        pass
        
    def clientConnectionFailed(self, connector, reason):
        #todo:need to retry
        print('SvrClientFactory',reason)



if __name__ == '__main__':
        
    class SvrTest(SvrClientFactory):
        def __init__(self):
            SvrClientFactory.__init__(self)
            SvrClientFactory._add_protocols(self,'req_test',self._request_test)
            
        def _request_test(self,data):
            return {'protocol':'res_test','data':'ok. got it.'}    
    
    def test_server(ip='localhost'):
        reactor.connectTCP(ip, 18000, SvrTest())
        reactor.run()
        #print(reactor.__dict__.keys())

    
    test_server()