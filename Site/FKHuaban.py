import imp
import mimetypes
import re
import os
import string
import random

from json import JSONDecodeError
from pprint import pformat
from typing import NamedTuple
from urllib.parse import urljoin

from Utils.FKLogger import FKLogger
from Core.FKTaskItem import FKImageItem, FKTaskItem
from Site.FKBaseSite import FKBaseSite
from Site.FKBaseFetcher import FKBaseFetcher
from Utils.FKUtilsFunc import NormalizeFileName, NormalizeName, NormalizePath, Retry
#================================================================
IMAGE_URL_TPL = "http://img.hb.aicdn.com/{file_key}"
BASE_URL = "http://huaban.com"
XHR_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/56.0.2924.87 Safari/537.36",
}

#================================================================
class Pin(NamedTuple):
    url: str
    filename: str

#================================================================
class FKHuabanFetcher(FKBaseFetcher):
    def __init__(self):
        super(FKHuabanFetcher, self).__init__()
        self.session.headers.update(XHR_HEADERS)
    
    @classmethod
    def GetSavePath(cls, taskItem):
        boardName = NormalizeName(taskItem.image.meta['board_name'])
        savePath = os.path.join(taskItem.baseSavePath, boardName)
        os.makedirs(savePath, exist_ok=True)
        savePath = os.path.join(savePath, taskItem.image.name)
        savePath = NormalizePath(savePath)
        return savePath
    
    @Retry
    def Get(self, url, requireJson=False, **kwargs):
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        resp = self.session.get(url, timeout=(2, 30), **kwargs)
        if requireJson:
            try:
                resp.json()
            except JSONDecodeError:
                FKLogger.error("转换 URL {} 的响应为json失败: {}".format(url, resp.text))
                raise
        return resp
    
    def Save(self, content, taskItem: FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKHuabanFetcher, self).Save(content, taskItem)
        savePath = self.GetSavePath()
        with open(savePath, "wb") as f:
            f.write(content)
    
def RandomString(length):
    return ''.join(
        random.choice(string.ascii_lowercase + string.digits)
        for _ in range(length)
    )
    
def GetFileExt(mimeType):
    return mimeType.split("/")[-1]

def GetPins(boardDict):
    board = boardDict
    pins = []
    for info in board['pins']:
        ext = GetFileExt(info['file']['type'])
        fileName = "%s.%s" % (info['pin_id'], ext)
        meta = {
            "pin_id": info['pin_id'],
            "url": IMAGE_URL_TPL.format(file_key=info['file']['key']),
            'type': info['file']['type'],
            'ext': ext,
            "title": info['raw_text'],
            "link": info['link'],
            "source": info['source'],
            "file_name": fileName,
            "tags": info['tags'],
        }
        pins.append(meta)
    return pins
