"""
Package-wide config options

default_suffix: `str`, defaults to `.hdf`
    Default suffix to use for saveing hdf files.
use_lazy: `bool`, defaults to `True`
    Default setting for lazyness on loading.
default_compression: `tuple`, defaults to `(True, 5)`
    Default setting for gzip compression. First element is yes or no, second
    is level of compression. See `h5py` docs for more details.
allow_fallback_open: `bool`, defaults to `True`
    If an item is unwrapped from a closed file (e.g. when holding many files
    open in long list comprehension), this allows a quick reopen and getting
    of a specified item. This can substantially slow down data handling,
    increase memory load and lead to access errors on files open by other
    applications.
"""
default_suffix = '.hdf'
use_lazy = True
default_compression = (True, 5)
allow_fallback_open = False
