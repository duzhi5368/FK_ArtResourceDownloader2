import os
import time

from queue import Queue
from functools import wraps

from Utils.FKStoppableThread import FKStoppableThread
from Utils.FKUtilsFunc import RunAsDaemonThread
from Utils.FKLogger import FKLogger
from Site.FKBaseFetcher import FKBaseFetcher
from Core.FKTaskItem import FKTaskItem, FKWorkerTask
from Core.FKTaskCounter import FKTaskCounter

def CreateDownloadThenSave(fetcher : FKBaseFetcher):

    def downloadThenSave(taskItem: FKTaskItem):
        response = fetcher.Get(taskItem.image.url)
        if response is None:
            FKLogger.error("下载图片：%s 失败" % taskItem.image.url)
            return
        fetcher.Save(response.content, taskItem)
        return True

    return downloadThenSave

class FKDownloader:
    def __init__(self, fetcher, workerNum = 5, saveDir = '.'):
        self.saveDir = saveDir
        self.workerNum = workerNum
        self.downloadQueue = Queue()
        self.counter = FKTaskCounter()
        self.isDone = False
        self.isStop = False
        self.isAllTaskAdded = False

        self.EnsureDir()

        def CounterWrapper(func):
            @wraps(func)
            def wrapped(taskItem):
                ret = func(taskItem=taskItem)
                self.counter.IncrementDone()
                return ret
            return wrapped

        downloadThenSave = CreateDownloadThenSave(fetcher)
        taskFunc = CounterWrapper(downloadThenSave)

        self.downloadWorkders = [FKStoppableThread(self.downloadQueue, taskFunc) for _ in range(workerNum)]
        self.StartDaemons()

    def EnsureDir(self):
        if not os.path.exists(self.saveDir):
            os.mkdir(self.saveDir)
    
    def StartDaemons(self):
        for worker in self.downloadWorkders:
            worker.start()

    def AddTask(self, taskIter, background = False):
        if background:
            RunAsDaemonThread(self.AddTaskImp, taskIter)
        else:
            self.AddTaskImp(taskIter)
        
    def AddTaskImp(self, taskIter):
        for image in taskIter:
            if self.isStop:
                break
            taskItem = FKTaskItem(image=image, baseSavePath=self.saveDir)
            self.counter.IncrementTotal()
            self.downloadQueue.put(FKWorkerTask(kwargs={'taskItem': taskItem}))
            #print("==[debug]== add %d" % self.downloadQueue.qsize())
        self.isAllTaskAdded = True
    
    def Join(self, background = False):
        def run():
            self.downloadQueue.join()
            while not self.isAllTaskAdded:
                time.sleep(0.2)
                self.downloadQueue.join()
                #print("==[debug]== join %d" % self.downloadQueue.qsize())
            self.isDone = True
        
        if background:
            RunAsDaemonThread(run)
        else:
            run()

    def Stop(self):
        self.isStop = True
        for worker in self.downloadWorkders:
            worker.Stop()
        for worker in self.downloadWorkders:
            worker.join()

    @property
    def TaskaAllAdded(self):
        return self.isAllTaskAdded

    @property
    def Stopped(self):
        return self.isStop
    
    def ToString(self):
        return self.counter.ToString()