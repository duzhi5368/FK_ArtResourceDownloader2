import os
import re

from flask import request
from pixivpy3 import AppPixivAPI, PixivError
from GUI.FKUITookits import FKMessageInfo

from Utils.FKUtilsFunc import GetFileExtension, NormalizeFileName, NormalizePath
from Core.FKTaskItem import FKImageItem, FKTaskItem
from Site.FKBaseFetcher import FKBaseFetcher
from Site.FKBaseSite import FKBaseSite
#================================================================

XHR_HEADERS = {
    "Referer": "http://www.pixiv.net/"
}

#================================================================
def ParseImageUrls(illustration):
    if 'original_image_url' in illustration['meta_single_page']:
        url = illustration['meta_single_page']['original_image_url']
        if illustration['type'] == 'ugoira':
            url = url.replace("img-original", 'img-zip-ugoira')
            url = re.findall('(.*)_ugoira0\..*', url)[0]
            url = "%s%s" % (url, '_ugoira1920x1080.zip')

        fileName = '%s.%s' % (illustration['id'], GetFileExtension(url))
        yield FKImageItem(name=fileName, url=url)
    else:
        dirName = NormalizeFileName(illustration['title'])
        images = illustration['meta_pages']
        for index, image in enumerate(images):
            url = image['image_urls']['original']
            name = "%s.%s" % (index, GetFileExtension(url))
            yield FKImageItem(name=name, url=url, meta={'is_comic':True, 'dir_name':dirName})

#================================================================
class FKPixivFetcher(FKBaseFetcher):
    def __init__(self, **kwargs):
        super(FKPixivFetcher, self).__init__(**kwargs)
        self.session.headers.update(XHR_HEADERS)

    def Save(self, content, taskItem : FKTaskItem):
        if taskItem.image.meta is None:
            return super(FKPixivFetcher, self).Save(content, taskItem)
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
class FKPixivSite(FKBaseSite):
    def __init__(self, url:str, refreshToken):
        requestsKwargs = {'timeout': (3, 10)}
        self.api = AppPixivAPI(**requestsKwargs)
        self.fetcher = FKPixivFetcher()
        try:
            self.api.auth(refresh_token=refreshToken)
        except PixivError as e:
            FKMessageInfo(e.reason)
            pass
        self.userId = int(url.split("/")[-1])
        self.dirName = None
        self.totalIllustrations = 0
        self.FetchUserDetail()

    @property
    def Fetcher(self):
        return self.fetcher
    
    @property
    def DirName(self):
        assert self.dirName is not None
        return self.dirName
    
    @property
    def Tasks(self):
        yield from self.FetchImageList()
    
    def FetchUserDetail(self):
        assert self.userId is not None
        profile = self.api.user_detail(self.userId)
        user = profile['user']
        dirName = "-".join([user['name'], user['account'], str(user['id'])])
        self.dirName = NormalizeFileName(dirName)
        self.totalIllustrations = profile['profile']['total_illusts']
        return self.dirName
    
    def FetchImageList(self):
        ret = self.api.user_illusts(self.userId)
        while True:
            for illustration in ret.illusts:
                yield from ParseImageUrls(illustration)
            if ret.next_url is None:
                break
            ret = self.api.user_illusts(**self.api.parse_qs(ret.next_url))
    
    def FetchSingleImageUrl(self, illustrationId):
        jsonRet = self.api.illust_detail(illustrationId)
        illustrationInfo = jsonRet.illust
        return illustrationInfo.image_urls['large']

    
