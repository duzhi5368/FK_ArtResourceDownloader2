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
    def GetSavePathImp(cls, taskItem:FKTaskItem):
        boardName = NormalizeName(taskItem.image.meta['board_name'])
        savePath = os.path.join(taskItem.baseSavePath, boardName)
        os.makedirs(savePath, exist_ok=True)
        savePath = os.path.join(savePath, taskItem.image.name)
        savePath = NormalizePath(savePath)
        return savePath
    
    @Retry()
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
        savePath = self.GetSavePathImp(taskItem)
        if os.path.exists(savePath):
            return
        with open(savePath, "wb") as f:
            f.write(content)

#================================================================
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

def GetBoards(userMeta):
    boards = []
    for board in userMeta['boards']:
        meta = {
            "board_id": board['board_id'],
            "title": board['title'],
            "pins": None,
            "pin_count": board['pin_count'],
            "dir_name": NormalizeFileName(board['title']),
        }
        boards.append(board)
    return boards

def CreatePins(pinMeta):
    url = pinMeta["url"]
    filename = u"{title}.{ext}".format(title=pinMeta['pin_id'], ext=pinMeta['ext'])
    return Pin(url=url, filename=filename)

#================================================================
class Board(object):
    def __init__(self, boardUrlOrId):
        boardId = str(boardUrlOrId)
        self.fetcher = FKHuabanFetcher()
        if "http"  in boardId:
            boardId = re.findall(r'boards/(\d+)', boardId)[0]
        self.id = boardId
        path = "/boards/{boardId}".format(boardId=boardId)
        self.baseUrl = urljoin(BASE_URL, path)
        self.furtherPinUrlTpl = urljoin(self.baseUrl, "?{randomString}&max={pinId}&limit=20&wfl=1")
        self.pinCount = None
        self.title = None
        self.description = None
        self.pins = []
        self.FetchHome()

    def FetchHome(self):
        resp = self.fetcher.Get(self.baseUrl, requireJson=True)
        resp = resp.json()
        board = resp['board']
        self.pinCount = board['pin_count']
        self.title = board['title']
        self.description = board['description']
        return GetPins(board)

    def FetchFurther(self, prevPins):
        if len(prevPins) == 0:
            errorFormat = (
                "prebPins 不应当为空数组, "
                "标题: %s, "
                "路径: %s, "
                "PIN图总数: %s, "
                "当前PIN图: %s, "
            )
            FKLogger.error(errorFormat % (self.title, self.baseUrl, self.pinCount, pformat(self.pins)))
            return []
        maxId = prevPins[-1]['pin_id']
        furtherUrl = self.furtherPinUrlTpl.format(pinId=maxId, randomString=RandomString(8))
        resp = self.fetcher.Get(furtherUrl, requireJson=True)
        content = resp.json()
        return GetPins(content['board'])
    
    def FetchPins(self):
        assert len(self.pins) == 0
        self.pins.extend(self.FetchHome())
        for pin in self.pins:
            yield pin
        while self.pinCount > len(self.pins):
            furtherPins = self.FetchFurther(self.pins)
            if len(furtherPins) <= 0:
                break
            self.pins.extend(furtherPins)
            for pin in furtherPins:
                yield pin
    
    @property
    def Pins(self):
        yield from self.FetchPins()
    
    def ToString(self):
        return {
            "pins": self.Pins,
            "title": self.title,
            "description": self.description,
            "pin_count": self.pinCount,
        }

#================================================================
class User(object):
    def __init__(self, userUrl:str):
        self.fetcher = FKHuabanFetcher()
        if "http"  in userUrl:
            urlPath = userUrl.replace('/user/', '/')
        else:
            urlPath = BASE_URL + "/" + userUrl
        self.baseUrl = urlPath
        self.furtherUrlTpl = urljoin(self.baseUrl, "?{randomString}&max={boardId}&limit=10&wfl=1")
        self.username = None
        self.boardCount = None
        self.pinCount = None
        self.boardMetas = []
        self.FetchHome()
    
    def FetchHome(self):
        resp = self.fetcher.Get(self.baseUrl, requireJson=True)
        userMeta = resp.json()['user']
        self.username = userMeta['username']
        self.boardCount = userMeta['board_count']
        self.pinCount = userMeta['pin_count']
        return GetBoards(userMeta)
    
    def FetchFurther(self, prevBoards):
        maxId = prevBoards[-1]['board_id']
        furtherUrl = self.furtherUrlTpl.format(randomString=RandomString(8), boardId=maxId)
        resp = self.fetcher.Get(furtherUrl, requireJson=True)
        content = resp.json()
        return GetBoards(content['user'])

    def FetchBoards(self):
        assert len(self.boardMetas) == 0
        self.boardMetas.extend(self.FetchHome())
        furtherBoards = self.boardMetas
        while True:
            for meta in furtherBoards:
                yield Board(meta['board_id'])
            if self.boardCount > len(self.boardMetas):
                furtherBoards = self.FetchFurther(self.boardMetas)
                self.boardMetas.extend(furtherBoards)
            else:
                break
    
    @property
    def Boaders(self):
        yield from self.FetchBoards()

    def ToString(self):
        return {
            "username": self.username,
            "board_count": self.boardCount,
            "boards": self.Boaders,
        }

#================================================================
class FKHuabanSite(FKBaseSite):
    Fetcher = FKHuabanFetcher()

    def __init__(self, userUrl):
        self.meta = None
        self.baseUrl = userUrl
        self.user = User(userUrl)
        self.boards = []
    
    @property
    def DirName(self):
        return self.user.username
    
    @property
    def BoardsPins(self):
        for board in self.user.Boaders:
            self.boards.append(board)
            for pin in board.Pins:
                yield board, pin
    
    @property
    def Tasks(self):
        for board, pinMeta in self.BoardsPins:
            pinItem = CreatePins(pinMeta)
            yield FKImageItem(url=pinItem.url, name=pinItem.filename, meta={'board_name': board.title}, pinMeta=pinMeta)
    
    def ToString(self):
        meta = self.user.ToString()
        meta['boards'] = [board.ToString() for board in self.boards]
        return meta

#================================================================
class FKHuabanBoard(FKBaseSite):
    Fetcher = FKHuabanFetcher()

    def __init__(self, boardUrl):
        self.baseUrl = boardUrl
        self.board = Board(self.baseUrl)

    @property
    def DirName(self):
        return NormalizeFileName("%s-%s" % (self.board.title, self.board.id))
    
    @property
    def Tasks(self):
        for pinMeta in self.board.Pins:
            pinItem = CreatePins(pinMeta)
            yield FKImageItem(url=pinItem.url, name=pinItem.filename, pinMeta=pinMeta)