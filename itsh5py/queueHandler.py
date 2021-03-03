from collections import deque
from logging import getLogger
logger = getLogger(__package__)

openFiles = deque()
maxFiles = 3

def addOpenFile(lazyDict):
    if len(openFiles) >= maxFiles:
        close(openFiles.pop())

    openFiles.appendleft(lazyDict)

def isOpen(file):
    filenames = [h.h5file.filename for h in openFiles]
    if file in filenames:
        return openFiles[filenames.index(file)]
    else:
        return None

def removeFromQueue(file):
    filenames = [h.h5file.filename for h in openFiles]
    if file in filenames:
        handle = openFiles[filenames.index(file)]
        openFiles.remove(handle)
        close(handle)

def close(lazyDict):
    if lazyDict.h5file and hasattr(lazyDict.h5file, 'close'):
        lazyDict.h5file.close()
