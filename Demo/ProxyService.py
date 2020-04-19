from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from utils.ProtocolUtils import ProtocolUtils

class Proxy(Protocol):

    def __init__(self, factory):
        self.factory = factory
        self.protocols = []

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        self.factory.proxys[str(self)] = self

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1
        #释放自己的信息
        del self.factory.proxys[str(self)]
        #释放自己注册的协议
        for pro in self.protocols:
            del self.factory.protocols[pro]
            print('Proxy','connectionLost',pro)

    def dataReceived(self, data):
        s = eval(data.decode('utf-8'))
        print('Proxy','dataReceived',s)
        if s['protocol'] == 'req_registprotocols':
            #之前没注册过，就可以注册
            if not (set(s['protocols']) & set(self.factory.protocols.keys())):
                for pro in s['protocols']:
                    self.factory.protocols[pro] = self
                #备注当前协议是被注册过的，方便释放时释放
                self.protocols = s['protocols']
                s = {'protocol':'res_registprotocols','success':True}
            else:
                s = {'protocol':'res_registprotocols','success':False,'data':'duplication regist %s'%(s['protocols'])}
            s = ProtocolUtils.sign_create(s)
            self.transport.write(str(s).encode('utf-8'))       
        elif s['protocol'].startswith('req_'):
            if not self.factory.protocols.__contains__(s['protocol']):
                s = {'protocol':'res_error','data':'process %s is not be regist.'%s['protocol']}
                s = ProtocolUtils.sign_create(s)
                self.transport.write(str(s).encode('utf-8'))                 
            else:
                #转发该协议
                protocol = self.factory.protocols[s['protocol']]
                s['proxy'] = str(self)#标记是该代理的请求
                protocol.transport.write(str(s).encode('utf-8'))
        elif s['protocol'].startswith('res_'):
            #收到之前转的协议的回调了
            if 'proxy' in s:
                protocol = self.factory.proxys[s['proxy']]
                del s['proxy']
                protocol.transport.write(str(s).encode('utf-8'))
            else:
                print('miss',s)
        
class ProxyFactory(Factory):
    def __init__(self):
        self.numProtocols = 0
        self.protocols = {}
        self.proxys = {}
    def buildProtocol(self, addr):
        return Proxy(self)


# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 18000)
endpoint.listen(ProxyFactory())
reactor.run()        
stdout.write('proxy service done')