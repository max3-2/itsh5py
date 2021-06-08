"""Main init file of itsh5py
"""
# Metadata
# Meta information
__title__ = 'itsh5py'
__version__ = '0.6.0'
__date__ = '2021–06–15'
__author__ = 'Max Elfner'
__copyright__ = 'Max Elfner, ITS, KIT https://www.its.kit.edu'
__license__ = 'MIT'

from .hdf_support import save, load, LazyHdfDict
dump = save  # This is an alias since the two names are used often
from .queue_handler import max_open_files, open_files
from . import config
