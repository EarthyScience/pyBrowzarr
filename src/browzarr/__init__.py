"""
Browzarr
================

A small Python package that serves the pre-built Browzarr static frontend
(WebGPU/WebGL Earth science visualization) from a local HTTP server and
opens it in the user's browser.

The actual frontend build lives in ``web/dist`` and is generated separately
via the frontend's build tooling. After install, run use_latest to stay up 
to date with the Browzarr website. 
"""

from .server_utils import main
from .api import Browzarr, use_latest, use_version

__all__ = ["main", "__version__", "Browzarr", "use_latest", "use_version"]

