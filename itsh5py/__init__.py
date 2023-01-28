"""Python datatype support for hdf files
"""
# Metadata
__title__ = 'itsh5py'
__version__ = '0.7.2'
__date__ = '2023-01-28'
__author__ = 'Max Elfner'
__copyright__ = 'Max Elfner'
__license__ = 'MIT'

from .hdf_support import save, load, LazyHdfDict
from .queue_handler import max_open_files, open_filenames
from . import config
