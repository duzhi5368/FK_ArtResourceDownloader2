import tkinter as tk
import webbrowser as wb
from tkinter import ttk
from Utils.Const import __VERSION__
from GUI.FKDownloader import FKDownloaders
from GUI.FKUITookits import FKMessageInfo

class FKApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super(FKApp, self).__init__(*args, **kwargs)
        self.tabs = ttk.Notebook(self)
        self.title("FK美术资源下载器  v%s" % __VERSION__)
        self.BuildMenu()
        for FKDownloader in FKDownloaders:
            self.tabs.add(FKDownloader(self), text=FKDownloader.title)
        self.tabs.pack(side=tk.LEFT)
    
    def BuildMenu(self):
        menuBar = tk.Menu(self)
        helpMenu = tk.Menu(menuBar)
        helpMenu.add_command(label="帮助", command=self.OpenHelp)
        helpMenu.add_command(label="关于", command=self.ShowAbout)
        helpMenu.add_command(label="联系我们", command=self.ContractUs)
        menuBar.add_cascade(label="帮助", menu=helpMenu)
        self.config(menu=menuBar)

    @staticmethod
    def OpenHelp():
        url = 'https://github.com/duzhi5368/FK_ArtResourceDownloader'
        wb.open_new_tab(url)
    
    @staticmethod
    def ShowAbout():
        url = 'https://github.com/duzhi5368/FK_ArtResourceDownloader'
        wb.open_new_tab(url)
    
    @staticmethod
    def ContractUs():
        FKMessageInfo("有任何问题可联系作者邮箱: duzhi5368@gmail.com")


def main():
    app = FKApp()
    app.mainloop()

if __name__ == "__main__":
    main()
    