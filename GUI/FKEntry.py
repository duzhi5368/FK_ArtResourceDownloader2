import os

from Core.FKDownloader import FKDownloader
from Site.FKArtStation import ArtStation
from Site.FKBaseSite import FKBaseSite

def UserHomeRun(site, pathPrefix=None):
    path = site.DirName
    if pathPrefix is not None:
        path = os.path.join(pathPrefix, path)
    downloader = FKDownloader(saveDir=path, fetcher=site.Fetcher)
    downloader.AddTask(site.Tasks, background=True)
    downloader.Join(background=True)
    return downloader

def ArtStationRun(url, pathPrefix=None, proxy=None):
    site = ArtStation(userUrl=url, proxy=proxy)
    return UserHomeRun(site, pathPrefix=pathPrefix)