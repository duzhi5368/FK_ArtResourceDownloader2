import os
import json

from urllib.parse import urlparse
import lxml.html as html

from Core.FKTaskItem import FKImageItem, FKTaskItem
from GUI.FKUITookits import FKMessageInfo
from Site.FKBaseFetcher import FKBaseFetcher
from Site.FKBaseSite import FKBaseSite
from Utils.FKUtilsFunc import NormalizePath
#================================================================

# todo : 地址可能要按国家区分
BASE_URL = "https://www.pinterest.com"
FETCH_BOARD_URL = BASE_URL + "/resource/BoardFeedResource/get"
FETCH_BOARD_SECTION_URL = BASE_URL + "/resource/BoardSectionPinsResource/get"
XHR_HEADERS = {
    "Host": "www.pinterest.com",
    "Referer": "https://www.pinterest.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/70.0.3538.113 "
        "Safari/537.36 "
        "Vivaldi/2.1.1337.51"
    ),
    "X-APP-VERSION": "ab1af2a",
    "X-B3-SpanId": "183fc9cb02974b",
    "X-B3-TraceId": "14f603d2caa27c",
    "X-Pinterest-AppState": "active",
    "X-Requested-With": "XMLHttpRequest",
}

#================================================================
class FKPinterestFetcher(FKBaseFetcher):
    def __init__(self, **kwargs):
        super(FKPinterestFetcher, self).__init__(**kwargs)
        self.session.headers.update(XHR_HEADERS)

    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKPinterestFetcher, self).Save(content, taskItem)
        image = taskItem.image
        savePath = os.path.join(taskItem.baseSavePath, image.meta['dir_name'])
        os.makedirs(savePath, exist_ok=True)
        savePath = NormalizePath(savePath)
        savePath = os.path.join(savePath, image.name)
        if os.path.exists(savePath):
            return
        with open(savePath, "wb") as f:
            f.write(content)

#================================================================
class FKPinterestSite(FKBaseSite):
    def __init__(self, url:str):
        self.fetcher = FKPinterestFetcher()
        self.userName = urlparse(url).path[1:]
        self.userName, _, _ = self.userName.partition('/')
        paths = self.GetUserBoardPaths(self.userName)
        self.boardsInfo = [self.GetBoardInfo(path) for path in paths]
        self.FetchBoardsList()

    @property
    def Fetcher(self):
        return self.fetcher

    @property
    def DirName(self):
        return self.userName

    @property
    def Tasks(self):
        yield from self.FetchBoardsList()

    def GetUserBoardPaths(self, userName):
        allBoards = self.GetUserBoards(userName)
        return [board["url"][1:-1] for board in allBoards]
    
    def GetUserBoards(self, userName):
        response = self.fetcher.Get((BASE_URL + "/{}/").format(userName))
        root = html.fromstring(response.content)
        rootPath = root.xpath("//script[@id='initial-state']")
        if len(rootPath) <= 0:
            FKMessageInfo("解析Pinterest网站数据失败，可能是因为国家区分网站导致的。")
            raise
        tag = rootPath[0]
        initialData = json.loads(tag.text)
        boardsResource = [
        resource for resource in initialData['resourceResponses']
        if resource['name'] == 'UserProfileBoardResource']
        if boardsResource:
            boards = boardsResource[0]['response']['data']
        return boards
    
    def GetBoardInfo(self, boardName):
        response = self.fetcher.Get((BASE_URL + "/{}/").format(boardName))
        root = html.fromstring(response.content)
        tag = root.xpath("//script[@id='initial-state']")[0]
        initialData = json.loads(tag.text)
        boardInfo = None
        if "resourceResponses" in initialData:
            boardInfo = initialData["resourceResponses"][0]["response"]["data"]
            try:
                sections = [
                    (section["slug"], section["id"])
                    for section in (
                        initialData.get("resourceResponses")[2].get("response").get("data")
                    )
                ]
                boardInfo["sections"] = sections
            except (IndexError, KeyError) as _:
                pass
        elif "resources" in initialData:
            boardInfo = (initialData.get('resources').get('data').get('BoardPageResource'))
            boardInfo = boardInfo[list(boardInfo.keys())[0]]['data']
        return 
        
    def FetchImageInfo(self, url, boardUrl, options):
        bookmark = None
        images = []
        while bookmark != '-end-':
            if bookmark:
                options.update({"bookmarks": [bookmark]})
            resp = self.fetcher.Get(url, params={
                "source_url": boardUrl,
                "data":json.dumps({"options": options, "context":{}})
            })
            data = resp.json()
            images += data["resource_response"]["data"]
            bookmark = data['resource']['options']['bookmarks'][0]
        return images

    def FetchBoardsList(self):
        imagesDic = {}
        for board in self.boardsInfo:
            saveDir = os.path.join(*board["url"][1:-1].split("/"))
            imagesDic[saveDir] = self.FetchImageInfo(url=FETCH_BOARD_URL, boardUrl=board['url'],
                options={"board_id": board["id"], "page_size":25})
            for section, sectionId in (board.get("sections") or ()):
                saveDir = os.path.join(os.path.join(*board['url'][1:-1].split("/")), section)
                imagesDic[saveDir] = self.FetchImageInfo(url=FETCH_BOARD_SECTION_URL, boardUrl=board["url"], 
                    options={"section_id": sectionId, "page_size":25})
            for saveDir, images in imagesDic.items():
                for i, image in enumerate(images, 1):
                    imageId = image['id']
                    if 'images' in image:
                        url = image['image']['orig']['url']
                        baseName = os.path.basename(url)
                        _, ext = baseName.split(".")
                        fileName = "{}.{}".format(str(imageId), ext)
                        yield FKImageItem(url=url, name=fileName, meta={'dir_name': saveDir})


            

    