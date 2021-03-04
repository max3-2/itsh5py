# ITS h5 support

This is a small implementation of recursive dict support for python to write
and read h5 files with many different types. The resulting files work in
hdfview and panoply.

Lists and tuples are unrolled so they do not have to be serialized in most cases.
Lazy support can be enabled allowing to work fast with large files.

To contribute, please use the Gitlab server and the issue and changes tracking
system supplied there!
