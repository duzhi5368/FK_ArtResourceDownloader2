class FKTaskCounter:
    def __init__(self, total = 0):
        self.total = total
        self.done = 0
    
    def OnChange(self):
        print(self.ToString(), end='\r', flush=True)
    
    def IncrementDone(self):
        self.done += 1
        self.OnChange()
    
    def IncrementTotal(self):
        self.total += 1
        self.OnChange()
    
    def ToString(self):
        return "总数: %s, 已完成: %s" % (self.total, self.done)
