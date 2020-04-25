from twisted.internet.protocol import Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory,ReconnectingClientFactory
from twisted.python import log, logfile

from ProtocolUtils import ProtocolUtils

from LogUtils import LogUtils

class SvrProtocol(Protocol):
    def __init__(self,factory):
        self.factory = factory
        self.log = factory.log
        
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
        
        self.log.msg('SvrBase connectionMade', s)
        
        self.transport.write( str(s).encode('utf-8') )
        
    def dataReceived(self, data):
        req = eval(data.decode('utf-8'))
        self.log.msg('SvrBase dataReceived', req)
        
        s = req
        if ProtocolUtils.sign_verify(s):
            if s['protocol'] in self.factory.processes:
                res = self.factory.processes[s['protocol']](s)
                s = res
                
                #让代理能确认该回复是谁的消息
                s['proxy'] = req['proxy']      
            elif s['protocol'] == 'res_registprotocols':
                self.log.msg(s)
                if not s['success']:
                    reactor.stop()
                else:
                    return
        else:
            s ={'protocol':'res_error','data':'sign_verify failure'}

        #回复请求
        s = ProtocolUtils.sign_create(s)
        self.transport.write( str(s).encode('utf-8') )
        
    def connectionLost(self, reason):
        pass
        

class SvrBase(ReconnectingClientFactory):
    
    def __init__(self):
        self.processes = {}
        self.log = LogUtils(self.__class__)
    
    '''
    子类调用的业务接口:获取注册的协议内容 ('req_redistool',self._func_)
    其函数类型是 def _request_*(self, data): pass
    '''
    def _add_protocols(self, req, pro):
        self.processes[req] = pro
        return   
    
    def startedConnecting(self, connector):
        #forever retry
        self.resetDelay()

    def buildProtocol(self, addr):
        return SvrProtocol(self)

    def clientConnectionLost(self, connector, reason):
        self.log.msg(self.__class__,'clientConnectionLost and retry...')
        self.retry(connector)
        
    def clientConnectionFailed(self, connector, reason):
        self.log.err(self.__class__,'clientConnectionFailed and retry...')
        self.retry(connector)



if __name__ == '__main__':
        
    class SvrTest(SvrBase):
        def __init__(self):
            SvrBase.__init__(self)
            SvrBase._add_protocols(self,'req_test',self._request_test)

        def _request_test(self,data):
            return {'protocol':'res_test','data':'ok. got it.'}

    def test_server(ip='localhost'):
        reactor.connectTCP(ip, 18000, SvrTest())
        reactor.run()

    
    test_server()
    print('SvrBase done')