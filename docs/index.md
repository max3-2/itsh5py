# itsh5py

While there are many ways to store different data types, many of them have
their drawbacks. [hdf][hdfl] is a common way to store large arrays.
Sometimes it can be practical to store arrays with additional (pythonic) data
in a single file. While *hdf attributes* can support some types, many exception
exists especially with python types.

This is a small implementation of recursive dict support for python to write
and read *hdf-files* with many different pythonic data types. Almost all types
implemented in default python and *numpy* should be supported, even in nested
structures. The resulting files work in *hdfview* and *panoply* with some small
drawbacks.

A major convenience is the ability to store iterables like lists and tuples,
even in nested form. Mixed types are also supported.


[hdfl]: https://www.hdfgroup.org


```{toctree}
:hidden:

installation
tutorial
usage
releases
```
