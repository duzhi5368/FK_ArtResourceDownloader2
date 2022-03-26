import os
import re
import time

from bs4 import BeautifulSoup
from GUI.FKUITookits import FKMessageInfo
from Site.FKBaseFetcher import FKBaseFetcher
from Site.FKBaseSite import FKBaseSite
from Core.FKTaskItem import FKImageItem, FKTaskItem
from Utils.FKUtilsFunc import NormalizePath, FKLogger, NormalizeFileName
#================================================================

XHR_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Upgrade-Insecure-Requests': '1'
}

BASE_URL = "https://e-hentai.org"
SEARCH_URL = BASE_URL + "/?f_search={}&page={}&advsearch=1&f_sname=on&f_stags=on&f_sr=on&f_srdd=4"
BOARD_URL = BASE_URL + "/g/"

#================================================================
class FKEhantaiFetcher(FKBaseFetcher):
    def __init__(self, **kwargs):
        super(FKEhantaiFetcher, self).__init__(**kwargs)
        self.session.headers.update()

    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKEhantaiFetcher, self).Save(content, taskItem)
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
class FKEHantaiTag(FKBaseSite):
    def __init__(self, tags):
        self.fetcher = FKEhantaiFetcher()
        self.tagList = tags #urllib.parse.quote(tags) 暂时没必要做高级解析
        self.urls = self.GetUrlsByTags()
        # FKLogger.info("{}".format(self.urls))

    @property
    def DirName(self):
        return self.tagList
    
    @property
    def Fetcher(self):
        return self.fetcher
    
    @property
    def Tasks(self):
        yield from self.FetchBenzis()

    def FetchBenzis(self):
        for url in self.urls:
            yield from self.FetchBenzi(url, 0)

    def FetchBenzi(self, url, page):
        totalPics = 0
        try:
            if page == 0:
                reallyUrl = url
            else:
                reallyUrl = url + "?p=" + str(page)
            resp = self.fetcher.Get(reallyUrl)
            soup = BeautifulSoup(resp.text, 'lxml')
            divs = soup.find_all(class_='gdtm')
            totalPics = int(soup.find('div', id='gdd').find_all(class_="gdt2")[5].string.split(' ')[0])
            index = 0
            for div in divs:
                index = index + 1
                picUrl = div.a.get('href')
                picUrlSrc = self.FetchPicUrl(picUrl)
                ext = picUrlSrc.split(".")[-1]
                if picUrlSrc:
                    yield FKImageItem(url=picUrlSrc, name=str(index) + '.' + ext)
            
            totalPages = totalPics // 40
            if totalPages <= page:
                return
            else:
                yield from self.FetchBenzi(url, page+1)
        except:
            pass

    def FetchPicUrl(self, url):
        try:
            resp = self.fetcher.Get(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            images = soup.find_all(id="img")
            for image in images:
                picSrc = image['src']
                return picSrc
        except:
            pass

    def GetUrlsByTags(self):
        pageLineCount = 25
        downloadCount = 10
        urls = []
        try:
            intPages = downloadCount // pageLineCount
            lineMod = downloadCount % pageLineCount
            for intPage in range(0, intPages + 1):
                requestUrl = SEARCH_URL.format(self.tagList, intPage)
                # FKLogger.info(requestUrl)
                resp = self.fetcher.Get(requestUrl)
                soup = BeautifulSoup(resp.text, 'lxml')
                tds = soup.find_all(class_='glname')
                for index, td in enumerate(tds):
                    urls.append(td.a['href'])
                    if (25 > downloadCount - 1 == index) or (downloadCount > 25 and intPage == intPage and index == lineMod - 1):
                        break
        except:
            FKMessageInfo("查找失败,请检查tag格式")
        return urls
#================================================================
class FKEhantaiSite(FKBaseSite):
    def __init__(self, url):
        self.fetcher = FKEhantaiFetcher()
        self.url = url
        self.dirName = self.GetDirPath()
    
    @property
    def DirName(self):
        return self.dirName
    
    @property
    def Fetcher(self):
        return self.fetcher
    
    @property
    def Tasks(self):
        yield from self.FetchBenzi(self.url, 0)

    def GetDirPath(self):
        if self.url.find(BOARD_URL) == -1:
            FKMessageInfo("路径不合法，请重新输入。")
            return time.time()
        try:
            resp = self.fetcher.Get(self.url)
            soup = BeautifulSoup(resp.text, 'lxml')
            title = str(soup.h1.get_text())
            totalPages = int(soup.find('div', id='gdd').find_all(class_="gdt2")[5].string.split(' ')[0])
            dirPath = re.sub(r"[\/\\\:\*\?\"\<\>\|]", "-", title)
            dirPath = dirPath + '_' + str(totalPages) + '页'
            dirPath = NormalizeFileName(dirPath)
            FKLogger.info("保存路径为 %s" % dirPath)
        except:
            FKMessageInfo("网址解析错误，请确认该网址正确，或反馈给开发人员协助解决。")
            return time.time()
        return dirPath

    def FetchBenzi(self, url, page):
        totalPics = 0
        try:
            if page == 0:
                reallyUrl = url
            else:
                reallyUrl = url + "?p=" + str(page)
            resp = self.fetcher.Get(reallyUrl)
            soup = BeautifulSoup(resp.text, 'lxml')
            divs = soup.find_all(class_='gdtm')
            totalPics = int(soup.find('div', id='gdd').find_all(class_="gdt2")[5].string.split(' ')[0])
            index = 0
            for div in divs:
                index = index + 1
                picUrl = div.a.get('href')
                picUrlSrc = self.FetchPicUrl(picUrl)
                ext = picUrlSrc.split(".")[-1]
                if picUrlSrc:
                    yield FKImageItem(url=picUrlSrc, name=str(index) + '.' + ext)
            
            totalPages = totalPics // 40
            if totalPages <= page:
                return
            else:
                yield from self.FetchBenzi(url, page+1)
        except:
            pass

    def FetchPicUrl(self, url):
        try:
            resp = self.fetcher.Get(url)
            soup = BeautifulSoup(resp.text, 'lxml')
            images = soup.find_all(id="img")
            for image in images:
                picSrc = image['src']
                return picSrc
        except:
            pass
