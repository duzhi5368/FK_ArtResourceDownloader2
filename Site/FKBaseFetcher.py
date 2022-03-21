import os
import requests
from flask import request

from Core.FKTaskItem import FKImageItem
from Utils.Const import __FK_USER_AGENT__
from Utils.FKUtilsFunc import NormalizePath, Retry

class FKBaseFetcher:

    def __init__(self, proxies=None):
        self.session = requests.session()
        if proxies is not None:
            self.session.proxies = proxies
        self.session.headers.update(__FK_USER_AGENT__)

    @Retry
    def Get(self, url, **kwargs):
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        return self.session.get(url, timeout=(2, 30), **kwargs)
    
    def GetSavePath(self, basePath, imageName, image: FKImageItem):
        savePath = os.path.join(basePath, imageName)
        return savePath
    
    def Save(self, content, taskItem):
        image = taskItem.image
        imageName = image.name
        if callable(image.name):
            imageName = image.name(image.url, content)
        savePath = self.GetSavePath(basePath=taskItem.baseSavePath, imageName=imageName, image=image)
        savePath = NormalizePath(savePath)
        if os.path.exists(savePath):
            return
        with open(savePath, "wb") as f:
            f.write(content)
            f.flush