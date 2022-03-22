import os

from Core.FKDownloader import FKDownloader
from Site.FKArtStation import FKArtStationSite
from Site.FKBaseSite import FKBaseSite
from Site.FKHuaban import FKHuabanSite, FKHuabanBoard

def UserHomeRun(site, pathPrefix=None):
    path = site.DirName
    if pathPrefix is not None:
        path = os.path.join(pathPrefix, path)
    downloader = FKDownloader(saveDir=path, fetcher=site.Fetcher)
    downloader.AddTask(site.Tasks, background=True)
    downloader.Join(background=True)
    return downloader

def ArtStationRun(url, pathPrefix=None, proxy=None):
    site = FKArtStationSite(userUrl=url, proxy=proxy)
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