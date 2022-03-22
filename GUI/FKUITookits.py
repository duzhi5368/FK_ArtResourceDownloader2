import platform
import os
import tkinter as tk
from tkinter import COMMAND, filedialog, messagebox as msgbox, ttk
from pathlib import Path
from GUI.FKConfig import FKConfig

#================================================================
def FKMessageInfo(msg, title="提示"):
    msgbox.showinfo(title=title, message=msg)

def OpenSysExplorer(path):
    plf = platform.system().lower()
    path = Path(path)
    if "darwin" in plf:
        return os.system('open %s' % path)
    elif "windows" in plf:
        return os.system('explorer.exe "%s"' % path)
    elif "linux" in plf:
        return os.system('xdg-open %s' % path)
    
    return FKMessageInfo("不支持当前平台")

def GetWorkingDir():
    return os.getcwd()

#================================================================
class FKUI_StatusBar(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.variable = tk.StringVar()
        self.label = tk.Label(self, bd=1, relief=tk.SUNKEN, anchor=tk.W, 
            textvariable=self.variable, font=('arial', 16, 'normal'))
        self.variable.set('')
        self.label.pack(fill=tk.X)
        self.pack(fill=tk.BOTH)

    def Set(self, value):
        self.variable.set(value)

#================================================================
class FKUI_NamedInput(tk.Frame):
    def __init__(self, master=None, name=None, **kwargs):
        super(FKUI_NamedInput, self).__init__(master=master, **kwargs)
        assert name is not None
        self.name = name
        label = tk.Label(self, text=name)
        label.pack(side=tk.LEFT)
        self.entry = tk.Entry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.pack(fill=tk.X)

    def GetInput(self):
        return self.entry.get()
    
    def AssertNoError(self):
        text = self.GetInput()
        if not text:
            FKMessageInfo("%s 不能为空" % self.name)
            return ValueError("错误，输入内容为空")

#================================================================
class FKUI_PasswordInput(tk.Frame):
    def __init__(self, master=None, name=None, **kwargs):
        super(FKUI_PasswordInput, self).__init__(master=master, **kwargs)
        assert name is not None
        self.name = name
        label = tk.Label(self, text=name)
        label.pack(side=tk.LEFT)
        self.entry = tk.Entry(self, show="*")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.pack(fill=tk.X)

    def GetInput(self):
        return self.entry.get()
    
    def AssertNoError(self):
        text = self.GetInput()
        if not text:
            FKMessageInfo("%s 不能为空" % self.name)
            return ValueError("错误，输入内容为空")

#================================================================
class FKUI_FileBrowser(tk.Frame):
    def __init__(self, master=None, store_name=None, text_label=None, **kwargs):
        super(FKUI_FileBrowser, self).__init__(master=master, **kwargs)
        self.labelText = tk.StringVar()
        btn = tk.Button(self, text = text_label or "下载到", command=self.ChooseFile)
        btn.pack(side=tk.LEFT)
        tk.Label(self, textvariable=self.labelText).pack(side=tk.LEFT, fill=tk.X)
        self.pack(fill=tk.X)
        self.storeName = store_name
        if store_name is not None:
            self.configStore = FKConfig
            savePath = self.configStore.OpReadPath(store_name) or GetWorkingDir()
        else:
            self.configStore = None
            savePath = GetWorkingDir()
        self.labelText.set(savePath)

    def AskPath(self):
        return filedialog.askdirectory(title="请选择下载文件夹")
    
    def ChooseFile(self):
        path = self.AskPath()
        if not path:
            return
        path = Path(path)
        self.labelText.set(str(path))
        if self.configStore is not None:
            self.configStore.OpStorePath(self.storeName, path)
        
    def GetPath(self):
        return self.labelText.get()

    def AssertNoError(self):
        text = self.GetPath()
        if not text:
            FKMessageInfo("%s 不能为空" % self.name)
            return ValueError("错误，路径内容为空")

#================================================================
class FKUI_FilePathBrowser(FKUI_FileBrowser):
    def AskPath(self):
        return filedialog.askdirectory(title="请选择CSV文件")

#================================================================
class FKUI_ProgressBar(ttk.Progressbar):
    def __init__(self, master=None):
        super(FKUI_ProgressBar, self).__init__(master=master, orient="horizontal", length=600, mode="determinate")
        self.pack(expand=1)

    def UpdateProgress(self, current, max=None):
        self['value'] = current
        if max is not None:
            self['maximum'] = max
        
    def ResetProgress(self):
        self.UpdateProgress(0, 0)