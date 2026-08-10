"""
browzarr_viewer
================

A small Python package that serves the pre-built Browzarr static frontend
(WebGPU/WebGL Earth science visualization) from a local HTTP server and
opens it in the user's browser.

The actual frontend build lives in ``web/dist`` and is generated separately
via the frontend's build tooling (see ``build_and_copy.sh`` in the repo
root). This package only knows how to serve those static files.
"""

# from importlib.metadata import PackageNotFoundError, version

# try:
#     __version__ = version("browzarr-viewer")
# except PackageNotFoundError:
#     # Package is not installed (e.g. running from source without `pip install -e .`)
#     __version__ = "0.0.0.dev0"

from .server_utils import main
from .api import Browzarr

__all__ = ["main", "__version__", "Browzarr"]
