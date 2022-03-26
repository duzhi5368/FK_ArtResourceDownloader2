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
        yield from self.FetchBenzi()

    def GetDirPath(self):
        if self.url.find('https://e-hentai.org/g/') == -1:
            FKMessageInfo("路径不合法，请重新输入。")
            return time.time()
        try:
            resp = self.fetcher.Get(self.url)
            soup = BeautifulSoup(resp.text, 'lxml')
            divs = soup.find_all(class_='gdtm')
            title = str(soup.h1.get_text())
            page = 0
            for _ in divs:
                page = page + 1
            dirPath = re.sub(r"[\/\\\:\*\?\"\<\>\|]", "-", title)
            dirPath = dirPath + '_' + str(page) + '页'
            dirPath = NormalizeFileName(dirPath)
            FKLogger.info("保存路径为 %s" % dirPath)
        except:
            FKMessageInfo("网址解析错误，请确认该网址正确，或反馈给开发人员协助解决。")
            return time.time()
        return dirPath

    def FetchBenzi(self):
        try:
            resp = self.fetcher.Get(self.url)
            soup = BeautifulSoup(resp.text, 'lxml')
            divs = soup.find_all(class_='gdtm')
            page = 0
            for div in divs:
                page = page + 1
                picUrl = div.a.get('href')
                picUrlSrc = self.FetchPicUrl(picUrl)
                ext = picUrlSrc.split(".")[-1]
                if picUrlSrc:
                    yield FKImageItem(url=picUrlSrc, name=str(page) + '.' + ext)
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
