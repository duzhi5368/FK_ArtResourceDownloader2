import os
import json
import requests
import time
import lxml.html as html

from pathlib import PurePath
from json import JSONDecodeError
from urllib.parse import urlparse, urlencode, unquote
from Core.FKTaskItem import FKImageItem, FKTaskItem
from GUI.FKUITookits import FKMessageInfo
from Site.FKBaseFetcher import FKBaseFetcher
from Site.FKBaseSite import FKBaseSite
from Utils.FKUtilsFunc import NormalizePath, Retry, FKLogger, ImageSortFunc, NormalizeFileName
#================================================================

# todo : 地址可能要按国家区分
BASE_URL = "https://www.pinterest.ph"
FETCH_BOARD_URL = BASE_URL + "/resource/BoardFeedResource/get/"
FETCH_BOARD_SECTION_URL = BASE_URL + "/resource/BoardSectionPinsResource/get/"
FETCH_BOARDS_URL = BASE_URL + "/resource/BoardsResource/get/"
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.0.0 Safari/537.36'
XHR_HEADERS_0 = {
    'User-Agent': UA,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive'
}
XHR_HEADERS_1 = {
    'User-Agent': UA,
    'Accept': 'application/json, text/javascript, */*, q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': BASE_URL,
    'X-Requested-With': 'XMLHttpRequest',
    'X-APP-VERSION': 'c643827',
    'X-Pinterest-AppState': 'active',
    'X-Pinterest-PWS-Handler': 'www/[username]/[slug]/[section_slug].js',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'Trailers'
}
XHR_HEADERS_2 = {
    'User-Agent': UA,
    'Accept': 'application/json, text/javascript, */*, q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': BASE_URL,
    'X-Requested-With': 'XMLHttpRequest',
    'X-APP-VERSION': '4c8c36f',
    'X-Pinterest-AppState': 'active',
    'X-Pinterest-PWS-Handler': 'www/[username]/[slug]/[section_slug].js',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'TE': 'Trailers'
}
XHR_HEADERS_3 = {
    'User-Agent': UA,
    'Accept': 'image/webp,*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': BASE_URL,
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'Trailers'
}
XHR_HEADERS_4 = {
    'User-Agent': UA,
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Origin': BASE_URL,
    'DNT': '1',
    'Referer': BASE_URL,
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}

#================================================================
class FKPinterestFetcher(FKBaseFetcher):
    def __init__(self):
        super(FKPinterestFetcher, self).__init__()
        self.session.headers.update(XHR_HEADERS_0)
    
    def UpdateHeader(self, xhrHeaders):
        self.session.headers.update(xhrHeaders)

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
    
    def TestGet(self, url, **kwargs):
        if 'timeout' in kwargs:
            kwargs.pop('timeout')
        resp = self.session.get(url, timeout=(2, 30), **kwargs)
        return resp

    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKPinterestFetcher, self).Save(content, taskItem)
        image = taskItem.image
        savePath = os.path.join(taskItem.baseSavePath, image.meta['folder'])
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
        self.userName = urlparse(url).path
        slashPathList = self.userName.split('/')
        self.userName = slashPathList[1]
        # paths = self.GetUserBoardPaths(self.userName)
        # self.boardsInfo = [self.GetBoardInfo(path) for path in paths]
        # self.FetchBoardsList()
        self.boardsInfo = self.GetBoardsByUser(self.userName)

    @property
    def Fetcher(self):
        return self.fetcher

    @property
    def DirName(self):
        return self.userName

    @property
    def Tasks(self):
        # yield from self.FetchBoardsList()
        yield from self.FetchUserImages()

    def GetBoardsByUser(self, userName):
        bookmark = None
        boards = []
        while bookmark != '-end-':
            options = {
                'isPrefetch': 'false',
                'privacy_filter': 'all',
                'sort': 'alphabetical', 
                'field_set_key': 'profile_grid_item',
                'username': userName,
                'page_size': 25,
                'group_by': 'visibility',
                'include_archived': 'true',
                'redux_normalize_feed': 'true',
            }
            if bookmark:
                options.update({'bookmarks': [bookmark]})
            
            postParmas = urlencode({
                'source_url': userName,
                'data': {
                    'options': options,
                    'context': {}
                },
                '_': int(time.time()*1000)
            }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

            try:
                self.fetcher.UpdateHeader(XHR_HEADERS_1)
                resp = self.fetcher.Get(FETCH_BOARDS_URL, params=postParmas)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                FKLogger.info("网络连接不稳定")
                break
            
            try:
                data = resp.json()
                boards.extend(data['resource_response']['data'])
                bookmark = data['resource']['options']['bookmarks'][0]
                # FKLogger.info("当前 bookmark 为 %s" % bookmark)
            except:
                FKMessageInfo("解析pinterest响应数据错误")
                break
            # FKLogger.info("当前正在处理第 %d 个board" % len(boards))
        return boards

    def FetchUserImages(self):
        boards = self.boardsInfo
        for _, board in enumerate(boards):
            if 'name' not in board:
                continue
            boardPath = board['url'].strip('/')
            isMainBoard = False
            boardSlug = boardPath
            if '/' in boardPath:
                boardSlug = boardPath.split('/')[1]
                isMainBoard = False
            else:
                boardSlug = boardPath
                isMainBoard = True
            yield from self.FetchBoardOrSectionImages(board, self.userName, boardSlug, None, isMainBoard)

            if board['section_count'] > 0:
                board, sections = self.GetBoardInfoByPath(boardPath, None, None)
                for section in sections:
                    sectionPath = boardPath + '/' + section['slug']
                    board = self.GetBoardInfoByPath(sectionPath, section['slug'], boardPath)
                    sectionUserName, sectionBoardName = boardPath.split('/')
                    yield from self.FetchBoardOrSectionImages(board, sectionUserName, sectionBoardName, section['slug'], False)
            
    def FetchBoardOrSectionImages(self, board, userName, boardSlug, sectionSlug, isMainBoard):
        bookmark = None
        images = []
        try:
            if 'owner' in board:
                boardId = board['id']
                boardName = board['name']
            elif 'board' in board:
                boardId = boardId['board']['id']
                boardName = board['board']['name']
                if sectionSlug:
                    try:
                        sectionId = board['section']['id']
                    except (KeyError, TypeError):
                        return
                    sectionTitle = board['section']['title']
            else:
                return
        except (KeyError, TypeError):
            return 

        if sectionSlug:
            saveDir = os.path.join(boardName, sectionTitle)
            url = '/' + '/'.join((self.userName, boardSlug, sectionSlug)) + '/'
        else:
            saveDir = boardName
            if isMainBoard:
                url = self.userName
            else:
                url = '/'.join((self.userName, boardSlug))
        
        latestPin = self.GetLatestPin(saveDir)

        isSortedAPI = True
        while bookmark != '-end-':
            if sectionSlug:
                options = {
                    'isPrefetch': 'false',
                    'field_set_key': 'react_grid_pin',
                    'is_own_profile_pins': 'false',
                    'page_size': 25,
                    'redux_normalize_feed': 'true',
                    'section_id': sectionId
                }
            else:
               options = {
                    'isPrefetch': 'false',
                    'board_id': boardId,
                    'board_url': url,
                    'field_set_key': 'react_grid_pin',
                    'filter_section_pins': 'true',
                    'layout':'default',
                    'page_size': 25,
                    'redux_normalize_feed': 'true'
                }

            if bookmark:
                options.update({'bookmarks': [bookmark]})
            
            postParmas = urlencode({
                'source_url': url,
                'data': {
                    'options': options,
                    'context': {}
                },
                '_': int(time.time()*1000)
            }).replace('+', '').replace('%27', '%22').replace('%3A%22true%22', '%3Atrue').replace('%3A%22false%22', '%3Afalse')

            try:
                if sectionSlug:
                    self.fetcher.UpdateHeader(XHR_HEADERS_2)
                    resp = self.fetcher.Get(FETCH_BOARD_SECTION_URL, params=postParmas)
                else:
                    self.fetcher.UpdateHeader(XHR_HEADERS_2)
                    resp = self.fetcher.Get(FETCH_BOARD_URL, params=postParmas)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                FKLogger.info("网络连接不稳定")
                break

            data = resp.json()
            imagesRound = data['resource_response']['data']

            isReachLastestPin = False
            if isSortedAPI and latestPin != '0':
                imagePrev = 0
                isOnHoldBreak = False
                for imagesRoundIndex, image in enumerate(imagesRound):
                    if 'images' in image:
                        if image['id'].isdigit():
                            imageCurr = image['id']
                            if imagePrev and (int(imageCurr) > int(imagePrev)):
                                isSortedAPI = False
                                isReachLastestPin = False
                                if isOnHoldBreak:
                                    imagesRound = data['resource_response']['data']
                                    break
                            if latestPin == imageCurr:
                                imagesRound = imagesRound[:imagesRoundIndex]
                                isReachLastestPin = True
                                isOnHoldBreak = True
                            imagePrev = imageCurr
                        else:
                            isSortedAPI = False
                            isReachLastestPin = False
                            imagesRound = data['resource_response']['data']
                    else:
                        pass
            
            images.extend(imagesRound)
            if isReachLastestPin:
                break
            
            bookmark = data['resource']['options']['bookmarks'][0]
        
        if isSortedAPI:
            images = images[::-1]

        # FKLogger.info("等待下载的图像有 %d 个" % len(images))
        for image in images:
            try:
                if 'id' not in image:
                    continue
                if 'images' not in image:
                    continue
                imageId = image['id']
                url = image['images']['orig']['url']
                basename = os.path.basename(url)
                ext = basename.split('.')[-1]
                filePath = imageId+ '.' + ext
                yield FKImageItem(url=url, name=filePath, meta={'folder': saveDir})
            except:
                continue

    def GetLatestPin(self, saveDir):
        latestPin = '0'
        depth = 1
        walkDir = os.path.abspath(saveDir)
        for root, dirs, files in os.walk(walkDir):
            if root[len(walkDir):].count(os.sep) < depth:
                imagesList = [_ for _ in files if _.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.mp4', '.mkv', '.webp', '.svg', '.m4a', '.mp3', '.flac', '.m3u8', '.wmv', '.webm', '.mov', '.flv', '.m4v', '.ogg', '.avi', '.wav', '.apng', '.avif' )) ]
                imagesListBySort = sorted(imagesList, key=ImageSortFunc)
                if not imagesListBySort:
                    break
                latestPin = imagesListBySort[-1].split('.')[0].split('_')[0]
        return latestPin
        
    def GetBoardInfoByPath(self, boardOrSectionPath, section, boardPath):
        boards = {}
        sections = []
        isSucessed = False

        try:
            self.fetcher.UpdateHeader(XHR_HEADERS_0)
            resp = self.fetcher.Get(BASE_URL+"/{}/".format(boardOrSectionPath))
            isSucessed = True
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            FKLogger.info("网络连接不稳定")

        if isSucessed:
            root = html.fromstring(resp.content)
            scripts = root.xpath('//script/text()')
            boardInfo = {}
            boardSectionInfo = {}
            for script in scripts:
                try:
                    data = json.loads(script)
                    if 'prop' in data:
                        boardInfo = data['props']['initialReduxState']['boards']
                        boardSectionInfo = data['props']['initialReduxState']['boardsections']
                        isSucessed = True
                        break
                except:
                    isSucessed = False

        if not isSucessed:
            if section:
                return boards
            else:
                return boards, sections

        boardInfoKeys = list(boardInfo.keys())
        if section:
            pathToCompare = boardPath
        else:
            pathToCompare = boardOrSectionPath
        for key in boardInfoKeys:
            if unquote(boardInfo[key].get('url', '').strip('/')) == unquote(pathToCompare):
                boardInfoInKey = boardInfo[key]
                boardInfoMap = {}
                boardInfoMap['url'] = boardInfoInKey.get('url', '')
                boardInfoMap['id'] = boardInfoInKey.get('id', '')
                boardInfoMap['name'] = boardInfoInKey.get('name', '')
                boardInfoMap['section_count'] = boardInfoInKey.get('section_count', '')
                boards['board'] = boardInfoMap
                break
        
        boardSectionInfoKeys = list(boardSectionInfo.keys())
        for key in boardSectionInfoKeys:
            boardSectionInfoInKey = boardSectionInfo[key]
            boardSectionInfoMap = {}
            sectionSlug = unquote(boardSectionInfoInKey.get('slug', ''))
            if section and (sectionSlug != section):
                continue
            boardSectionInfoMap['slug'] = sectionSlug
            boardSectionInfoMap['id'] = boardSectionInfoInKey.get('id', '')
            boardSectionInfoMap['title'] = boardSectionInfoInKey.get('title', '')

            if section:
                boards['section'] = boardSectionInfoMap
            else:
                sections.append(boardSectionInfoMap)
        
        if section:
            return boards
        else:
            return boards, sections


"""
    def GetUserBoardPaths(self, userName):
        allBoards = self.GetUserBoards(userName)
        return [board["url"][1:-1] for board in allBoards]
    
    def GetUserBoards(self, userName):
        response = self.fetcher.Get((BASE_URL + "/{}/").format(userName))
        root = html.fromstring(response.content)
        rootPath = root.xpath("//script/text()")
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

"""