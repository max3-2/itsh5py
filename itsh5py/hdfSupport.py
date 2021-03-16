"""
Functions to handle h5 save and load with all types present in python.
Currently, deepdish is still used due to dependecy issues with old files,
however it will be deprecated in future releases
"""
import traceback
from collections import UserDict
from datetime import datetime
import h5py
import numpy as np
import pandas as pd
import yaml
from logging import getLogger
logger = getLogger(__package__)

from .queueHandler import add_open_file, is_open, remove_from_queue

TYPEID = '_TYPE_'

class LazyHdfDict(UserDict):
    """Helps loading data only if values from the dict are requested. This is
    done by reimplementing the __getitem__ method from dict. Additional args
    and kwargs are passen to the dict init.

    Parameters
    ------------
    h5file:
        h5py File object.
    """
    def __init__(self, _h5file=None, group='/', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h5file = None
        self._h5filename = None
        self.h5file = _h5file
        self.group = group

    @property
    def h5file(self):
        return self._h5file

    @h5file.setter
    def h5file(self, handle):
        if handle is not None:
            self._h5file = handle
            self._h5filename = handle.filename
            logger.debug(f'Added handle and file to LazyDict: {handle}::{handle.filename}')

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, group):
        self._group = group

    def __getitem__(self, key):
        """
        Returns item and loads dataset if needed. Emergency fallback when
        accessing a closed file (e.g. when using long file lists preloaded)
        is included."""
        # logger.debug(f'Accessing key: {key}')  # TOO much
        if not self.h5file:
            # Check if this was unwrapped anyway...catching tuples etc.
            item = super().__getitem__(key)
            if not isinstance(item, h5py.Dataset):
                return item

            logger.debug(f'!!File {self._h5filename} was already closed, reopening...!!')
            self.h5file = h5py.File(self._h5filename, 'r')

            sub = self.h5file
            if self._group != '/':
                for level in [g for g in self._group.split('/') if g != '']:
                    logger.debug(f'Access to subgroup iter.: {level}')
                    sub = sub[level]
                item = unpack_dataset(sub[key])
            else:
                item = unpack_dataset(self.h5file[key])

            self.h5file.close()

        else:
            item = super().__getitem__(key)
            if isinstance(item, h5py.Dataset):
                try:
                    item = unpack_dataset(item)
                    self.__setitem__(key, item)
                except ValueError:
                    logger.exception(f'Error reading {key} from {self.group} in {self.h5file}')

        return item

    def unlazy(self):
        """Unpacks all datasets. With this trick, you can call
        dict(this_instance) then to get a real dict.
        """
        load(self, lazy=False)
        self.close()

    def close(self):
        """Closes the h5file if provided at initialization."""
        if self._h5file is not None:  # set
            if self._h5file:  # ...and open
                if self._group == '/':  # Only if this is a root file...
                    remove_from_queue(self._h5file.filename)

    def __del__(self):
        try:
            self.close()
        except ImportError:  # this can happen on ipython crtl+D
            ...

    def _ipython_key_completions_(self):
        """Returns a tuple of keys.
        Special Method for ipython to get key completion support.
        """
        return tuple(self.keys())

def unpack_dataset(item):
    """Reconstruct a hdfdict dataset. Only some special unpacking for
    yaml, tuple and datetime types.

    Parameters
    ----------
    item: `h5py.Dataset`
        The dataset to unpack

    Returns
    -------
    value:
        Unpacked Data
    """
    if TYPEID in item.attrs:
        if item.attrs[TYPEID] == 'datetime':
            value = item[()]
            if hasattr(value, '__iter__'):
                value = [datetime.fromtimestamp(
                    ts) for ts in value]
            else:
                value = datetime.fromtimestamp(value)

        elif item.attrs[TYPEID] == 'yaml':
            value = item[()]
            try:
                value = yaml.safe_load(value.decode())
            except AttributeError:  # already decoded string
                value = yaml.safe_load(value)

        elif item.attrs[TYPEID] == 'tuple':
            value = 0

        elif item.attrs[TYPEID] == 'strlist':
            try:
                value = [it.decode() for it in item[()]]
            except UnicodeDecodeError:
                try:
                    value = [it.decode('latin-1') for it in item[()]]
                except UnicodeDecodeError:
                    logger.exception(f'Cant decode bytes in {item.name}')
                    value = None

        elif item.attrs[TYPEID] == 'strArray':
            logger.warning('The strArray typeID is deprecated!')
            value = item[()]
            try:
                value = yaml.safe_load(value.decode())
            except AttributeError:  # already decoded string
                value = yaml.safe_load(value)
            value = np.array(value)

        else:
            raise RuntimeError('Invalid TYPEID in h5 database')

    else:
        value = item[()]
        if isinstance(value, bytes):
            # This is most likely a str...trying to decode that right away
            try:
                value = item.asstr()[()]
            except Exception as e:
                logger.warning(f'Converting bytes to str failed: {e}')
                value = item[()]

    return value

def load(hdf, lazy=True, unpacker=unpack_dataset):
    """Returns a dictionary containing the groups as keys and the datasets as
    values from given hdf file.

    Parameters
    ----------
    hdf: `string`, `h5py.File()`, `h5py.Group()`
        (path to file) or h5 types
    lazy: `bool`
        If True, the datasets are lazy loaded at the moment an item is
        requested. Defaults to False, future releases planned with True.
    unpacker : `callable`
        Unpack function gets `value` of type h5py.Dataset.
        Must return the data you would like to have it in the returned dict.

    Returns
    -------
    result : `dict`
        The dictionary containing all groupnames as keys and datasets as
        values.
    """
    def _recurseIterData(value, isTuple=False):
        dl = list()
        for _, v in value.items():
            # Tuples wont work lazy so we have to unpack them right
            # away, anything else is way to complicated
            if TYPEID in v.attrs:
                if v.attrs[TYPEID] == 'tuple':
                    dl.append(_recurseIterData(v, True))
                elif v.attrs[TYPEID] == 'list':
                    dl.append(_recurseIterData(v))
                else:
                    dl.append(unpacker(v))
            else:
                dl.append(unpacker(v))

        if isTuple:
            dl = tuple(dl)

        return dl

    def _recurse(hdfobject, datadict):
        for key, value in hdfobject.items():
            if 'pandas_type' in value.attrs:
                # This is a dataframe or a series...
                datadict[key] = pd.read_hdf(hdfobject.filename, key)
            else:
                if TYPEID in value.attrs:
                    if value.attrs[TYPEID] == 'tuple':
                        datadict[key] = _recurseIterData(value, True)
                    elif value.attrs[TYPEID] == 'list':
                        datadict[key] = _recurseIterData(value)
                    else:
                        if lazy:
                            datadict[key] = value
                        else:
                            datadict[key] = unpacker(value)

                elif isinstance(value, h5py.Group) or isinstance(value, LazyHdfDict):
                    if lazy:
                        datadict[key] = LazyHdfDict()
                        if isinstance(value, h5py.Group):
                            logger.debug('LazyDict from Group - searching parent...')
                            datadict[key].h5file = value.file
                            datadict[key].group = value.name
                            logger.debug(
                                f'Created child LazyDict of Group {datadict[key].group} in File {datadict[key].h5file}')
                        else:
                            datadict[key].h5file = hdfobject
                    else:
                        datadict[key] = {}

                    datadict[key] = _recurse(value, datadict[key])

                elif isinstance(value, h5py.Dataset):
                    if lazy:
                        datadict[key] = value
                    else:
                        datadict[key] = unpacker(value)

        return datadict

    # Fixing windows issues
    if '\\' in hdf:
        hdf = hdf.replace('\\', '/')
        logger.debug('Found windows style paths, replacing separator')

    # First check if lazy and file is already loaded
    if lazy:
        data = is_open(hdf)
        if data is not None:
            return data

    # Else open the file and go on
    hdfl = h5py.File(hdf, 'r')

    if lazy:
        data = LazyHdfDict(_h5file=hdfl)
        add_open_file(data)

    else:
        data = {}

    # Attributes are loaded into a dict so this does not explode in complexity
    # Unwrap them on the way
    data['attrs'] = {k: v for k, v in hdfl.attrs.items()}

    # Finally, add the rest from the file. If not lazy, close it right away.
    # If lazy, the file must stay open.
    data = _recurse(hdfl, data)

    if lazy:
        return data

    hdfl.close()
    if len(data.keys()) == 1:
        data = data[list(data.keys())[0]]

    return data

def pack_dataset(hdfobject, key, value, compress):
    """Packs a given key value pair into a dataset in the given hdfobject.

    Fairly simple extra routine that checks for datetime. If a value exists
    that is not conformable with hdfthe the function tries to serialize the
    calue using yaml as last resort, raising a TypeWarning on the go. If yaml
    fails, the exception of the failure is raised and not handled, thus
    having the code fail!

    Parameters
    ------------
    hdfobject: `h5py.File` or similar to save the data to.
        The object to pack
    key: `string`
        Indetifier to write the data to.
    value:
        Data value
    compress: `tuple`
        Tuple of (bool compress, 0-9 level) which specifies the compression.
    """
    def _dumpArray(name, array, group, compress):
        if len(array) == 0:
            return

        logger.debug(f'Dumping array {name} to file')
        if compress[0]:
            subset = group.create_dataset(
                name=name, data=array, compression='gzip',
                compression_opts=compress[1])
        else:
            subset = group.create_dataset(
                name=name, data=array)

        if np.issubdtype(array.dtype, bytes) or array.dtype.str.startswith('|S'):
            logger.debug(f'Numpy binary (str?) array found for {name}, adding type hint to unwrap as list')
            subset.attrs.create(
                name=TYPEID,
                data=str('strlist'))

    def _iterateIterData(hdfobject, key, value, typeID):
        ds = hdfobject.create_group(key)
        elementsOrder = int(np.floor(np.log10(len(value))) + 1)
        fmt = 'i_{:0' + str(elementsOrder) + 'd}'
        for i, v in enumerate(value):
            if isinstance(v, tuple):
                _iterateIterData(ds, fmt.format(i), v, "tuple")
            elif isinstance(v, list):
                # check for mixed type, if yes, dump to group as tuple
                if not all([type(v) == type(value[0]) for v in value]):
                    _iterateIterData(hdfobject, key, value, "list")
                else:
                    _iterateIterData(ds, fmt.format(i), v, "list")
            else:
                if isinstance(v, np.ndarray):
                    _dumpArray(fmt.format(i), v, ds, compress)
                else:
                    if isinstance(v, np.str_):
                        v = str(v)
                    ds.create_dataset(name=fmt.format(i), data=v)

        ds.attrs.create(
            name=TYPEID,
            data=str(typeID))

    logger.debug(f'Packing {key}, with type {type(value)}')

    isdt = None
    if isinstance(value, datetime):
        value = value.timestamp()
        isdt = True

    elif hasattr(value, '__iter__'):
        if all(isinstance(i, datetime) for i in value):
            value = [item.timestamp() for item in value]
            isdt = True

    try:
        if isinstance(value, tuple):
            _iterateIterData(hdfobject, key, value, "tuple")
            return

        # Catching list of strings or list of np.str_ or mixed lists..
        if isinstance(value, list):
            # check if all float or all int, then its ok to pass on
            if all([isinstance(v, (int, float)) for v in value]):
                value = np.array(value)

            # check for mixed type, if yes, dump to group same as tuple
            elif not all([type(v) == type(value[0]) for v in value]):
                _iterateIterData(hdfobject, key, value, "list")
                return

            # List of (np) string
            elif all([isinstance(v, (str, np.str_)) for v in value]):
                value = np.array([str(v).encode() for v in value])
                logger.debug('List of strings will be binarized as array, adding type '
                             f'attribute for later decompression for {key}...')

            # List of numpy arrays (changing shape possible)
            elif all([isinstance(v, np.ndarray) for v in value]):
                _iterateIterData(hdfobject, key, value, "list")
                return

        logger.debug(f'Trying to save {key} with type {type(value)}')
        if isinstance(value, np.ndarray):
            _dumpArray(key, value, hdfobject, compress)

        else:
            if compress[0]:
                if isdt:
                    logger.debug('No compression for datetime...')
                else:
                    logger.debug('No compression for unknown type...')

            ds = hdfobject.create_dataset(name=key, data=value)

        if isdt:
            ds.attrs.create(
                name=TYPEID,
                data=str("datetime"))

    except TypeError:
        # Typecast to def. string for yaml. If it was a string, no action
        # needed but to dump it
        if isinstance(value, np.str_) or isinstance(value, str):
            value = str(value)
            ds = hdfobject.create_dataset(
                name=key,
                data=value
                )
        else:
            # Obviously the data was not serializable. To give it
            # a last try; serialize it to yaml but expect this to go down the
            # crapper
            try:
                ds = hdfobject.create_dataset(
                    name=key,
                    data=yaml.safe_dump(value)
                )
                ds.attrs.create(
                    name=TYPEID,
                    data=str("yaml"))
            except yaml.representer.RepresenterError:
                logger.error(
                    'Cannot dump {:s} to h5, incompatible data format '
                    'even when using serialization.'.format(key))
                logger.exception('EXP')
                logger.error(50*'-')


def dump(hdf, data, compress=(True, 4), packer=pack_dataset, *args, **kwargs):
    """
    Adds keys of given dict as groups and values as datasets to the given
    hdf-file (by string or object) or group object.

    Parameters
    -----------
    hdf: `string`, `h5py.File()`, `h5py.Group()`
        (path to file) or h5 types
    data: `dict`
        The dictionary containing only string or tuple keys and
        data values or dicts as above again.
    packer: `callable`
        Callable gets `hdfobject, key, value` as input.
        `hdfobject` is considered to be either a h5py.File or a h5py.Group.
        `key` is the name of the dataset.
        `value` is the dataset to be packed and accepted by h5py.
        Defaults to `pack_dataset()`
    compress: `tuple`
        Try to compress arrays, use carfully. If on, gzip mode is used in
        every case. Defaults to `(False, 0)`. When `(True,...)` the second
        element specifies the level from `0-9`, see h5py doc.

    Returns
    --------
    hdf: `string`,
        Path to new file
    """
    def _recurse(datadict, hdfobject):
        for key, value in datadict.items():
            if isinstance(key, tuple):
                key = '_'.join((str(i) for i in key))
            if isinstance(value, (dict, LazyHdfDict)):
                hdfgroup = hdfobject.create_group(key)
                _recurse(value, hdfgroup)
            else:
                if isinstance(value, (pd.DataFrame, pd.Series)):
                    logger.warning('Currently, pandas must be stored in root')
                else:
                    packer(hdfobject, key, value, compress)

    if not hdf.endswith('.h5'): hdf += '.h5'

    # Single dataframe
    if isinstance(data, (pd.DataFrame, pd.Series)):
        if compress[0]:
            store = pd.HDFStore(hdf, compress=compress[1], complib='zlib')
        else:
            store = pd.HDFStore(hdf, compress=None)

        store.put('pd_dataframe', data)
        store.close()

        return hdf

    # Dataframe in dict. Pandas is stored in advance...stupid file lock in pandas....
    pandasKeys = list()
    fileMode = 'w'
    for k, v in data.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            if compress[0]:
                v.to_hdf(hdf, key=k, mode=fileMode, compress=compress[1], complib='zlib')
            else:
                v.to_hdf(hdf, key=k, mode=fileMode, compress=None)
            pandasKeys.append(k)
            fileMode = 'r+'

    if pandasKeys:
        data = data.copy()
        for k in pandasKeys:
            _ = data.pop(k)

    with h5py.File(hdf, fileMode, *args, **kwargs) as hdfl:
        # handle manually loaded atts
        if 'attrs' in data:
            for k, v in data['attrs'].items():
                hdfl.attrs[k] = v
            _ = data.pop('attrs')

        _recurse(data, hdfl)

    return hdf


__all__ = ['dump', 'load', 'LazyHdfDict']
