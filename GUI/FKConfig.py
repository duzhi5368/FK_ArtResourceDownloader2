import json
import os
from pathlib import Path
from Utils.Const import __CONFIG_FILE_PATH__

#================================================================
class FKAttrDic(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            return AttributeError(r"FKAttrDic 对象没有叫做 '%s' 的属性" % attr)
    
    def __setattr__(self, attr: str, value):
        self[attr] = value

#================================================================
class FKConfigStore(FKAttrDic):
    saveFilePath = Path(os.path.expanduser(__CONFIG_FILE_PATH__))

    @classmethod
    def LoadFromConfigFile(cls):
        path = Path(cls.saveFilePath)
        if not os.path.exists(path):
            return cls()
        with open(path, "rb") as f:
            return cls(**json.load(f))

    def __setattr__(self, attr: str, value):
        super(FKAttrDic, self).__setattr__(attr, value)
        self.Save()
    
    def Save(self):
        path = Path(self.saveFilePath)
        with open(path, "w") as f:
            json.dump(self, f)
    
    def OpStorePath(self, name, path):
        path = Path(path)
        self[name] = str(path)
        self.Save()
    
    def OpReadPath(self, name):
        path = self.get(name, None)
        return Path(path) if path is not None else None

#================================================================

FKConfig = FKConfigStore.LoadFromConfigFile()

__all__ = ("FKConfig")