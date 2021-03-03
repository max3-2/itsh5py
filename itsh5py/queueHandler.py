from collections import deque

openFiles = deque()
maxFiles = 3

def addOpenFile(lazyDict):
    if len(openFiles) > maxFiles:
        close(openFiles.pop())

    openFiles.appendleft(lazyDict)

def isOpen(file):
    filenames = [h._h5file.filename for h in openFiles]
    if file in filenames:
        return openFiles[filenames.index(file)]
    else:
        return None

def removeFromQueue(file):
    filenames = [h._h5file.filename for h in openFiles]
    if file in filenames:
        handle = openFiles[filenames.index(file)]
        openFiles.remove(handle)
        close(handle)

def close(lazyDict):
    lazyDict.close()
