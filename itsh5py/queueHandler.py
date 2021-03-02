from collections import OrderedDict

openFiles = OrderedDict()
maxFiles = 6

def addOpenFile(file, handle):
    if len(openFiles) > maxFiles:
        close(openFiles.popitem(False)[0])

    openFiles[file] = handle

def isOpen(file):
    return openFiles.get(file, None)

def close(file):
    openFiles.pop(file).close()
