import os
import requests
import json
import re
import time

from typing import NamedTuple
from urllib.parse import urljoin
from collections import Counter

from Core.FKTaskItem import FKImageItem, FKTaskItem
from Site.FKBaseSite import FKBaseSite
from Utils.FKUtilsFunc import GetNameWithHashFromUrl, NormalizeName, NormalizePath, FromatProxy
from Utils.Const import __FK_USER_AGENT__
from RPC.FKTaskServer import FKServer
from Site.FKBaseFetcher import FKBaseFetcher
#================================================================
BASE_URL = "https://www.artstation.com/"
PROJECT_URL_TPL = '/users/{username}/projects.json?page={page}'
ALBUMS_URL_TPL = 'https://www.artstation.com/albums.json?' \
                 'include_total_count=true&page={page}' \
                 '&per_page=25&user_id={user_id}'
ALBUM_CONTENT_URL_TPL = 'https://www.artstation.com/users/{username}' \
                        '/projects.json?album_id={album_id}&page={page}'
DETAIL_URL_TPL = '/projects/{hash_id}.json'
#================================================================
class ArtStationAlbum(NamedTuple):
    name: str
    id: str
#================================================================
"""
    {
        "liked":false,
        "tags":[

        ],
        "hide_as_adult":false,
        "visible_on_artstation":true,
        "assets":[
            {
                "has_image":true,
                "has_embedded_player":false,
                "player_embedded":null,
                "oembed":null,
                "id":12260469,
                "title_formatted":"",
                "image_url":"https://cdnb.artstation.com/p/assets/images/images/012/260/469/large/ham-sung-choul-braveking-180809-1-mini.jpg?1533864344",
                "width":1300,
                "height":2434,
                "position":0,
                "asset_type":"image",
                "viewport_constraint_type":"constrained"
            },
            {
                "has_image":false,
                "has_embedded_player":false,
                "player_embedded":null,
                "oembed":null,
                "id":12260473,
                "title_formatted":"",
                "image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/260/473/large/ham-sung-choul-braveking-180809-1-mini-2.jpg?1533864353",
                "width":822,
                "height":822,
                "position":1,
                "asset_type":"cover",
                "viewport_constraint_type":"constrained"
            }
        ],
        "collections":[

        ],
        "user":{
            "followed":true,
            "following_back":false,
            "blocked":false,
            "is_staff":false,
            "id":199106,
            "username":"braveking",
            "headline":"freelance artist",
            "full_name":"Ham Sung-Choul(braveking)",
            "permalink":"https://www.artstation.com/braveking",
            "medium_avatar_url":"https://cdna.artstation.com/p/users/avatars/000/199/106/medium/ab27ac7f48de117074c14963a3371914.jpg?1461412259",
            "large_avatar_url":"https://cdna.artstation.com/p/users/avatars/000/199/106/large/ab27ac7f48de117074c14963a3371914.jpg?1461412259",
            "small_cover_url":"https://cdn.artstation.com/static_media/placeholders/user/cover/default.jpg",
            "pro_member":false
        },
        "medium":null,
        "categories":[
            {
                "name":"Characters",
                "id":1
            },
            {
                "name":"Fantasy",
                "id":2
            },
            {
                "name":"Concept Art",
                "id":3
            }
        ],
        "software_items":[

        ],
        "id":3513664,
        "user_id":199106,
        "title":"doodle",
        "description":"<p></p>",
        "description_html":"<p></p>",
        "created_at":"2018-08-09T07:50:11.347-05:00",
        "updated_at":"2018-08-10T01:55:50.964-05:00",
        "views_count":3257,
        "likes_count":699,
        "comments_count":1,
        "permalink":"https://www.artstation.com/artwork/mr5aZ",
        "cover_url":"https://cdnb.artstation.com/p/assets/covers/images/012/260/473/medium/ham-sung-choul-braveking-180809-1-mini-2.jpg?1533864353",
        "published_at":"2018-08-09T07:50:19.308-05:00",
        "editor_pick":true,
        "adult_content":false,
        "admin_adult_content":false,
        "slug":"doodle-184-a5ea10f5-e98e-46e2-866e-63ae54fd443a",
        "suppressed":false,
        "hash_id":"mr5aZ",
        "visible":true
    }
    :rtype: list[ImageItem]
"""
def ParseSingleArtwork(dict: dict):
    assets = dict['assets']
    assets = [
        asset for asset in assets
        if asset['has_image']
    ]
    images = (
        FKImageItem(
            url = asset['image_url'],
            name = GetNameWithHashFromUrl
        )
        for asset in assets
    )
    return images

"""
    {
    "data":
        [
            {
                "id":3497866,
                "user_id":199106,
                "title":"doodle",
                "description":"",
                "created_at":"2018-08-06T04:23:20.695-05:00",
                "updated_at":"2018-08-10T01:39:27.162-05:00",
                "likes_count":340,
                "slug":"doodle-184-669828ca-6a1b-4fc7-986d-e4eeaa4b5d55",
                "published_at":"2018-08-06T04:24:58.518-05:00",
                "adult_content":false,
                "cover_asset_id":12192935,
                "admin_adult_content":false,
                "hash_id":"KnrbX",
                "permalink":"https://www.artstation.com/artwork/KnrbX",
                "hide_as_adult":false,
                "cover":{
                    "id":12192935,
                    "small_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/small/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "medium_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/medium/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "small_square_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/small_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "thumb_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/smaller_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "micro_square_image_url":"https://cdnb.artstation.com/p/assets/covers/images/012/192/935/micro_square/ham-sung-choul-braveking-180806-1-b-mini-3.jpg?1533547474",
                    "aspect":1
                },
                "icons":{
                    "image":false,
                    "video":false,
                    "model3d":false,
                    "marmoset":false,
                    "pano":false
                },
                "assets_count":1
            },
        ],
        "total_count":38
    }
"""
def ParseArtworkUrl(dict: dict):
    url = urljoin( BASE_URL, DETAIL_URL_TPL.format(hash_id = dict['hash_id']))
    return url

def GetProjectPageUrl(username, page=1):
    path = PROJECT_URL_TPL.format(username = username, page = page)
    url = urljoin(BASE_URL, path)
    return url

def GetProjectAlbumsPageUrl(user_id, page=1):
    path = ALBUMS_URL_TPL.format(user_id = user_id, page = page)
    url = urljoin(BASE_URL, path)
    return url

def GetProjectAlbumsDetailPageUrl(user_id, album_id, page=1):
    path = ALBUM_CONTENT_URL_TPL.format(user_id = user_id, album_id=album_id, page = page)
    url = urljoin(BASE_URL, path)
    return url

def HasNextPage(curPage, totalPage):
    return curPage < totalPage

#================================================================
class ArtStationBaseMetaFetcher:
    def RequestUrl(self, url):
        raise NotImplementedError
    
    def GetArtworkSummary(self, url):
        return self.RequestUrl(url)
    
    def GetAlbumsIndexPage(self, userId):
        page = 1
        curPage = 0
        totalPage = 1
        while curPage < totalPage:
            url = GetProjectAlbumsPageUrl(user_id=userId, page=page)
            resp = self.RequestUrl(url)
            if 'total_count' not in resp:
                return
            totalPage = resp['total_count']
            for albumDetail in resp['data']:
                yield ArtStationAlbum(id=albumDetail['id'], name=albumDetail['title'])
            curPage = len(resp['data'])
            page += 1
        
    def GetAlbumProjectsSinglePage(self, username, ablum_id, page):
        initialUrl = GetProjectAlbumsDetailPageUrl(username=username, album_id=ablum_id, page=page)
        resp = self.RequestUrl(initialUrl)
        if 'total_count' not in resp:
            return 0, 0, None
        totalPage = resp['total_count']
        curPage = len(resp['data'])
        return totalPage, curPage, resp['data']

    def GetProjectsSinglePage(self, username, page):
        initialUrl = GetProjectAlbumsDetailPageUrl(username=username, page=page)
        resp = self.RequestUrl(initialUrl)
        if 'total_count' not in resp:
            return 0, 0, None
        totalPage = resp['total_count']
        curPage = len(resp['data'])
        return totalPage, curPage, resp['data']

#================================================================
class ArtStationLocalMetaFetcher(ArtStationBaseMetaFetcher):
    def __init__(self, proxies):
        self.proxies = proxies
    
    def RequestUrl(self, url):
        resp = requests.get(url, headers=__FK_USER_AGENT__, proxies=self.proxies)
        return resp.json()

#================================================================
class ArtStationBrowserMetaFetcher(ArtStationBaseMetaFetcher):
    server = FKServer

    def __init__(self):
        self.server.Start()
    
    def RequestUrl(self, url):
        text = self.server.requester.SendAndWait(url, timeout=10, maxRetry=3)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

#================================================================
class ArtStationTaskMaker:
    def __init__(self, userUrl, username, metaFetcher: ArtStationBaseMetaFetcher):
        self.userUrl = userUrl
        self.username = username
        self.metaFetcher = metaFetcher
        self.userId = None
    
    @staticmethod
    def GetRepeatedUID(userIds):
        counter = Counter(userIds)
        topUID = counter.most_common(1)
        return topUID[0][0]

    def GetUserId(self, userUrl):
        resp = self.metaFetcher.RequestUrl(userUrl)
        userIds = re.findall(r"user_id.*?(\d+)", resp)
        return self.GetRepeatedUID(userIds)

    def GetImageItemFromDetail(self, artworkSummary):
        summaryUrl = ParseArtworkUrl(artworkSummary)
        resp = self.metaFetcher.GetArtworkSummary(summaryUrl)
        return ParseSingleArtwork(resp)

    def YieldImageItems(self, data, albumName=None):
        for summary in data:
            for imageItem in self.GetImageItemFromDetail(summary):
                if albumName is not None:
                    imageItem = FKImageItem(url=imageItem.url, name=imageItem.name, meta={"album_name": albumName})
                yield imageItem
    
    def GenTasksFromRoot(self):
        page = 1
        totalPage, curPage, data = self.metaFetcher.GetProjectsSinglePage(self.username, page)
        yield from self.YieldImageItems(data)
        while HasNextPage(curPage, totalPage):
            page += 1
            _, countDelta, data = self.metaFetcher.GetProjectsSinglePage(self.username, page)
            curPage += countDelta
            yield from self.YieldImageItems(data)
            time.sleep(0.2)
        
    def GenTasksFromAlbums(self):
        for index, album in enumerate(self.metaFetcher.GetAlbumsIndexPage(userId=self.userId)):
            page = 0
            curPage = 0
            totalPage = 1
            while HasNextPage(curPage, totalPage):
                page += 1
                _, countDelta, data = self.metaFetcher.GetAlbumProjectsSinglePage(self.username, album.id, page)
                curPage += countDelta
                yield from self.YieldImageItems(data, albumName=album.name)
                time.sleep(0.2)
    
    def GenTasks(self):
        yield from self.GenTasksFromRoot()
        yield from self.GenTasksFromAlbums()

    def __call__(self, *args, **kwargs):
        self.userId = self.GetUserId(userUrl=self.userUrl)
        yield from self.GenTasks()

#================================================================
class FKArtStationFetcher(FKBaseFetcher):
    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKArtStationFetcher, self).Save(content, taskItem)
        image = taskItem.image
        if image.meta is not None:
            escapedName = NormalizeName(image.meta['album_name'])
            savePath = os.path.join(taskItem.baseSavePath, escapedName)
            os.makedirs(savePath, exist_ok=True)
        else:
            savePath = taskItem.baseSavePath
        savePath = NormalizePath(savePath)
        if callable(image.name):
            imageName = image.name(image.url, content)
        else:
            iamgeName = image.name
        savePath = os.path.join(savePath, imageName)
        with open(savePath, "wb") as f:
            f.write(content)

#================================================================
class FKArtStationSite(FKBaseSite):
    def __init__(self, userUrl : str, proxy=None):
        self.tasks = None
        self.url = userUrl
        assert(userUrl.startswith(BASE_URL))
        self.username = userUrl.replace(BASE_URL, '')
        self.proxies = FromatProxy(proxy)
        self.fetcher = FKArtStationFetcher(**self.proxies)
        self.taskMaker = ArtStationTaskMaker(userUrl=userUrl, username=self.username, metaFetcher=ArtStationBrowserMetaFetcher())

    @property
    def DirName(self):
        return self.username
    
    @property
    def Fetcher(self):
        return self.fetcher

    @property
    def Tasks(self):
        yield from self.taskMaker()   