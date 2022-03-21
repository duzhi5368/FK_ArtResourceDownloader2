import json
import queue
import time
from queue import Queue
from threading import Lock
from Utils.FKUtilsFunc import RunAsDaemonThread

class FKBrowserRequester:
    def __init__(self):
        self.recvQueue = Queue()
        self.sendQueue = Queue()
        self.thread = RunAsDaemonThread(self.StartRecv)
        self.lockRegistry = {}
        self.retRegistry = {}

    def StartRecv(self):
        while True:
            raw = self.recvQueue.get()
            retMeta = json.loads(raw)
            url = retMeta['request_url']
            data = retMeta['response']
            self.retRegistry[url] = data
            self.lockRegistry[url].release()
    
    def GetRequest(self, timeout=None):
        if timeout is not None:
            try:
                return self.sendQueue.get(timeout=timeout)
            except queue.Empty:
                return None
        return self.sendQueue.get()

    def SendRequest(self, url):
        self.lockRegistry[url] = Lock()
        self.lockRegistry[url].acquire()
        self.sendQueue.put(url)

    def SubmitResponse(self, resp):
        self.recvQueue.put(resp)
    
    def GetResponse(self, url, timeout=None):
        if timeout is None:
            got = self.lockRegistry[url].acquire()
        else:
            got = self.lockRegistry[url].acquire(timeout=timeout)        
        if got is None:
            return None
        ret = self.retRegistry[url]
        del self.retRegistry[url]
        del self.lockRegistry[url]
        return ret

    def SendAndWait(self, url, timeout=None, maxRetry=0):
        retried = 0
        while True:
            self.SendRequest(url)
            ret = self.GetResponse(url, timeout=timeout)
            if ret is None:
                retried += 1
                time.sleep(5)
            else:
                return ret
            if retried > maxRetry:
                return ValueError("访问url失败: %s" % url)