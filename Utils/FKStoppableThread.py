from threading import Thread
from queue import Empty

class FKStoppableThread(Thread):

    def __init__(self, queue, taskFunc):
        super(FKStoppableThread, self).__init__()
        self.taskFunc = taskFunc
        self.queue = queue
        self.daemon = True
        self.isStopped = False

    def Run(self):
        while not self.isStopped:
            try:
                workerTask =  self.queue.get(timeout=0.2)
            except Empty:
                continue
            else:
                args = workerTask.args or ()
                kwargs = workerTask.kwargs or {}
                self.taskFunc(*args, **kwargs)
                self.queue.task_done()
    
    def Stop(self):
        self.isStopped = True
