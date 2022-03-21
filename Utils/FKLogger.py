import logging
import sys

from Utils.Const import __FK_LOGGER_NAME__, __LOG_FILE__

def GetLogger(loggerName):
    logLevel = logging.INFO

    if "--debug-%s" % loggerName in sys.argv:
        logLevel = logging.DEBUG

    dataFormat = "%(levelname)s - %(asctime)-15s - %(filename)s - line %(lineno)d --> %(message)s"
    dateFormat = "%a %d %b %Y %H:%M:%S"
    logFormatter = logging.Formatter(dataFormat, dateFormat)

    streamHandler = logging.StreamHandler()
    fileHandler = logging.FileHandler(__LOG_FILE__)
    streamHandler.setFormatter(logFormatter)

    logger = logging.getLogger(loggerName)
    logger.setLevel(level=logLevel)
    logger.addHandler(streamHandler)
    logger.addHandler(fileHandler)
    return logger

FKLogger = GetLogger(__FK_LOGGER_NAME__)

__all__ = ( "FKLogger" )