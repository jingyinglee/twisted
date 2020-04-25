import time

from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor, task


from utils.ProtocolUtils import ProtocolUtils,HeartBeatSTime
from utils.LogUtils import LogUtils


log = LogUtils('proxyservice.log')

class Proxy(Protocol):

    def __init__(self, factory):
        self.factory = factory
        self.protocols = []

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        self.factory.proxys[str(self)] = self
        self.factory.heartbeats[str(self)] = time.time()

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1
        #释放自己的信息
        del self.factory.proxys[str(self)]
        #释放自己注册的协议（服务端）
        for pro in self.protocols:
            del self.factory.svrProtocols[pro]
            log.msg('Proxy','connectionLost svr',pro)
            
            #todo 如果服务端关闭了，那么其对应的请求端也应该要关闭它
            for protocol in self.factory.busProtocols[pro]:
                log.msg('Proxy','connectionLost bus',protocol)
                protocol.transport.abortConnection()
        
        #释放自己请求的协议（客户端）
        for pro,protocols in self.factory.busProtocols.items():
            if self in self.factory.busProtocols[pro]:
                self.factory.busProtocols[pro].remove(self)
        

    def dataReceived(self, data):
        s = eval(data.decode('utf-8'))
        
        if s['protocol'] != 'req_heartbeat':
            log.msg('Proxy','dataReceived',s)
            
        if s['protocol'] == 'req_heartbeat':
            self._update_heartbeat()
        elif s['protocol'] == 'req_registprotocols':
            self._process_registprotocols(s)     
        elif s['protocol'].startswith('req_'):
            self._process_request(s)
        elif s['protocol'].startswith('res_'):
            self._process_respone(s)
            
        
                
    def _process_registprotocols(self,s):
        '''
        处理协议的注册
        '''
        if s['protocol'] == 'req_registprotocols':
            #之前没注册过，就可以注册
            if not (set(s['protocols']) & set(self.factory.svrProtocols.keys())):
                log.msg('Proxy','req_registprotocols', s['protocols'])
                for pro in s['protocols']:
                    self.factory.svrProtocols[pro] = self
                #备注当前协议是被注册过的，方便释放时释放
                self.protocols = s['protocols']
                s = {'protocol':'res_registprotocols','success':True}
            else:
                s = {'protocol':'res_registprotocols','success':False,'data':'duplication regist %s'%(s['protocols'])}
            s = ProtocolUtils.sign_create(s)
            self.transport.write(str(s).encode('utf-8'))   
            return True
        else:
            return False
        
    def _process_request(self,s):
        '''
        某客户端有请求消息，这边找到之前有注册过的协议并转发其请求
        '''
        if s['protocol'].startswith('req_'):
            if not self.factory.busProtocols.__contains__(s['protocol']):
                self.factory.busProtocols[s['protocol']] = set()
            self.factory.busProtocols[s['protocol']].add(self)
            
            if not self.factory.svrProtocols.__contains__(s['protocol']):
                s = {'protocol':'res_error','data':'process %s is not be regist.'%s['protocol']}
                s = ProtocolUtils.sign_create(s)
                self.transport.write(str(s).encode('utf-8'))                 
            else:
                #转发该协议
                protocol = self.factory.svrProtocols[s['protocol']]
                s['proxy'] = str(self)#标记是该代理的请求
                protocol.transport.write(str(s).encode('utf-8'))      
                
            return True
        else:
            return False
        
    def _process_respone(self,s):
        '''
        某服务有响应消息回执了，这边找到之前的请求，并回调其具体响应内容
        '''
        if s['protocol'].startswith('res_'):
            #收到之前转的协议的回调了
            if 'proxy' in s and s['proxy'] in self.factory.proxys:
                protocol = self.factory.proxys[s['proxy']]
                del s['proxy']
                protocol.transport.write(str(s).encode('utf-8'))
            else:
                log.err('miss respone',str(s))
            return True
        else:
            return False
        
    def _update_heartbeat(self):
        self.factory.heartbeats[str(self)] = time.time()
        
class ProxyFactory(Factory):
    def __init__(self):
        self.numProtocols = 0
        #各注册协议的具体Protocol实例 {ProtocolName:Protocol}
        self.svrProtocols = {}
        #各请求协议的具体Protocols实例 {ProtocolName:[Protocol]}
        self.busProtocols = {}
        #记录各连接的实例，方便对请求端响应其回调 {str(Protocol):Protocol}
        self.proxys = {}
        #记录各连接的心跳时间，判断是否超时 {str(Protocol):time}
        self.heartbeats = {}
    def buildProtocol(self, addr):
        return Proxy(self)
    
    def checkHeartbeat(self):
        '''
        检测各连接的心跳，如果超时，则中断其连接
        '''
        for flag,protocol in self.proxys.items():
            if flag in self.heartbeats:
                endTime = self.heartbeats[flag]
                if time.time() - endTime > 3*HeartBeatSTime:
                    log.msg('%s heartbeat lost'%flag)
                    protocol.transport.abortConnection()


# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 18000)

factory = ProxyFactory()

tk = task.LoopingCall(factory.checkHeartbeat)
tk.start(HeartBeatSTime,now=False)

endpoint.listen(factory)
reactor.run()        
stdout.write('proxy service done')