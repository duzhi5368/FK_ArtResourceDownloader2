import os
import time
import hashlib

from functools import wraps
from threading import Thread
from pathlib import Path

from Utils.FKLogger import FKLogger
from Core.FKTaskItem import FKTaskItem

def RunAsDaemonThread(func, *args, name=None, **kwargs):
    if name is None:
        name = func.__name__
    t = Thread(target=func, args=args, kwargs=kwargs, name=name)
    t.setDaemon(True)
    t.start()
    return t

def ConvertByte2KB(sizeInByte):
    return sizeInByte / 1024

def CalcFileSize(fileName):
    sizeInByte = os.path.getsize(fileName)
    return ConvertByte2KB(sizeInByte)

# 装饰器，插入函数已进行多次执行
def Retry(maxTimes=3):

    def wrapper(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            round = 0
            while round <= maxTimes:
                round += 1
                try:
                    return func(*args,**kwargs)
                except Exception:
                    if round > maxTimes:
                        FKLogger.error("调用函数 %s 异常" % func.__name__)
                        break
                    time.sleep(1)
            return None
        return wrapped

    return wrapper

def NormalizeName(name):
    name = name.replace("/", " ")
    name = name.replace("\\", " ")
    name = name.strip()
    name = name.replace(" ", '-')
    return name

def NormalizePath(path):
    return Path(path).absolute()

def GetFileHash(fileContent):
    m = hashlib.md5()
    m.update(fileContent)
    return m.digest().hex()

def GetNameAndExtFromUrl(url):
    fileName = url.split('/')[-1]
    if "?" in fileName:
        fileName = fileName.split('?')[:-1]
        fileName = '?'.join(fileName)
    name = fileName.split('.')[:-1]
    name = '.'.join(name)
    ext = fileName.split('.')[-1]
    return name, ext

def GetFileExtension(imageName):
    return imageName.split('.')[-1]

def GetFilenameFromUrl(url):
    name, ext = GetNameAndExtFromUrl(url)
    return ".".join(name, ext)

def GetNameWithHashFromUrl(url, fileContent):
    name, ext = GetNameAndExtFromUrl(url)
    nameHash = GetFileHash(fileContent)
    fileName = "-".join([name, nameHash])
    fileName = ".".join([fileName, ext])
    return fileName

def NormalizeFileName(filename):
    filename = filename.replace("/", "_")
    filename = filename.replace("?", "__")
    filename = filename.replace(":", "___")
    filename = filename.replace("../", "_")
    filename = filename.replace("..\\", "_")
    filename = filename.replace("\\", "_")
    return filename