"""Package stup file for podbox
"""
import sys
import glob
import setuptools
from podbox import __version__, __uiname__

# ======================================
# Minimal Python version sanity check
# ======================================
V = sys.version_info
if (V[0] >= 3 and V[:2] < (3, 6)):
    ERR = "ERROR: podbox requires Python 3.6 and above."
    print(ERR, file=sys.stderr)
    sys.exit(1)

with open("README.md", "r") as fh:
    long_description = fh.read()

imageFiles = ['/'.join(g.split('/')[1:]) for g in glob.glob('podbox/images/*')]

setuptools.setup(
    name=__uiname__,
    version=__version__,
    author="M. Elfner, ITS, KIT",
    author_email="maximilian.elfner@kit.edu",
    description="The ITS podbox",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.scc.kit.edu/itsheat/podbox",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['podbox = podbox.main:runMainUI',
                            'davisstacker = podbox.main:runStacker',]
        },
    package_data={
        'podbox':imageFiles
        },
    install_requires=[
        'numpy',
        'matplotlib',
        'PyQt5',
        'qtpy',
        'seaborn',
        'qdarkstyle',
        'tifffile',
        'scikit-image',
        'h5py',
    ],
)
