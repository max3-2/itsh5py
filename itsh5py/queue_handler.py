"""
Base module to handle the queue of open (in memory) files. The main
important settings of how many filse are allowed (`max_open_files`) and
the currently open files are exposed in the main API.
"""
from collections import deque
import atexit
from logging import getLogger

logger = getLogger(__package__)

open_files = deque()
max_open_files = 12


def add_open_file(lazy_dict):
    """Adds a file (or better a LazyDict reference) to the queue."""
    if len(open_files) >= max_open_files:
        close(open_files.pop())
        logger.debug('Removed file from queue due to size limit')

    open_files.appendleft(lazy_dict)
    logger.debug(f'Added new file to queue: {lazy_dict.h5file.filename}')


def is_open(filepath):
    """Checks if a file is in the queue and thus oenened in memory."""
    filenames = [h.h5file.filename for h in open_files]
    if filepath.name in filenames:
        logger.debug(f'File {filepath.name} found in memory - returning...')
        return open_files[filenames.index(filepath.name)]
    else:
        return None


def remove_from_queue(file):
    """
    Removes file from the queue and from memory. Only if file exists.

    This is more complicated than it should be. The issue is that in the queue
    the actual LazyHdfDict are stored and comparison of those on remove can
    fail. So comaprison is done on file name basis and removal via index.
    """
    filenames = [h.h5file.filename for h in open_files]
    logger.debug(f'Removing {file} from queue: {filenames}')
    if file in filenames:
        handle_index = filenames.index(file)
        handle = open_files[handle_index]
        close(handle)
        del open_files[handle_index]
        logger.debug(f'File {file} removed from queue')
    else:
        logger.debug(f'File {file} not found in queue, can not remove!')


def close(lazy_dict):
    """Closes a LazyDict. This is a small wrapper to check if close will work."""
    if lazy_dict.h5file and hasattr(lazy_dict.h5file, 'close'):
        lazy_dict.h5file.close()


def open_filenames():
    """Show file paths of open files"""
    return [h.h5file.filename for h in open_files]


@atexit.register
def cleanup():
    """
    This will be run atexit and ensures that no references persist in
    memory and all hdf files are freed.
    """
    for lzd in open_files:
        close(lzd)
