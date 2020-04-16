import os,sys,hashlib,time


class ProtocolUtils:
    @staticmethod
    def getClassName(obj):
        cls = obj.__class__
        #<class '__main__.SvrAdb'>
        name = str(cls)
        return name[(name.find(".")+1):name.rfind("'")]    
    
    @staticmethod
    def sign_create(protocol):
        timestamp = int(round(time.time()*1000))

        msg = '2222%d1111'%(timestamp)
        sign = hashlib.new('md5',msg.encode(encoding='utf-8')).hexdigest()

        protocol['timestamp'] = timestamp
        protocol['sign'] = sign
        return protocol    
    
    @staticmethod
    def sign_verify(protocol):
        signbk = protocol['sign']
        timestamp = protocol['timestamp']

        msg = '2222%d1111'%(timestamp)
        sign = hashlib.new('md5',msg.encode(encoding='utf-8')).hexdigest()

        return signbk == sign    
    
if __name__ == '__main__':
    protocol = {'protocol':'req_test','data':'123'}
    
    sp = ProtocolUtils.sign_create(protocol)
    res = ProtocolUtils.sign_verify(protocol)
    
    print(res)
    