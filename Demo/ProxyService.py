from twisted.internet.protocol import Protocol
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from utils.ProtocolUtils import ProtocolUtils

class Proxy(Protocol):

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        self.factory.proxys[str(self)] = self

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols - 1
        del self.factory.proxys[str(self)]

    def dataReceived(self, data):
        s = eval(data.decode('utf-8'))
        print('Proxy','dataReceived',s)
        if s['protocol'] == 'req_registprotocols':
            self.protocols = s['protocols']
            for pro in self.protocols:
                if pro not in self.factory.protocols.keys():
                    self.factory.protocols[pro] = self
                else:
                    s = {'protocol':'res_error','data':'duplication regist %s'%pro}
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
            protocol = self.factory.proxys[s['proxy']]
            protocol.transport.write(str(s).encode('utf-8'))
        
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