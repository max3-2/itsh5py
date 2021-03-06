# itsh5py
*Python datatype support for hdf files*

While there are many ways to store different data types, many of them have
their drawbacks. Sometimes it can be practical to store arrays with
additional (pythonic) data in a single file. While *hdf attributes* can
support some types, many exception exists especially with pyhtonic types.

This is a small implementation of recursive dict support for python to write
and read *hdf* files with many different pythonic data types. Almost all types
implemented in default python and *numpy* should be supported, even in nested
structures. The resulting files work in hdfview and panoply with some small
drawbacks.

Data types which are unknown will be serialized if possible using *yaml*.
Lists and tuples are unrolled so they do not have to be serialized in most cases.
Lazy support can be enabled allowing to work fast with large files, only loading
references of large arrays and fetching the data on demand as supported by
*h5py*. This works for *numpy* arrays only but mixed results are possible, e.g.
having fully loaded pythonic types and referenced *numpy* arrays in a single
loaded file.

Since this module is most likely used for data storage, please be warned that
*tests are still WiP* and there is a good chance that you will encounter some
types that either **won't be saved** or possibly **break your file**. No
warranty is given.

The original idea was taken from [SiggiGue](https://github.com/SiggiGue/hdfdict)
thus there are some obvious similarities. This package extends the
functionality to handle most of the pythonic data types and adds functions
for convenient handling of the different data structures.


Find the [Full documentation here](https://itsh5py.readthedocs.io/en/latest)
