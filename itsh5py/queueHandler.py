from collections import deque
from logging import getLogger
logger = getLogger(__package__)

openFiles = deque()
maxFiles = 10

def addOpenFile(lazyDict):
    """Adds a file (or better a LazyDict reference) to the queue."""
    if len(openFiles) >= maxFiles:
        close(openFiles.pop())
        logger.debug('Removed file from queue due to size limit')

    openFiles.appendleft(lazyDict)
    logger.debug('Added new file to queue')

def isOpen(file):
    """Checks if a file is in the queue and thus oenened in memory."""
    filenames = [h.h5file.filename for h in openFiles]
    if file in filenames:
        logger.debug('File found in memory - returning...')
        return openFiles[filenames.index(file)]
    else:
        return None

def removeFromQueue(file):
    """Removes file from the queue and from memory. Only if file exists"""
    filenames = [h.h5file.filename for h in openFiles]
    if file in filenames:
        handle = openFiles[filenames.index(file)]
        openFiles.remove(handle)
        close(handle)
        logger.debug(f'File {file} removed from queue')
    else:
        logger.debug(f'File {file} not found in queue, can not remove!')

def close(lazyDict):
    """Closes a LazyDict. This is a small wrapper to check if close will work."""
    if lazyDict.h5file and hasattr(lazyDict.h5file, 'close'):
        lazyDict.h5file.close()
