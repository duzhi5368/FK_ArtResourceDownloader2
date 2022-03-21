class FKBaseSite:
    @property
    def DirName(self):
        raise NotImplementedError
    
    @property
    def Fetcher(self):
        raise NotImplementedError

    @property
    def Tasks(self):
        raise NotImplementedError