import os

from Core.FKDownloader import FKDownloader
from Site.FK18Comic import FK18ComicSite
from Site.FKArtStation import FKArtStationSite
from Site.FKBaseSite import FKBaseSite
from Site.FKEHantai import FKEHantaiTag, FKEhantaiSite
from Site.FKHuaban import FKHuabanSite, FKHuabanBoard
from Site.FKPinterest import FKPinterestSite
from Site.FKPixiv import FKPixivSite

def UserHomeRun(site:FKBaseSite, pathPrefix=None):
    path = site.DirName
    if pathPrefix is not None:
        path = os.path.join(pathPrefix, path)
    downloader = FKDownloader(saveDir=path, fetcher=site.Fetcher)
    downloader.AddTask(site.Tasks, background=True)
    downloader.Join(background=True)
    return downloader

def ArtStationRun(url, pathPrefix=None):
    site = FKArtStationSite(userUrl=url)
    return UserHomeRun(site, pathPrefix=pathPrefix)

def HuabanRun(url, pathPrefix=None, returnSite=True):
    site = FKHuabanSite(url)
    if returnSite:
        return UserHomeRun(site=site, pathPrefix=pathPrefix), site
    else:
        return UserHomeRun(site=site, pathPrefix=pathPrefix)

def HuabanBoardRun(url, pathPrefix=None):
    site = FKHuabanBoard(url)
    return UserHomeRun(site=site, pathPrefix=pathPrefix)

def PixivRun(url, refreshToken, pathPrefix=None):
    site = FKPixivSite(url=url, refreshToken=refreshToken)
    return UserHomeRun(site, pathPrefix)

def PinterestRun(url, pathPrefix=None):
    site = FKPinterestSite(url)
    return UserHomeRun(site, pathPrefix)

def Comic18Run(url, pathPrefix=None):
    site = FK18ComicSite(url)
    return UserHomeRun(site, pathPrefix)

def EHantaiRun(url, pathPrefix=None):
    site = FKEhantaiSite(url)
    return UserHomeRun(site, pathPrefix)

def EHantaiByTagRun(url, pathPrefix=None):
    site = FKEHantaiTag(url)
    return UserHomeRun(site, pathPrefix)