import time
from random import randint
import sys

from twisted.internet.protocol import Protocol
from twisted.internet import reactor, task
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.protocol import ClientFactory,ReconnectingClientFactory
from twisted.python import log, logfile

from ProtocolUtils import ProtocolUtils, HeartBeatSTime
from LogUtils import LogUtils



class SvrProtocol(Protocol):
    def __init__(self,factory):
        self.factory = factory
        self.log = factory.log
        
        tk = task.LoopingCall(self._heartbeat)
        tk.start(HeartBeatSTime,now=False)

    def connectionMade(self):
        #注册协议
        request = {'protocol':'req_registprotocols','from':str(self.factory.__class__)}
        request['protocols'] = tuple(self.factory.processes.keys())        
        
        self._sendMsg(request)
        
    def dataReceived(self, data):
        req = eval(data.decode('utf-8'))
        self.log.msg('SvrBase dataReceived', req)
        
        def _process(data):
            self,req = data
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
            self._sendMsg(s)
        
        #考虑到服务这边一般是耗时操作，所以这里默认去线程中执行
        reactor.callInThread(_process,(self,req))
        
        
    def connectionLost(self, reason):
        pass
        
    def _heartbeat(self):
        request = {'protocol':'req_heartbeat','from':str(self.factory.__class__)}
        self._sendMsg(request)
           
    def _sendMsg(self, msg):
        def __send(data):
            protocol,msg = data
            s = ProtocolUtils.sign_create(msg)
            
            if s['protocol'] != 'req_heartbeat':
                protocol.log.msg('SvrBase write', s)
                
            protocol.transport.write( str(s).encode('utf-8') )     
            
        reactor.callFromThread( __send, (self,msg))

class SvrBase(ReconnectingClientFactory):
    
    def __init__(self, poolsize=5):
        self.processes = {}
        self.log = LogUtils(self.__class__)
        
        reactor.suggestThreadPoolSize(poolsize)
    
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
        def __init__(self, index):
            SvrBase.__init__(self)
            self.index = index
            SvrBase._add_protocols(self,'req_test%d'%self.index,self._request_test)

        def _request_test(self,data):
            recvTime = time.time()
            time.sleep(randint(1,4)*HeartBeatSTime)
            return {'protocol':'res_test%d'%self.index,'data':'ok. %d got it. '%recvTime}

    def test_server(index,ip='localhost'):
        reactor.connectTCP(ip, 18000, SvrTest(index))
        reactor.run()

    def test_mul():
        #压测时HeartBeatSTime可修改为1秒
        #bat测试： for /l %I in (0,1,50) do (start python SvrBase.py %I )
        print(sys.argv)
        test_server(index=int(sys.argv[1]))
    
    def test():
        test_server(index=0)
        
    test()
    #test_mul()
    print('SvrBase done')