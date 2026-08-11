import threading
import time
import urllib.parse
import json
import webbrowser
from dataclasses import dataclass, field, asdict
from .export import Export
from typing import Any
import xarray as xr
from .server_utils import find_free_port, get_dist_dir, make_handler, DEFAULT_START_PORT
from .plot_types import Volume, Points, Flat, Sphere, snake_to_camel
import socketserver
import os
import subprocess
import numpy as np
import importlib.resources
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing_extensions import Unpack

def _in_jupyter() -> bool:
    """True if running inside a Jupyter/IPython kernel (notebook or lab)."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
        if shell is None:
            return False
        return shell.__class__.__name__ == "ZMQInteractiveShell"
    except ImportError:
        return False

def _in_vscode() -> bool:
    """True if running inside a VS Code integrated terminal/kernel."""
    return os.environ.get("TERM_PROGRAM") == "vscode" or "VSCODE_PID" in os.environ

def _open_vscode_simple_browser(url: str) -> bool:
    """
    Ask VS Code to open its built-in Simple Browser tab via the
    `code` CLI's URI handler. Returns True on apparent success.
    """
    try:
        subprocess.run(
            ["code", "--open-url", f"vscode://ms-vscode.simple-browser?url={url}"],
            check=True,
            capture_output=True,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

class BrowzarrSession:
    """
    Holds a single running local server so repeated .plot() calls
    from the same session reuse it instead of spawning duplicates.
    """

    _port: int | None = None
    _httpd: socketserver.TCPServer | None = None
    _thread: threading.Thread | None = None

    # Classmethod shares values across all class instances. Only one server running
    @classmethod
    def _ensure_server(cls) -> int:
        if cls._httpd is not None:
            return cls._port  # already running

        dist_path = get_dist_dir()
        port = find_free_port()
        handler = make_handler(str(dist_path))
        socketserver.TCPServer.allow_reuse_address = True

        httpd = socketserver.TCPServer(("localhost", port), handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()

        cls._httpd = httpd
        cls._port = port
        cls._thread = thread
        return port

    @classmethod
    def shutdown(cls) -> None:
        if cls._httpd is not None:
            cls._httpd.shutdown()
            cls._httpd = None
            cls._port = None

def isNC(path: str):
    return any(nc in path for nc in (".nc", ".nc4", ".netcdf"))

# dataclass generates all __init__ and self values boilerplate. Just list all potential fields. 
@dataclass
class Browzarr:
    """
    User-facing config object. Set attributes (or use kwargs), then
    call .plot() to launch a preconfigured Browzarr view.
    """
    dataset: str | xr.Dataset | xr.DataArray
    variable: str | None = None
    x_slice: tuple[int, int | None] = (0, None)
    y_slice: tuple[int, int | None] = (0, None)
    z_slice: tuple[int, int | None] = (0, None)
    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.export_plot = False
        self.reproject = False
        self._export_state = None
        if not isinstance(self.dataset, str):
            self._parse_xr_object()
            return
        if self.variable == None:
            raise ValueError("Variable must be included when using a dataset path")
        
        self.init_store = self.dataset
    def _parse_xr_object(self) -> None:
        store = self.dataset
        def parse_da(da: xr.DataArray) -> None:
            # Check if it has been sliced. If so, indexes will be erroneous
            original_shape = tuple(da.encoding.get("original_shape"))
            this_shape = da.shape
            if len(this_shape) > 3:
                raise ValueError("Too many dimensions. Reduce to 3")
            if any([val not in original_shape for val in this_shape]):
                raise LookupError(
                    """
                    Cannot infer slice range from pre-sliced DataArray. 
                    Pass unsliced DataArray and use .sel() method 
                    e.g., Browzarr(da).sel()/.isel()
                    """
                )
            self.axis_mapping = [original_shape.index(x) for x in this_shape]
            self.variable = da.name
            self.init_store = da.encoding.get("source")
        
        #Handle DataArray
        if isinstance(store, xr.DataArray):
            da = store
            parse_da(da)
            return
        #Handle DataSet
        if self.variable == None:
            raise ValueError("Variable must be included when using a dataset")
        var = self.variable
        if var not in store.variables:
            raise LookupError("Variable not found in Dataset")
        da = store[var]
        parse_da(da)
        self.dataset = da
        return

    # ---- Plot Functions ---- #
    def volume(self, **kwargs: Volume) -> "Browzarr":
        self._plot_state = Volume(**kwargs)
        return self

    def points(self, **kwargs: Points) -> "Browzarr":
        self._plot_state = Points(**kwargs)
        return self

    def flat(self, **kwargs: Flat) -> "Browzarr":
        self._plot_state = Flat(**kwargs)
        return self

    def sphere(self, **kwargs: Sphere) -> "Browzarr":
        self._plot_state = Sphere(**kwargs)
        return self

    # ---- Export Functions ---- #
    def export(self, **kwargs: Any) -> "Browzarr":
        self._export_state = Export(**kwargs)
        self.export_plot = True
        return self.plot(open_browser = False)
    # ---- Build States ---- #
    def _build_global_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}

        for key in ["init_store", "variable"]:
            value = getattr(self, key)
            if value is not None:
                state[snake_to_camel(key)] = value

        return state
 
    def _build_zarr_state(self) -> dict[str, Any]:
        self.useNC = isNC(self.init_store)
        state: dict[str, Any] = {}
        for key in ["useNC"]:
            value = getattr(self, key)
            if value is not None:
                state[snake_to_camel(key)] = value
        state["ndSlices"] = [self.z_slice, self.y_slice, self.x_slice]
        return state

    def _build_export_state(self) -> dict[str, Any]:
        if not self.export_plot:
            return {}
        state: dict[str, Any] = {}
        export_obj = self._export_state.to_spec() if self._export_state is not None else {}
        for key, value in export_obj.items():
            if key == "keyframes" and value is not None:
                ## Write to JSON file and pass path to frontend
                keyframe_path = "keyframes.json"
                with open(keyframe_path, "w") as f:
                    json.dump(value, f)
                ## pass path as absolute path to frontend
                self._export_state.keyframes_path = os.path.abspath(keyframe_path)
                continue
            if key == 'keyframesPath' and value is not None:
                self._export_state.keyframes_path = os.path.abspath(value)
                continue
            if value is not None:
                ## Key already camelCase from to_spec()
                state[key] = value
        return state
    
    # ---- Query from States ---- #
    def _build_query(self) -> str:
        es = self._build_export_state()
        plot_spec = self._plot_state.to_spec() if self._plot_state is not None else {}
        ## Exclude parameters if the 
        full_obj = {
            "globalState": self._build_global_state(),
            "plotState": plot_spec,
            "zarrState": self._build_zarr_state(),
            **({"exportState": es} if len(es) > 0 else {}),
        }
        ## Reproject if dst_CRS and native_CRS provided
        if (self._plot_state is not None
            and getattr(self._plot_state, "native_CRS", None) is not None
            and getattr(self._plot_state, "dest_CRS", None) is not None):
            self.reproject = True

        full_obj["plotState"].update(self.extra_params)
        
        kfp = self._export_state.keyframes_path if self._export_state is not None else None
        return urllib.parse.urlencode({"data": json.dumps(full_obj), 
                                       "store":self.init_store, 
                                       "export": json.dumps(self.export_plot), 
                                       "reproject": json.dumps(self.reproject),
                                       **({"keyFramesPath": kfp} if kfp is not None else {}),
                                       })

    # ---- Dataslicers ----#
    def _resolve_slices(self, indexers: dict, positional: bool) -> list[tuple]:
        da = self.dataset
        if not isinstance(da, xr.DataArray):
            raise ValueError("Incorrect dataset type passed into class")

        slices_by_dim: dict[int, tuple] = {}
        for dim, key in indexers.items():
            if dim not in da.dims:
                raise ValueError(f"{dim} is not a valid dimension")

            axis = da.get_axis_num(dim)

            if positional:
                start, stop = key.start, key.stop
            else:
                index = da.get_index(dim)
                indexer = index.slice_indexer(key.start, key.stop)
                start, stop = indexer.start, indexer.stop
                start = start.item() if isinstance(start, np.integer) else start
                stop = stop.item() if isinstance(stop, np.integer) else stop

            slices_by_dim[axis] = (start, stop)

        return self._align_slices_to_shape(slices_by_dim)

    def sel(self, **indexers) -> "Browzarr":
        z, y, x = self._resolve_slices(indexers, positional=False)
        self.z_slice, self.y_slice, self.x_slice = z, y, x
        return self

    def isel(self, **indexers) -> "Browzarr":
        z, y, x = self._resolve_slices(indexers, positional=True)
        self.z_slice, self.y_slice, self.x_slice = z, y, x
        return self


    def plot(self, open_browser: bool = True, wait: float = 0.3) -> str:
        """
        Launch (or reuse) the local Browzarr server and open the
        browser pointed at this config's URL params.

        Returns the full URL (handy for notebooks / headless use).
        """
        port = BrowzarrSession._ensure_server()
        query = self._build_query()
        url = f"http://localhost:{port}/"
        if query:
            url += f"?{query}"

        if open_browser:
            time.sleep(wait)  # tiny buffer so server is accepting connections

            if _in_jupyter():
                from IPython.display import IFrame, display
                display(IFrame(src=url, width="100%", height=600))
            elif _in_vscode() and _open_vscode_simple_browser(url):
                pass  # opened in VS Code's built-in tab
            else:
                webbrowser.open(url)

        return url


def _check_pnpm():
    try:
        subprocess.run(["pnpm", "--version"], check=True, shell=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    
def build_browzarr():
    if not _check_pnpm():
        print('''
        pnpm not installed. Install it then run again
        https://pnpm.io/installation
        ''')
        return
    base_path = ""
    dist_dir = importlib.resources.files("browzarr") / "web" / "dist"
    dist_path = Path(str(dist_dir))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tarball = tmp_path / "source.tar.gz"

        print("Downloading source from GitHub...")
        urllib.request.urlretrieve(
            "https://codeload.github.com/EarthyScience/Browzarr/tar.gz/refs/heads/main",
            tarball,
        )

        print("Extracting...")
        with tarfile.open(tarball) as tar:
            tar.extractall(tmp_path)

        extracted_root = next(tmp_path.glob("Browzarr-*"))
        print("Installing dependencies with pnpm...")
        subprocess.run(["pnpm", "install"], cwd=extracted_root, check=True, shell=True)

        subprocess.run(
            ["pnpm", "run", "build"],
            cwd=extracted_root,
            check=True,
            env={**os.environ, "BASE_PATH": base_path},
            shell=True
        )

        built_out = extracted_root / "out"

        if dist_path.exists():
            shutil.rmtree(dist_path)

        dist_path.parent.mkdir(parents=True, exist_ok=True)

        print("Copying built distribution...")
        shutil.copytree(built_out, dist_path)

    print("Browzarr distribution updated successfully!")

def update_browzarr():
    dist_dir = importlib.resources.files("browzarr") / "web" / "dist"
    dist_path = Path(str(dist_dir))

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tarball = tmp_path / "python-dist.tar.gz"
        print("Downloading from github...")
        urllib.request.urlretrieve(
            "https://codeload.github.com/EarthyScience/Browzarr/tar.gz/refs/heads/python-dist",
            tarball,
        )
        print("Extracting...")
        with tarfile.open(tarball) as tar:
            tar.extractall(tmp_path)

        extracted_root = next(tmp_path.glob("Browzarr-python-dist*"))

        if dist_path.exists():
            shutil.rmtree(dist_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copytree(extracted_root, dist_path)
    print("Succesfully updated Browzarr distribution")
    