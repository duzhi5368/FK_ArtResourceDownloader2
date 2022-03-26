import os
import re
import time
from lxml import etree

from typing import NamedTuple
from GUI.FKUITookits import FKMessageInfo
from Site.FKBaseFetcher import FKBaseFetcher
from Site.FKBaseSite import FKBaseSite
from Core.FKTaskItem import FKImageItem, FKTaskItem
from Utils.FKUtilsFunc import NormalizePath, FKLogger
#================================================================

XHR_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43"
}

BASE_URL = "https://18comic.org"
SEARCH_URL = BASE_URL + "/search/photos?search_query={}"

#================================================================
class FK18ComicFetcher(FKBaseFetcher):
    def __init__(self, **kwargs):
        super(FK18ComicFetcher, self).__init__(**kwargs)
        self.session.headers.update(XHR_HEADERS)

    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FK18ComicFetcher, self).Save(content, taskItem)
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
class FK18ComicSite(FKBaseSite):
    def __init__(self, keywordOrUrl):
        self.fetcher = FK18ComicFetcher()
        self.keywordOrUrl = keywordOrUrl
        self.links, self.dirname = self.GetBenziUrlList(self.keywordOrUrl)

    @property
    def DirName(self):
        return self.dirname
    
    @property
    def Fetcher(self):
        return self.fetcher
    
    @property
    def Tasks(self):
        yield from self.FetchEpisodeList()

    def GetBenziNameList(self, links):
        nameList = []
        for link in links:
            nameList.append(link.split('/')[-1])
        return nameList
        
    def FetchEpisodeList(self):
        for link in self.links: # 逐项目
            name = link.split('/')[-1]
            resp = self.fetcher.Get(url=link)
            FKLogger.info("%s" % link)
            episodeUrl = []
            try:
                episodeList = re.findall('<a href="(.*?)">\n<li class=".*">', resp.text)
                if len(episodeList) <= 0:
                    episodeList = re.findall('col btn btn-primary dropdown-toggle reading" href="(.*?)"')
                    episodeUrl = BASE_URL + episodeList[0]
                    #FKLogger.info("%s" % episodeUrl)
                else:
                    for i in range(len(episodeList) // 2): # 逐本
                        episodeUrl.append(BASE_URL + episodeList[i])
                    #FKLogger.info("%s" % episodeUrl)

                totalEpisode = len(episodeList)
                FKLogger.info("%s 需要下载 %d 个章节" % (name, totalEpisode))
                for j in range(0,totalEpisode): # 逐章节
                    yield from self.GetOneEpisode(episodeUrl[j], str(j), name)
            except:
                continue

    def GetOneEpisode(self, episodeUrl, episodeNum, path):
        # FKLogger.info("%s, %s, %s" % (episodeUrl, episodeNum, path))
        strNum = str(int(episodeNum) + 1)
        try:
            resp = self.fetcher.Get(episodeUrl)
            #temp = re.search('scramble_id = (.*?);\n.*?\n.*?var aid = (.*?);', resp.text)
            #scrambleId = temp.group(1)
            #aid = temp.group(2)
            temp = re.findall('data-original="(.*?)" id="album_photo_(.+?)"', resp.text)
            imageUrl = []
            for i in range(len(temp)):
                imageUrl = temp[i][0]
                imageSavePath = path + "/" + strNum + "/"
                imageName = temp[i][1]
                yield FKImageItem(url=imageUrl, name=imageName, meta={'dir_name': imageSavePath})
        except:
            pass

    def GetBenziUrlList(self, keywordOrUrl):
        if re.match(r'^https?:/{2}\w.+$', keywordOrUrl):
            links = []
            links.append(keywordOrUrl)
            name = keywordOrUrl.split("/")[-1]
            return links, name
        else:
            resp = self.fetcher.Get(SEARCH_URL.format(keywordOrUrl))
            MAX_BENZI_NUM = 5
            try:
                linkList = re.findall('list-col.*?\n.*?\n<a href="(.*?)">', resp.text)
                if len(linkList) <= 0:
                    FKMessageInfo("关键字 {} 未搜寻到结果，请尝试更换关键字。" % keywordOrUrl)
                    return
                links = []
                for i in range(len(linkList)):
                    if i < MAX_BENZI_NUM:
                        links.append(BASE_URL + linkList[i])
                    else:
                        break
                # 封面图片
                #coverImageUrls = []
                #htmlTree = etree.HTML(resp.text)
                #coverImageUrls = htmlTree.xpath('//div[@class="row m-0"]//img/@data-original')
                #coverImageUrls = coverImageUrls[0:maxCoverNum]

                #for i in range(len(coverImageUrls)):
                #    imageName = "{}.jpg".format(i)
                #    meta['dir_name'] = fileAddress
                #    yield FKImageItem(url=coverImageUrls[i], name=imageName, meta=meta)
            except:
                FKMessageInfo("解析网站数据失败，请尝试更换关键字再次尝试或联系开发者反馈。")
                raise
            return links, keywordOrUrl

