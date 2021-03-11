"""Main init file of itsh5py
"""
name = 'itsh5py'
__version__ = '1.0'

# This should only be enabled in rare debug cases!
# import logging
# # Initialize logger
# logger = logging.getLogger(__package__)
# logger.setLevel(logging.DEBUG)
# _formatter = logging.Formatter(
#     '%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(filename)s:%(lineno)d] %(message)s',
#     datefmt='%Y-%m-%d_%H:%M:%S')
#
# _stream_handler = logging.StreamHandler()
# _stream_handler.setFormatter(_formatter)
# _stream_handler.setLevel(logging.INFO)
# logger.addHandler(_stream_handler)

# This protects the setup routine
try:
    from .hdfSupport import *
    from .queueHandler import max_files, open_filenames
except ModuleNotFoundError:
    ...
