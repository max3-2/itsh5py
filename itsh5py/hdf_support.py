"""
Functions to handle h5 save and load with all types present in python.
Currently, deepdish is still used due to dependecy issues with old files,
however it will be deprecated in future releases
"""
import os
import platform
from pathlib import Path, PureWindowsPath
from collections import UserDict
from datetime import datetime
import h5py
import numpy as np
import pandas as pd
import yaml
from logging import getLogger

from .queue_handler import add_open_file, is_open, remove_from_queue
from . import config

logger = getLogger(__package__)

TYPEID = '_TYPE_'


def _tree(hdf, levels=[], max_depth=None, buffer=None, printout=True):
    """
    Displays the hdf tree for lazy dicts.

    This function displays a representation of the hdf file tree without
    loading the actual datasets. Basic information is printed.
    """
    if max_depth and len(levels) > max_depth:
        return
    markers = ''.join('   ' if last else '│  ' for last in levels[:-1])
    markers += '' if not levels else '└─ ' if levels[-1] else '├─ '

    if buffer is None:
        buffer = ''

    if isinstance(hdf, h5py.File):
        msg = f'{markers}{os.path.basename(hdf.filename)}'
        if printout:
            print(msg)
        buffer += msg + '\n'

        children = hdf.keys()
        last = len(children) - 1
        for (index, child) in enumerate(children):
            buffer = _tree(
                hdf[child], levels + [index == last], max_depth, buffer=buffer,
                printout=printout)

    elif isinstance(hdf, h5py.Group):
        msg = f'{markers}Group {hdf.name}'
        if printout:
            print(msg)
        buffer += msg + '\n'

        children = hdf.keys()
        last = len(children) - 1
        for (index, child) in enumerate(children):
            buffer = _tree(
                hdf[child], levels + [index == last], max_depth, buffer=buffer,
                printout=printout)

    elif isinstance(hdf, h5py.Dataset):
        if hdf.ndim == 0 and TYPEID not in hdf.attrs:
            msg = f'{markers}{hdf.name}::{hdf[()]}'
        else:
            msg = f'{markers}{hdf.name}::{hdf.shape}'

        if TYPEID in hdf.attrs:
            msg += f' (py-type: {hdf.attrs[TYPEID]})'

        if printout:
            print(msg)
        buffer += msg + '\n'

    else:
        ...

    return buffer


class LazyHdfDict(UserDict):
    """
    Helps loading data only if values from the dict are requested. This is
    done by reimplementing the __getitem__ method from dict. Other convenience
    functions are added to work with the hdf files as backend.

    Parameters
    ------------
    _h5file: 'h5py.File', optional
        h5py File object or None
    group: `str`, optional
        Group to anchor the LazyHdfDict into.
    args, kwargs:
        Passed to the parent `UserDcit` implemented type.
    """
    def __init__(self, _h5file=None, group='/', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._h5file = None
        self._h5filename = None
        self.h5file = _h5file
        self.group = group

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        buffer = _tree(self.h5file, printout=False)
        return buffer

    @property
    def h5file(self):
        """File handle of the `h5py.File()` object behind the `LazyHdfDict`."""
        return self._h5file

    @h5file.setter
    def h5file(self, handle):
        if handle is not None:
            if not isinstance(handle, (h5py.File, h5py.Dataset)):
                raise TypeError('Invalid h5file handle type')
            self._h5file = handle
            self._h5filename = handle.filename
            logger.debug(f'Added handle and file to LazyDict: {handle}::{handle.filename}')

    @property
    def group(self):
        """Root group of the `LazyHdfDict`."""
        return self._group

    @group.setter
    def group(self, group):
        if isinstance(group, str):
            if group.startswith('/'):
                self._group = group
                return
        logger.warning('Cant set group, must be a string that starts with a /')

    def __getitem__(self, key):
        """
        Returns item and loads dataset if needed. Emergency fallback when
        accessing a closed file (e.g. when using long file lists preloaded)
        is included."""
        if not self.h5file:
            # Check if this was unwrapped anyway...catching tuples etc.
            item = super().__getitem__(key)
            if not isinstance(item, h5py.Dataset):
                return item

            if config.allow_fallback_open:
                logger.debug(f'File {self._h5filename} was already closed, reopening...')
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
                logger.error('Cant access data in closed file which is not '
                             'unwrapped.')
                return None

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
        """Unpacks all datasets and closes the Lazy reference
        """
        unlazied = dict(self)
        self.close()
        return unlazied

    def close(self):
        """Closes the h5file if provided at initialization.

        Unpackig will keep on working using the fallback routine if enabled.
        """
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
    """Reconstruct a hdfdict dataset.

    This holds all special **unpacking** procedures for types not natively
    supported by `h5py`.

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

        elif item.attrs[TYPEID] == 'list_str':
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

        elif item.attrs[TYPEID] == 'str_array':
            value = item[()]
            init_shape = value.shape
            try:
                value = np.array(
                    [v.decode() for v in value.ravel()]).reshape(init_shape)
            except UnicodeDecodeError:
                try:
                    value = np.array(
                        [v.decode() for v in value.ravel()]).reshape(init_shape)
                except UnicodeDecodeError:
                    logger.exception(f'Cant decode bytes in {item.name}')
                    value = None

        elif item.attrs[TYPEID] == 'list_arr':
            value = list(item[()])

        elif item.attrs[TYPEID] == 'path':
            value = Path(item[()].decode())

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


def load(hdf, unpack_attrs=False, unpacker=unpack_dataset):
    """Returns a dictionary containing the groups as keys and the datasets as
    values from given hdf file.

    Parameters
    ----------
    hdf: `string, Path`
        Path to hdf file.
    unpack_attrs : `bool`, optional
        If True attrs from h5 file will be unpacked and are available as dict
        key attrs, no matter if lazy or not. Defaults to False.
    unpacker : `callable`
        Unpack function gets `value` of type h5py.Dataset.
        Must return the data you would like to have it in the returned dict.

    Returns
    -------
    result : `dict`, `LazyHdfDict`
        The dictionary containing all groupnames as keys and datasets as
        values. Can be lazy and thus not unwrapped.
    """
    lazy = config.use_lazy

    def _recurse_iter_data(value, is_tuple=False):
        dl = list()
        for _, v in value.items():
            # Tuples wont work lazy so we have to unpack them right
            # away, anything else is way to complicated
            if TYPEID in v.attrs:
                if v.attrs[TYPEID] == 'tuple':
                    dl.append(_recurse_iter_data(v, True))
                elif v.attrs[TYPEID] == 'list':
                    dl.append(_recurse_iter_data(v))
                elif v.attrs[TYPEID] == 'path_list' or v.attrs[TYPEID] == 'path_tuple':
                    dl.append(_recurse_iter_data(v))

                else:
                    dl.append(unpacker(v))
            else:
                dl.append(unpacker(v))

        if is_tuple:
            dl = tuple(dl)

        return dl

    def _recurse(hdfobject, datadict):
        for key, value in hdfobject.items():
            if 'pandas_type' in value.attrs:
                # This is a dataframe or a series...might be in subgroup
                if isinstance(hdfobject, h5py.File):
                    datadict[key] = pd.read_hdf(hdfobject.filename, key)
                else:
                    datadict[key] = pd.read_hdf(hdfobject.file.filename,
                                                f'{hdfobject.name}/{key}')
            else:
                if TYPEID in value.attrs:
                    if value.attrs[TYPEID] == 'tuple':
                        datadict[key] = _recurse_iter_data(value, True)
                    elif value.attrs[TYPEID] == 'list':
                        datadict[key] = _recurse_iter_data(value)
                    elif value.attrs[TYPEID] == 'path_list' or value.attrs[TYPEID] == 'path_tuple':
                        datadict[key] = _recurse_iter_data(value, 'tuple' in value.attrs[TYPEID])

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

    if isinstance(hdf, str):
        # Fixing windows issues with manually specified pathes
        if platform.system() == 'Windows':
            hdf = PureWindowsPath(hdf)

        hdf = Path(hdf)

    if not hdf.suffix:
        hdf = hdf.parent / (hdf.name + config.default_suffix)

    # First check if lazy and file is already loaded
    if lazy:
        data = is_open(hdf)
        if data is not None:
            if 'attrs' not in data and unpack_attrs:
                logger.debug('Reloading file attributes to unwrap...')
                data['attrs'] = {k: v for k, v in data.h5file.attrs.items()}
                return data
            else:
                return data

    # Else open the file and go on
    hdf_handle = h5py.File(hdf, 'r')

    if lazy:
        data = LazyHdfDict(_h5file=hdf_handle)
        add_open_file(data)

    else:
        data = {}

    # Attributes are loaded into a dict if asked for. Else they will remain
    # in the h5file
    if unpack_attrs:
        data['attrs'] = {k: v for k, v in hdf_handle.attrs.items()}

    # Finally, add the rest from the file. If not lazy, close it right away.
    # If lazy, the file must stay open.
    data = _recurse(hdf_handle, data)

    if lazy:
        return data

    hdf_handle.close()

    # squeeze singleton data from dict, only if enabled. Default is off
    if config.squeeze_single and len(data.keys()) == 1:
        data = data[list(data.keys())[0]]

    return data


def pack_dataset(hdfobject, key, value, compress):
    """Packs a given key value pair into a dataset in the given hdfobject.

    This holds all special **packing** procedures for types not natively
    supported by `h5py`. If a value exists that is not conformable with hdf,
    the the function tries to adapt or serialize the value using yaml as last
    resort, raising a TypeWarning on the go.
    If yaml fails, the exception of the failure is raised and not handled, thus
    having the code fail, e.g. saving is only successful if all datasets were
    packable!

    Parameters
    ------------
    hdfobject: `h5py.File` or similar to save the data to.
        The object to pack the key-value in to.
    key: `string`
        Indetifier to write the data to.
    value: `any`
        Data value
    compress: `tuple`
        Tuple of (bool compress, 0-9 level) which specifies the compression.
    """
    def _dump_array(name, array, group, compress, type_id=None):
        if len(array) == 0:
            return

        # This is a string array - to avoid unicode this will be made binary
        # and stored with a unique typeid
        if array.dtype.str.startswith('<U'):
            logger.debug('(unicode) str array found, making list')
            init_shape = array.shape
            array = np.array([str(v).encode() for v in array.ravel()]).reshape(init_shape)
            if compress[0]:
                subset = group.create_dataset(
                    name=name, data=array, compression='gzip',
                    compression_opts=compress[1])
            else:
                subset = group.create_dataset(
                    name=name, data=array)
            subset.attrs.create(
                name=TYPEID,
                data=str('str_array'))

            return

        logger.debug(f'Dumping array {name} to file')
        if compress[0]:
            subset = group.create_dataset(
                name=name, data=array, compression='gzip',
                compression_opts=compress[1])
        else:
            subset = group.create_dataset(
                name=name, data=array)

        if type_id is not None:
            subset.attrs.create(
                name=TYPEID,
                data=str(type_id))

    def _iterate_iter_data(hdfobject, key, value, typeID, inner_id=None):
        ds = hdfobject.create_group(key)
        elementsOrder = int(np.floor(np.log10(len(value))) + 1)
        fmt = 'i_{:0' + str(elementsOrder) + 'd}'
        for i, v in enumerate(value):
            if isinstance(v, tuple):
                _iterate_iter_data(ds, fmt.format(i), v, "tuple", inner_id)
            elif isinstance(v, list):
                # check for mixed type, if yes, dump to group as tuple
                if not all([isinstance(v, type(value[0])) for v in value]):
                    _iterate_iter_data(hdfobject, key, value, "list", inner_id)
                else:
                    _iterate_iter_data(ds, fmt.format(i), v, "list", inner_id)
            else:
                if isinstance(v, np.ndarray):
                    _dump_array(fmt.format(i), v, ds, compress)
                else:
                    if isinstance(v, np.str_):
                        v = str(v)
                    inner = ds.create_dataset(name=fmt.format(i), data=v)

                    if inner_id is not None:
                        logger.debug(f'Adding innermost id {inner_id} to {inner}')
                        inner.attrs.create(
                            name=TYPEID,
                            data=str(inner_id))

        ds.attrs.create(
            name=TYPEID,
            data=str(typeID))

    logger.debug(f'Packing {key}, with type {type(value)}')

    isdt = False
    if isinstance(value, datetime):
        value = value.timestamp()
        isdt = True

    elif hasattr(value, '__iter__'):
        if all(isinstance(i, datetime) for i in value):
            value = [item.timestamp() for item in value]
            isdt = True

    try:
        manual_type = None

        # Catch a list or tuple of Path as a special cases
        if isinstance(value, tuple) or isinstance(value, list):
            if isinstance(value[0], Path):
                if not all([isinstance(v, type(value[0])) for v in value]):
                    error = 'Path iterables are only supported in homogeneoeus packs'
                    logger.error(error)
                    raise RuntimeError(error)

                if isinstance(value, tuple): path_type = 'tuple'
                elif isinstance(value, list): path_type = 'list'
                else:
                    error = 'Unsupported Path iterable'
                    logger.error(error)
                    raise RuntimeError(error)

                _iterate_iter_data(
                    hdfobject, key, [str(v) for v in value], path_type, inner_id='path')
                return

        if isinstance(value, tuple):
            _iterate_iter_data(hdfobject, key, value, "tuple")
            return

        # Catching list of strings or list of np.str_ or mixed lists..
        if isinstance(value, list):
            # check if all float or all int, then its ok to pass on
            if all([isinstance(v, (int, float)) for v in value]):
                value = np.array(value)
                manual_type = 'list_arr'

            # check for mixed type if yes, dump to group
            # using the same as tuple
            elif not all([isinstance(v, type(value[0])) for v in value]):
                _iterate_iter_data(hdfobject, key, value, "list")
                return

            # check for nested list if yes, dump to group
            # using the same as tuple
            elif (all([isinstance(v, type(value[0])) for v in value])
                  and isinstance(value[0], list)):
                logger.debug('Packing list of lists')
                _iterate_iter_data(hdfobject, key, value, "list")
                return

            # List of (np) string
            elif all([isinstance(v, (str, np.str_)) for v in value]):
                value = np.array([str(v).encode() for v in value])
                logger.debug('List of strings will be binarized as array, adding type '
                             f'attribute for later decompression for {key}...')
                manual_type = 'list_str'

            # List of numpy arrays (changing shape possible)
            elif all([isinstance(v, np.ndarray) for v in value]):
                _iterate_iter_data(hdfobject, key, value, "list")
                return

        logger.debug(f'Trying to save {key} with type {type(value)}')
        if isinstance(value, np.ndarray):
            _dump_array(key, value, hdfobject, compress, type_id=manual_type)
            isdt = False

        elif isinstance(value, Path):
            ds = hdfobject.create_dataset(name=key, data=str(value))
            ds.attrs.create(
                name=TYPEID,
                data=str('path'))

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
                logger.error(50*'-')
                raise RuntimeError(f'Cant save {key}')


def save(hdf, data, compress=config.default_compression, packer=pack_dataset,
         *args, **kwargs):
    """
    Adds keys of given dict as groups and values as datasets to the given
    hdf-file (by string or object) or group object. Iterative dicts are
    supported.

    The dict can have the `attrs` key containing a dict of key, value pairs
    which are added as root level attributes to the hdf file. Those must be
    scalar, else exceptions will occur.

    `\*args` and `\*\*kwargs` will be passed to the `h5py.File` constructor.

    Parameters
    -----------
    hdf: `string`, `Path`
        Path to File
    data: `dict`
        The dictionary containing *only string or tuple* keys and
        data values or dicts as above again.
    packer: `callable`
        Callable gets `hdfobject, key, value` as input.
        `hdfobject` is considered to be either a h5py.File or a h5py.Group.
        `key` is the name of the dataset.
        `value` is the dataset to be packed and accepted by h5py.
        Defaults to `pack_dataset()`
    compress: `tuple`
        Try to compress arrays, use carefully. If on, gzip mode is used in
        every case. Defaults to `(False, 0)`. When `(True,...)` the second
        element specifies the level from `0-9`, see h5py doc.

    Returns
    --------
    hdf: `string`
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
                    raise TypeError('pandas Data must be stored in root group')
                else:
                    packer(hdfobject, key, value, compress)

    if isinstance(hdf, str):
        # Fixing windows issues with manually specified pathes
        if platform.system() == 'Windows':
            hdf = PureWindowsPath(hdf)

        hdf = Path(hdf)

    if not hdf.suffix == config.default_suffix:
        hdf = hdf.parent / (hdf.name + config.default_suffix)

    # Single dataframe
    if isinstance(data, (pd.DataFrame, pd.Series)):
        if compress[0]:
            store = pd.HDFStore(hdf, compress=compress[1], complib='zlib')
        else:
            store = pd.HDFStore(hdf, compress=None)

        store.put('pd_dataframe', data)
        store.close()

        return hdf

    if config.allow_overwrite:
        file_mode = 'w'
    else:
        file_mode = 'a'

    # Dataframe in dict. Pandas is stored in advance...stupid file lock in
    # pandas prevents otherwise.
    pandas_keys = list()

    for k, v in data.items():
        if isinstance(v, (pd.DataFrame, pd.Series)):
            if compress[0]:
                v.to_hdf(hdf, key=k, mode=file_mode, complevel=compress[1], complib='zlib')
            else:
                v.to_hdf(hdf, key=k, mode=file_mode, complib=None)
            pandas_keys.append(k)
            file_mode = 'r+'

    data = data.copy()  # this is needed so popping wont change the input data
    for k in pandas_keys:
        _ = data.pop(k)

    with h5py.File(hdf, file_mode, *args, **kwargs) as hdf_handle:
        # Handle manual attrs setup
        if 'attrs' in data:
            for k, v in data['attrs'].items():
                hdf_handle.attrs[k] = v
            _ = data.pop('attrs')

        # Finally save the data
        _recurse(data, hdf_handle)

    return hdf
