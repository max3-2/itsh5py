from collections import deque
from logging import getLogger
logger = getLogger(__package__)

open_files = deque()
max_files = 12

def add_open_file(lazyDict):
    """Adds a file (or better a LazyDict reference) to the queue."""
    if len(open_files) >= max_files:
        close(open_files.pop())
        logger.debug('Removed file from queue due to size limit')

    open_files.appendleft(lazyDict)
    logger.debug(f'Added new file to queue: {lazyDict.h5file.filename}')

def is_open(file):
    """Checks if a file is in the queue and thus oenened in memory."""
    filenames = [h.h5file.filename for h in open_files]
    if file in filenames:
        logger.debug(f'File {file} found in memory - returning...')
        return open_files[filenames.index(file)]
    else:
        return None

def remove_from_queue(file):
    """Removes file from the queue and from memory. Only if file exists"""
    filenames = [h.h5file.filename for h in open_files]
    if file in filenames:
        handle = open_files[filenames.index(file)]
        open_files.remove(handle)
        close(handle)
        logger.debug(f'File {file} removed from queue')
    else:
        logger.debug(f'File {file} not found in queue, can not remove!')

def close(lazyDict):
    """Closes a LazyDict. This is a small wrapper to check if close will work."""
    if lazyDict.h5file and hasattr(lazyDict.h5file, 'close'):
        lazyDict.h5file.close()

def open_filenames():
    """Show file paths of open files"""
    return [h.h5file.filename for h in open_files]

