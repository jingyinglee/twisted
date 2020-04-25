
def _twisted_log(name):
    '''
    使用该方法时，目前标准输出流也会被截获，输入至日志文件
    '''
    from twisted.python import log , logfile
    #开启本地日志
    import os    
    output = 'output%slog%s%s'%(os.sep,os.sep,name[:name.find('.')])
    if not os.path.isdir(output):
        os.makedirs(output)

    #限定最多10个日志文件，每个不大于1M
    f = logfile.LogFile(name, output, maxRotatedFiles=10)
    log.startLogging(f)     
   
    return log 

def _base_log(name):
    '''
    直接输出打印的
    '''
    import time
    
    class base():
        def __init__(self,name):
            self.name = name
            
        def msg(self,value='', sep=' ', end='\n'):
            print(time.strftime("%Y%D%m %H%M%S"),self.name,end=' ==> ')
            print(value,sep,end)
        
        def err(self,value='', sep=' ', end='\n'):
            print(self.name,end=' ==> ')
            print(value,sep,end)
    
    return base(name)

def LogUtils(name, debug=False):
    
    #如果输入的是类名，则自动修改名称下。
    name = str(name)
    #print(name)
    #<class '__main__.SvrAdb'> 转成：SvrAdb.log
    if name.startswith("<class '"):
        name = name[(name.find(".")+1):name.rfind("'")] 
        name += '.log'

    if debug:
        return _base_log(name)   
    else:
        return _twisted_log(name)
    #
 
    

