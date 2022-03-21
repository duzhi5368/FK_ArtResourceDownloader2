import os
import time

from queue import Queue
from functools import wraps

from Utils.FKStoppableThread import FKStoppableThread
from Utils.FKUtilsFunc import DownloadThenSave, RunAsDaemonThread
from Core.FKTaskItem import FKTaskItem, FKWorkerTask
from Core.FKTaskCounter import FKTaskCounter

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

        downloadThenSave = DownloadThenSave(fetcher)
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
            self.downloadQueue.put(FKWorkerTask(kwargs={'FKTaskItem': taskItem}))
        self.isAllTaskAdded = True
    
    def Join(self, background = False):
        def run():
            self.downloadQueue.join()
            while not self.isAllTaskAdded:
                time.sleep(0.2)
                self.downloadQueue.join()
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