"""Configuration file for the documentation.
"""
import sys                             # system specifics
from pathlib import Path               # file-system path
from unittest.mock import MagicMock    # mock imports

extensions = [
    'myst_parser',                     # Accept Markdown as input.
    'sphinx.ext.autodoc',              # Get documentation from doc-strings.
    'sphinx.ext.autosummary',          # Create summaries automatically.
    'sphinx.ext.viewcode',             # Add links to highlighted source code.
    'sphinx.ext.mathjax',              # Render math via JavaScript.
    'sphinx.ext.napoleon',             # numpy docstrings
]

# Add the project folder to the module search path.
main = Path(__file__).absolute().parent.parent
sys.path.insert(0, str(main))

# Mock external dependencies so they are not required at build time.
autodoc_mock_imports = ['numpy', 'pandas', 'h5py', 'pyyaml']
for package in autodoc_mock_imports:
    sys.modules[package] = MagicMock()

# Import package to make meta data available.
import itsh5py as meta

########################################
# Configuration                        #
########################################

# Meta information
project = meta.__title__
version = meta.__version__
release = meta.__version__
date = meta.__date__
author = meta.__author__
copyright = meta.__copyright__
license = meta.__license__

# Logo
# html_logo = 'images/TODO.png'  # documentation logo
# html_favicon = 'images/TODO.png'  # browser icon

# Source parsing
master_doc = 'index'                   # start page
nitpicky = False                      # Warn about missing references?

# Code documentation
autodoc_default_options = {
    'members':       True,             # Include module/class members.
    'member-order': 'bysource',        # Order members as in source file.
}
autosummary_generate = True           # Stub files are created by hand.
add_module_names = True               # Don't prefix members with module name.

# Rendering options
myst_heading_anchors = 2               # Generate link anchors for sections.
html_copy_source = False           # Copy documentation source files?
html_show_copyright = True           # Show copyright notice in footer?
html_show_sphinx = False           # Show Sphinx blurb in footer?

# Rendering style
html_theme = 'furo'           # custom theme with light and dark mode
pygments_style = 'friendly'       # syntax highlight style in light mode
pygments_dark_style = 'stata-dark'     # syntax highlight style in dark mode
# templates_path = ['templates']    # style template overrides
html_static_path = ['style']        # folders to include in output
html_css_files = ['custom.css']   # extra style files to apply
