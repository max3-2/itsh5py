"""Package stup file for podbox
"""
import sys
import glob
import setuptools
from itsh5py import __version__

# ======================================
# Minimal Python version sanity check
# ======================================
V = sys.version_info
if (V[0] >= 3 and V[:2] < (3, 6)):
    ERR = "ERROR: itsh5py requires Python 3.6 and above."
    print(ERR, file=sys.stderr)
    sys.exit(1)

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name='itsh5py',
    version=__version__,
    author="M. Elfner, ITS, KIT",
    author_email="maximilian.elfner@kit.edu",
    description="ITS h5 support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.scc.kit.edu/its-all/academics/itsh5py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'numpy',
        'pyyaml',
        'h5py',
    ],
)
