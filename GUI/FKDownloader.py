import os
import time
import tkinter as tk
from Core.FKDownloader import FKDownloader
from Utils.FKUtilsFunc import RunAsDaemonThread
from GUI.FKEntry import ArtStationRun
from GUI.FKUITookits import (
    FKUI_NamedInput,
    FKUI_FileBrowser,
    FKUI_StatusBar,
    FKUI_ProgressBar,
    FKUI_PasswordInput,
    FKUI_ProxyInput,
    OpenSysExplorer,
    FKMessageInfo,
)

#================================================================
def CreateFKNormalInputs(master=None, storeName=None, userHomeName=None):
    url = FKUI_NamedInput(master=master, name=userHomeName or "用户主页地址")
    savePath = FKUI_FileBrowser(master=master, store_name=storeName)
    return url, savePath

#================================================================
class FKUI_UserHomeDownloader(tk.Frame):
    title = "未命名下载器"
    def __init__(self, *args, storeName=None, userHomeName=None, **kwargs):
        super(FKUI_UserHomeDownloader, self).__init__(*args, **kwargs)
        self.downloader = None
        self.url, self.savePath = CreateFKNormalInputs(self, storeName=storeName, userHomeName=userHomeName)
        for attrName, value in self.UserInputs().items():
            setattr(self, attrName, value)
        self.btnGroup = self.BuildButtons()
        self.progress = FKUI_ProgressBar(self)
        self.status = FKUI_StatusBar(self)
        self.StartUpdate()
    
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
            if self.downloader.done:
                msg = msg + " 已全部下载完成，可开始新的下载任务了"
            self.status.Set(msg)

#================================================================
class FKUI_ArtStationDownlaoder(FKUI_UserHomeDownloader):
    title = "ArtStation 按作者"
    def UserInputs(self):
        return {'proxy': FKUI_ProxyInput(master=self, name="代理地址(可支持http/https/socks5)，可不填")}
    
    def StartDownload(self):
        self.url.AssertNoError()
        self.savePath.AssertNoError()
        self.proxy.AssertNoError()

        url = self.url.GetInput()
        pathPrefix = self.savePath.GetPath()
        proxy = self.proxy.GetInput()

        if not os.access(pathPrefix, os.W_OK):
            return FKMessageInfo("下载文件夹没有读写权限，请重新选择")
        if self.downloader is not None:
            if not self.downloader.isDone:
                return FKMessageInfo("请先停止当前下载后，再重新点击下载")
        self.downloader = self.Run(url=url, pathPrefix=pathPrefix, proxy=proxy)

    def Run(self, url, pathPrefix, proxy):
        return ArtStationRun(url=url, pathPrefix=pathPrefix, proxy=proxy)

#================================================================
FKDownloaders = [
    FKUI_ArtStationDownlaoder,
    # todo
]

__all__ = (
    "FKUI_ArtStationDownlaoder",
    "CreateFKNormalInputs"
)