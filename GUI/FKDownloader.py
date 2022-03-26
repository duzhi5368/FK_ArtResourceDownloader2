import os
import time
import tkinter as tk
from Core.FKDownloader import FKDownloader
from gppt import GetPixivToken
from Utils.FKUtilsFunc import RunAsDaemonThread
from GUI.FKEntry import ArtStationRun, HuabanRun, HuabanBoardRun, PinterestRun, \
    PixivRun, Comic18Run, EHantaiRun, EHantaiByTagRun
from GUI.FKUITookits import (
    FKUI_NamedInput,
    FKUI_FileBrowser,
    FKUI_StatusBar,
    FKUI_ProgressBar,
    FKUI_PasswordInput,
    OpenSysExplorer,
    FKMessageInfo,
)

#================================================================
def CreateFKNormalInputs(master=None, storeName=None, userHomeName=None):
    url = FKUI_NamedInput(master=master, name=userHomeName or "用户主页地址")
    savePath = FKUI_FileBrowser(master=master, store_name=storeName)
    return url, savePath

def CreateFKPixivInputs(master=None):
    url = FKUI_NamedInput(master, name="用户主页地址")
    # （参见：https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362）
    refreshToken = FKUI_NamedInput(master, name="RefreshToken")
    pivixUsername = FKUI_NamedInput(master, name="Pixiv账号")
    pivixPassword = FKUI_PasswordInput(master, name="Pixiv密码")
    savePath = FKUI_FileBrowser(master, store_name="pixiv_save_path")
    return url, refreshToken, pivixUsername, pivixPassword, savePath

#================================================================
class FKUI_UserHomeDownloader(tk.Frame):
    title = "未命名下载器"
    def __init__(self, *args, storeName=None, userHomeName=None, **kwargs):
        super(FKUI_UserHomeDownloader, self).__init__(*args, **kwargs)
        self.downloader : FKDownloader = None
        self.url, self.savePath = CreateFKNormalInputs(self, storeName=storeName, userHomeName=userHomeName)
        for attrName, value in self.UserInputs().items():
            setattr(self, attrName, value)
        self.btnGroup = self.BuildButtons()
        self.progress = FKUI_ProgressBar(self)
        self.status = FKUI_StatusBar(self)
        self.StartUpdate()
    
    def SetUrlPlaceholder(self, text):
        self.url.SetInputPlaceholder(text)
    
    def UserInputs(self):
        return {}
    
    def Run(self, url, pathPrefix):
        return NotImplementedError()
    
    def BuildButtons(self):
        btnArgs = dict(height = 1)
        btnGroup = tk.Frame(self)
        buttons = [
            tk.Button(btnGroup, text=text, command=command, **btnArgs)
            for text, command in (
                ("开始下载", self.StartDownload),
                ("停止下载", self.StopDownload),
                ("打开下载文件夹", self.OpenDownloadFolder)
            )
        ]
        for index, btn in enumerate(buttons):
            btn.grid(column=index, row=0, sticky=tk.N)
        btnGroup.pack(fill=tk.BOTH, expand=1)
        return btnGroup
    
    def OpenDownloadFolder(self):
        path = self.savePath.GetPath()
        OpenSysExplorer(path)
    
    def StartDownload(self):
        self.url.AssertNoError()
        self.savePath.AssertNoError()
        url = self.url.GetInput()
        pathPrefix = self.savePath.GetPath()
        if not os.access(pathPrefix, os.W_OK):
            return FKMessageInfo("下载文件夹没有读写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.isDone:
                return FKMessageInfo("请先停止当前下载后，再重新点击下载")
        self.downloader = self.Run(url=url, pathPrefix=pathPrefix)
    
    def StopDownload(self):
        if self.downloader is not None:
            self.downloader.Stop()
            self.downloader = None

    def StartUpdate(self):
        RunAsDaemonThread(self.UpdateLoop)

    def UpdateLoop(self):
        while True:
            time.sleep(0.1)
            try:
                self.UpdateProgress()
            except AttributeError:
                pass
    
    def UpdateProgress(self):
        if self.downloader is None:
            self.progress.UpdateProgress(0, 100)
            self.status.Set("")
        else:
            self.progress.UpdateProgress(self.downloader.counter.done, self.downloader.counter.total)
            msg = self.downloader.counter.ToString()
            if self.downloader.isDone:
                msg = msg + " 已全部下载完成，可开始新的下载任务了"
            self.status.Set(msg)

#================================================================
class FKUI_ArtStationDownloader(FKUI_UserHomeDownloader):
    title = "ArtStation 按作者"

    def __init__(self, *args, **kwargs):
        super(FKUI_ArtStationDownloader, self).__init__(*args, storeName="artstation_save_path", **kwargs)
        self.SetUrlPlaceholder("https://www.artstation.com/frankie_wong")

    def StartDownload(self):
        self.url.AssertNoError()
        self.savePath.AssertNoError()

        url = self.url.GetInput()
        pathPrefix = self.savePath.GetPath()

        if not os.access(pathPrefix, os.W_OK):
            return FKMessageInfo("下载文件夹没有读写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.isDone:
                return FKMessageInfo("请先停止当前下载后，再重新点击下载")
        self.downloader = self.Run(url=url, pathPrefix=pathPrefix)

    def Run(self, url, pathPrefix):
        return ArtStationRun(url=url, pathPrefix=pathPrefix)

#================================================================
class FKUI_HuabanDownloader(FKUI_UserHomeDownloader):
    title = "花瓣 按作者"
    def __init__(self, *args, **kwargs):
        super(FKUI_HuabanDownloader, self).__init__(*args, storeName="huaban_save_path", **kwargs)
        self.SetUrlPlaceholder("https://huaban.com/user/olqxc2ncpu")

    def Run(self, url, pathPrefix):
        downloader, site = HuabanRun(url=url, pathPrefix=pathPrefix, returnSite=True)
        return downloader

#================================================================
class FKUI_HuabanBoardDownloader(FKUI_UserHomeDownloader):
    title = "花瓣 按画板"
    def __init__(self, *args, **kwargs):
        super(FKUI_HuabanBoardDownloader, self).__init__(
            *args, storeName="huaban_board_save_path", userHomeName="画板地址", **kwargs
        )
        self.SetUrlPlaceholder("https://huaban.com/boards/24598373")

    def Run(self, url, pathPrefix):
        return HuabanBoardRun(url=url, pathPrefix=pathPrefix)

#================================================================
class FKUI_PixivDownloader(tk.Frame):
    # todo: 这里之后可以和 normalDownloader 做整合
    title = "Pixiv 按作者"

    def __init__(self, *args, **kwargs):
        super(FKUI_PixivDownloader, self).__init__(*args, **kwargs)
        self.downloader = None
        self.url, self.refreshToken, self.userName, self.password, self.savePath = CreateFKPixivInputs(self)
        self.btnGroup = self.BuildButtons()
        self.progress = FKUI_ProgressBar(self)
        self.status = FKUI_StatusBar(self)
        self.url.SetInputPlaceholder("https://www.pixiv.net/users/74700573")
        self.refreshToken.SetInputPlaceholder("请网上查询如何获取 或 填写下方pixiv帐号密码后点击【获取refresh_token】按钮")
        self.userName.SetInputPlaceholder("如自行填写 refresh_token，则无需填写账号密码")
        self.StartUpdate()

    def BuildButtons(self):
        btnArgs = dict(height = 1)
        btnGroup = tk.Frame(self)
        buttons = [
            tk.Button(btnGroup, text=text, command=command, **btnArgs)
            for text, command in (
                ("开始下载", self.StartDownload),
                ("停止下载", self.StopDownload),
                ("打开下载文件夹", self.OpenDownloadFolder),
                ("获取refresh_token", self.AutoGetFreshToken)
            )
        ]
        for index, btn in enumerate(buttons):
            btn.grid(column=index, row=0, sticky=tk.N)
        btnGroup.pack(fill=tk.BOTH, expand=1)
        return btnGroup
    
    def OpenDownloadFolder(self):
        path = self.savePath.GetPath()
        OpenSysExplorer(path)
    
    def StartDownload(self):
        self.url.AssertNoError()
        self.savePath.AssertNoError()
        self.refreshToken.AssertNoError()

        url = self.url.GetInput()
        refreshToken = self.refreshToken.GetInput()
        pathPrefix = self.savePath.GetPath()

        if not os.access(pathPrefix, os.W_OK):
            return FKMessageInfo("下载文件夹没有读写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.isDone:
                return FKMessageInfo("请先停止当前下载后，再重新点击下载")
        self.downloader = PixivRun(url=url, refreshToken=refreshToken, pathPrefix=pathPrefix)
    
    def StopDownload(self):
        if self.downloader is not None:
            self.downloader.Stop()
            self.downloader = None
    
    def AutoGetFreshToken(self):
        # 依赖库和说明 https://github.com/eggplants/get-pixivpy-token
        # 资源下载 https://chromedriver.chromium.org/downloads
        chromeFilePath = os.getcwd() + "/chromedriver.exe" 
        if not os.path.exists(chromeFilePath):
            FKMessageInfo("请去 https://chromedriver.chromium.org/downloads 下载本机chrome对应版本的chromeDriver，解压后放置到本目录内。")
        else:
            username = self.userName.GetInput()
            password = self.password.GetInput()
            resp = GetPixivToken().login(headless=True, user=username, pass_=password)
            self.refreshToken.SetInputPlaceholder(resp['refresh_token'])

    def StartUpdate(self):
        RunAsDaemonThread(self.UpdateLoop)

    def UpdateLoop(self):
        while True:
            time.sleep(0.1)
            try:
                self.UpdateProgress()
            except AttributeError:
                pass
    
    def UpdateProgress(self):
        if self.downloader is None:
            self.progress.UpdateProgress(0, 100)
            self.status.Set("")
        else:
            self.progress.UpdateProgress(self.downloader.counter.done, self.downloader.counter.total)
            msg = self.downloader.counter.ToString()
            if self.downloader.isDone:
                msg = msg + " 已全部下载完成，可开始新的下载任务了"
            self.status.Set(msg)
#================================================================
class FKUI_PinterestDownloader(FKUI_UserHomeDownloader):
    title = "Pinterest 按作者"
    def __init__(self, *args, **kwargs):
        super(FKUI_PinterestDownloader, self).__init__(*args, storeName="pinterest_save_path", **kwargs)
        self.SetUrlPlaceholder("https://www.pinterest.ph/duzhi5368/_saved/")

    def Run(self, url, pathPrefix):
        downloader = PinterestRun(url=url, pathPrefix=pathPrefix)
        return downloader

#================================================================
class FKUI_18ComicDownloader(FKUI_UserHomeDownloader):
    title = "18Comic 按作品或关键字"
    def __init__(self, *args, **kwargs):
        super(FKUI_18ComicDownloader, self).__init__(*args, storeName="18comic_save_path", userHomeName="漫画网址或中文关键字", **kwargs)
        self.SetUrlPlaceholder("https://18comic.org/album/235900/%E9%9B%99%E8%83%9E%E8%83%8E%E7%9A%84%E9%A3%9F%E8%AD%9C-%E6%B7%98%E6%B0%A3%E5%A7%8A%E5%A6%B9%E7%9A%84%E7%A7%98%E5%AF%86%E8%AA%BF%E5%91%B3%E6%96%99-%E7%A6%81%E6%BC%AB%E6%BC%A2%E5%8C%96%E7%B5%84-%E5%8F%8C%E5%AD%90%E3%81%AE%E3%83%AC%E3%82%B7%E3%83%94-%E3%82%A4%E3%82%B1%E3%81%AA%E3%81%84%E5%A7%89%E5%A6%B9%E3%81%AE%E9%9A%A0%E3%81%97%E5%91%B3-%E4%B8%80%E7%B7%92%E3%81%AB%E6%9A%AE%E3%82%89%E3%81%99%E3%81%A3%E3%81%A6")

    def Run(self, url, pathPrefix):
        downloader = Comic18Run(url=url, pathPrefix=pathPrefix)
        return downloader
#================================================================
class FKUI_EHantaiDownloader(FKUI_UserHomeDownloader):
    title = "Ehentai 按作品"
    def __init__(self, *args, **kwargs):
        super(FKUI_EHantaiDownloader, self).__init__(*args, storeName="ehantai_save_path", userHomeName="漫画网址", **kwargs)
        self.SetUrlPlaceholder("https://e-hentai.org/g/2175062/d9a7883ead/")

    def Run(self, url, pathPrefix):
        downloader = EHantaiRun(url=url, pathPrefix=pathPrefix)
        return downloader
#================================================================
class FKUI_EHantaiTagDownloader(FKUI_UserHomeDownloader):
    title = "Ehentai 按标签搜索"
    def __init__(self, *args, **kwargs):
        super(FKUI_EHantaiTagDownloader, self).__init__(*args, storeName="ehantaittag_save_path", userHomeName="搜索关键字", **kwargs)
        self.SetUrlPlaceholder("chinese")

    def Run(self, url, pathPrefix):
        downloader = EHantaiByTagRun(url=url, pathPrefix=pathPrefix)
        return downloader
#================================================================
FKDownloaders = [
    FKUI_ArtStationDownloader,
    FKUI_HuabanDownloader,
    FKUI_HuabanBoardDownloader,
    FKUI_PixivDownloader,
    FKUI_PinterestDownloader,
    FKUI_18ComicDownloader,
    FKUI_EHantaiDownloader,
    FKUI_EHantaiTagDownloader,
    # todo
]

__all__ = (
    "FKUI_ArtStationDownloader",
    "CreateFKNormalInputs"
)