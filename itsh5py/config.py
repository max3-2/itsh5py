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
allow_overwrite: `bool`, defaults to `False`
    If set to True, files will be overwritten if existing without warning.
    On default value of `False` the file mode will be `a` which is safe but
    can lead to exceptions if datasets already exist.
squeeze_single: `bool`, defaults to `False`
    If set to True, unpacked data containing a single key will be unpacked.
    This can lead to issues with single key dicts containing sub dicts,
    thus the default is the safer version (False)
"""
default_suffix = '.hdf'
use_lazy = True
default_compression = (True, 5)
allow_fallback_open = False
allow_overwrite = False
squeeze_single = False
