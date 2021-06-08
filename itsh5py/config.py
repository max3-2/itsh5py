"""
Package-wide config options

default_suffix: `str`, defaults to `.hdf`
    Default suffix to use for saveing hdf files.
use_lazy: `bool`, defaults to `True`
    Default setting for lazyness on loading.
default_compression: `tuple`, defaults to `(True, 5)`
    Default setting for gzip compression. First element is yes or no, second
    is level of compression. See `h5py` docs for more details.
"""
default_suffix = '.hdf'
use_lazy = True
default_compression = (True, 5)
