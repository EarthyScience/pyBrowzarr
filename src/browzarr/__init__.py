"""
Browzarr
================

A small Python package that serves the pre-built Browzarr static frontend
(WebGPU/WebGL Earth science visualization) from a local HTTP server and
opens it in the user's browser.

The actual frontend build lives in ``web/dist`` and is generated separately
via the frontend's build tooling. After install, run update_browzarr to stay up 
to dat with the browzarr website. 
"""

from .server_utils import main
from .api import Browzarr, update_browzarr, build_browzarr

__all__ = ["main", "__version__", "Browzarr", "update_browzarr", "build_browzarr"]
