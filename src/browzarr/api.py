import threading
import time
import urllib.parse
import json
import webbrowser
from dataclasses import dataclass, field
from typing import Any, Unpack
from .server_utils import find_free_port, get_dist_dir, make_handler, DEFAULT_START_PORT
from .method_types import Volume, Points, Flat, Sphere, Export
import socketserver
import os
import subprocess
import importlib.resources
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path
import re

def to_spec(param_dict, plot_type: str = None) -> dict:
    """Serialize to the JSON blob the JS frontend expects."""
    param_dict = {"plot_type": plot_type, **param_dict} if plot_type is not None else param_dict
    return {snake_to_camel(k): v for k, v in param_dict.items() if v is not None}


def snake_to_camel(s: str) -> str:
    return re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), s)

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

def _in_colab() -> bool:
    "True if running in Colab"
    try:    
        import google.colab
        return True
    except:
        return False

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
    chain operators. When satisfied, call .plot() to launch a preconfigured Browzarr view.
    """
    dataset: str 
    variable: str
    variable2: str | None = None
    share_scale: bool = False
    x_slice: tuple[int, int | None] = (0, None)
    y_slice: tuple[int, int | None] = (0, None)
    z_slice: tuple[int, int | None] = (0, None)
    extra_params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.export_plot = False
        self.reproject = False
        self._plot_state = None
        self._export_state = None
        self.init_store = self.dataset

    # ---- Plot Functions ---- #
    def volume(self, **kwargs: Unpack[Volume]) -> "Browzarr":
        self._plot_state = to_spec({**kwargs}, 'volume')
        return self

    def points(self, **kwargs: Unpack[Points]) -> "Browzarr":
        self._plot_state = to_spec({**kwargs}, 'point-cloud')
        return self

    def flat(self, **kwargs: Unpack[Flat]) -> "Browzarr":
        self._plot_state = to_spec({**kwargs}, 'flat')
        return self

    def sphere(self, **kwargs: Unpack[Sphere]) -> "Browzarr":
        self._plot_state = to_spec({**kwargs}, 'sphere')
        return self

    # ---- Export Functions ---- #
    def export(self, give_url: bool = False, open_browser:bool = True, **kwargs: Unpack[Export]) -> "Browzarr":
        self._export_state = to_spec({**kwargs})
        self.export_plot = True
        return self.plot(give_url=give_url, external_browser=open_browser)
    # ---- Build States ---- #
    def _build_global_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        for key in ["init_store", "variable", "variable2"]:
            value = getattr(self, key)
            if value is not None:
                state[snake_to_camel(key)] = value
        if getattr(self, "variable2", None) is not None:
            state["bivariate"] = True
            state["shareScale"] = self.share_scale
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
        export_obj = self._export_state if self._export_state is not None else {}
        for key, value in export_obj.items():
            if key == "keyframes" and value is not None:
                ## Write to JSON file and pass path to frontend
                keyframe_path = "keyframes.json"
                with open(keyframe_path, "w") as f:
                    json.dump(value, f)
                ## pass path as absolute path to frontend
                state["keyframesPath"] = os.path.abspath(keyframe_path)
                continue
            if key == "keyframesPath" and value is not None:
                state[key] = os.path.abspath(value)
                continue
            if value is not None:
                ## Key already camelCase from to_spec()
                state[key] = value
        return state
    
    # ---- Query from States ---- #
    def _build_query(self) -> str:
        es = self._build_export_state()
        ## Copy so repeated .plot() calls don't mutate the config
        plot_spec = dict(self._plot_state) if self._plot_state is not None else {}

        ## Reproject if native_CRS and dest_CRS provided
        if plot_spec.get("nativeCRS") is not None and plot_spec.get("destCRS") is not None:
            self.reproject = True

        camera_pos = plot_spec.pop("cameraPosition", None)
        kfp = es.pop("keyframesPath", None)

        ## Flat query: every param at the top level, no nesting
        query: dict[str, Any] = {}
        query.update(self._build_global_state())
        query.update(self._build_zarr_state())
        query.update(plot_spec)
        query.update(self.extra_params)
        query.update(es)
        if camera_pos is not None:
            query["cameraPosition"] = {'x':camera_pos[0], 'y':camera_pos[1], 'z':camera_pos[2]}
        if kfp is not None:
            query["keyFramesPath"] = kfp
        query["export"] = self.export_plot
        query["reproject"] = self.reproject

        ## Scalars pass through; bools/lists/tuples/dicts are JSON-encoded
        return urllib.parse.urlencode(
            {k: json.dumps(v) if isinstance(v, (bool, list, tuple, dict)) else v
             for k, v in query.items() if v is not None}
        )


    def plot(self, width=720, height=720, give_url: bool = False, external_browser: bool = False, wait: float = 0.3) -> str | None:
        """
        Launch (or reuse) the local Browzarr server and open the
        browser pointed at this config's URL params.

        Returns the full URL.
        """
        port = BrowzarrSession._ensure_server()
        query = self._build_query()
        url = f"http://localhost:{port}/"
        if query:
            url += f"?{query}"
        if give_url:
            return f"https://browzarr.io/latest/?{query}"
        else:
            time.sleep(wait)  # tiny buffer so server is accepting connections
            if external_browser:
                webbrowser.open(url)
            elif _in_jupyter():
                from IPython.display import IFrame, display
                display(IFrame(src=url, width=width, height=height))
            elif _in_vscode() and _open_vscode_simple_browser(url):
                pass  # opened in VS Code's built-in tab
            elif _in_colab():
                from google.colab import output
                output.serve_kernel_port_as_iframe(port, f"/?{query}", width=width, height=height)
            else:
                webbrowser.open(url)
                print("Failed to detect environment. Defaulting to external browser.")


NPM_PACKAGE = "browzarr"
NPM_REGISTRY_URL = f"https://registry.npmjs.org/{NPM_PACKAGE}"
NPM_VERSION_MARKER = ".npm-version"

def _dist_path() -> Path:
    dist_dir = importlib.resources.files("browzarr") / "web" / "dist"
    return Path(str(dist_dir))

def _installed_npm_version() -> str | None:
    marker = _dist_path() / NPM_VERSION_MARKER
    if marker.exists():
        return marker.read_text(encoding="utf-8").strip() or None
    return None

def _npm_versions() -> list[str]:
    with urllib.request.urlopen(NPM_REGISTRY_URL, timeout=30) as resp:
        data = json.load(resp)
    return list(data["versions"].keys())

def _latest_npm_version() -> str:
    with urllib.request.urlopen(NPM_REGISTRY_URL, timeout=30) as resp:
        data = json.load(resp)
    return data["dist-tags"]["latest"]

def _version_key(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in re.findall(r"\d+", v)) or (0,)

def _version_matches(requested: str, candidate: str) -> bool:
    ## PEP 440 style: "0.8" matches "0.8.0" (zero-padded equality)
    req, cand = _version_key(requested), _version_key(candidate)
    size = max(len(req), len(cand))
    return req + (0,) * (size - len(req)) == cand + (0,) * (size - len(cand))

def _resolve_npm_version(requested: str) -> str:
    """Resolve a requested version to a real npm release.

    Exact match (zero-padded, so "0.8" resolves to "0.8.0") wins; otherwise
    the nearest release at or below the request is used, falling back to the
    oldest release if the request predates everything.
    """
    available = _npm_versions()
    for v in available:
        if _version_matches(requested, v):
            return v
    req = _version_key(requested)
    lower = [v for v in available if _version_key(v) <= req]
    if lower:
        pick = max(lower, key=_version_key)
    else:
        pick = min(available, key=_version_key)
    print(f"browzarr {requested} not found on npm, using nearest version {pick}")
    return pick

def _fetch_npm_dist(version: str) -> None:
    dist_path = _dist_path()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tarball = tmp_path / "browzarr.tgz"
        urllib.request.urlretrieve(
            f"{NPM_REGISTRY_URL}/-/{NPM_PACKAGE}-{version}.tgz",
            tarball,
        )
        print("Extracting built site files...")
        with tarfile.open(tarball) as tar:
            members = [m for m in tar.getmembers() if m.name.startswith("package/out/")]
            try:
                tar.extractall(tmp_path, members=members, filter="data")
            except TypeError:
                tar.extractall(tmp_path, members=members)

        built_out = tmp_path / "package" / "out"

        if dist_path.exists():
            shutil.rmtree(dist_path)
        dist_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copytree(built_out, dist_path)
        (dist_path / NPM_VERSION_MARKER).write_text(version, encoding="utf-8")


def use_latest(from_github=False) -> str:
    """Fetch the latest published browzarr site build from npm or github into web/dist."""
    if from_github:
        _fetch_github()
        return "latest github build"
    version = _latest_npm_version()
    installed_version = _installed_npm_version()
    if version == installed_version:
        print("No updates from NPM")
        return version
    print(f"Fetching browzarr {version} from npm...")
    _fetch_npm_dist(version)
    print(f"Browzarr distribution updated to {version}")
    return version

def use_version(version: str = "latest") -> str:
    """
    Fetch a specific published browzarr site build from npm into web/dist.

    Accepts any released version string (e.g. "0.8.0" or "0.8"). If the
    requested version doesn't exist, the nearest release at or below it is
    used, mirroring pip's version resolution. "latest" grabs the newest
    release. Returns the version actually installed.
    """
    if version == "latest":
        return use_latest()
    resolved = _resolve_npm_version(version)
    print(f"Fetching browzarr {resolved} from npm...")
    _fetch_npm_dist(resolved)
    print(f"Browzarr distribution updated to {resolved}")
    return resolved

def _fetch_github():
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
    (dist_path / NPM_VERSION_MARKER).write_text("latest github", encoding="utf-8")
    print("Succesfully updated Browzarr distribution")
