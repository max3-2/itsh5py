# Installation

itsh5py is [available on PyPI][pypi] and can be readily installed via
```none
pip install itsh5py
```
Run `pip uninstall itsh5py` in order to remove the package from your system.

To work, this requires some additional packages. Obviously, `h5py` is used
for data storage. `numpy` is used for array handling. Dataframes are
also supported using `pandas`. Finally, for serialization of difficult
data types, *yaml* is used via `pyyaml`.

All the source packages above are available on PyPI for all common OS.

## Limitations and warning
Some limitation still exist:
- While most of the core data types should be implemented, there is arbitrary
complexity especially with nested iterables. Most likely there are still
some cases and types which are not supported and may fail with different levels
of grace. Since this package will most likely be used for data storage please
always consider checking if *your* type is saved **and loaded** correctly. If
in doubt, always open the file with `h5py.File()` and check. Feel free to
report missing or buggy data types and they will be implemented if possible.
- Numpy object arrays are not supported.
- Keys of the dictionary which will be saved should only be strings to avoid.
Any other typer are not tested and most likely will fail.
- Lazy slicing of arrays is not supported (yet).
- Long tuples and mixed type lists will be saved element-wise and thus be slow.
This is recognizable starting at approx. 100 elements.

[pypi]:  https://google.de
