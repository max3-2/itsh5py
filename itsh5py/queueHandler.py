from collections import deque

openFiles = deque()
maxFiles = 6

def addOpenFile(handle):
    if len(openFiles) > maxFiles:
        close(openFiles.pop())

    openFiles.appendleft(handle)

def isOpen(file):
    filenames = [h.filename for h in openFiles]
    if file in filenames:
        return openFiles[filenames.index(file)]
    else:
        return None

def removeFromQueue(file):
    filenames = [h.filename for h in openFiles]
    if file in filenames:
        handle = openFiles[filenames.index(file)]
        openFiles.remove(handle)
        close(handle)

def close(handle):
    if hasattr(handle, 'close'):
        handle.close()
