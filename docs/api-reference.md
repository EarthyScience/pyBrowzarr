# API Reference

This page documents the public, user-facing API. Everything lives under the `browzarr`
package.

## Exports

```python
from browzarr import Browzarr, build_browzarr, update_browzarr, main
```

| Name | Kind | Purpose |
|------|------|---------|
| `Browzarr` | class | The user-facing configuration object. |
| `build_browzarr()` | function | Rebuild the bundled frontend from the upstream source. |
| `update_browzarr()` | function | Update the bundled frontend from the prebuilt `python-dist` branch. |
| `main()` | function | Command-line entry point (`browzarr` launcher). |

---

## `Browzarr`

A `Browzarr` object holds the configuration for a single visualization. Set attributes
or pass them as keyword arguments, chain a plot type, then call `.plot()`.

### Constructor

```python
Browzarr(
    dataset,                       # str, required
    variable,                      # str, required
    x_slice=(0, None),             # tuple[int, int | None]
    y_slice=(0, None),             # tuple[int, int | None]
    z_slice=(0, None),             # tuple[int, int | None]
    extra_params={},               # dict[str, Any]
)
```

All fields are also accessible as attributes after construction.

`extra_params` is a catch-all dictionary that gets merged into the final plot state.
Use it to pass any option not explicitly modeled — keys are camel-cased automatically.

```python
bz = Browzarr(dataset="gs://store", variable="temp")
bz.extra_params["myCustomOption"] = True
```

There is no keyword validation — any unexpected keyword on a plot method is silently
serialized rather than raising. Be careful with typos.

### Plot methods

Each of these records the plot configuration and returns `self`, so calls can be chained
or stored.

```python
def volume(**kwargs) -> Browzarr   # 3D volume render
def points(**kwargs) -> Browzarr   # point cloud
def flat(**kwargs)   -> Browzarr   # flat surface (can be displaced)
def sphere(**kwargs) -> Browzarr   # globe/sphere
```

Only the *last* plot method called takes effect. See the
[common options](plot-types/common-options.md) and plot-type-specific pages for the
accepted keyword arguments.

```python
bz = Browzarr(dataset="gs://store", variable="temp")
bz.volume(transparency=0.5).points(point_size=3)   # points() wins — last call
```

### Export method

```python
def export(open_browser: bool = True, **kwargs) -> Browzarr
```

Configures an export (with optional animation) and immediately launches the plot by
calling `.plot()`. See [Export & Animation](export.md) for the accepted keyword arguments.

```python
Browzarr(dataset="gs://store", variable="temp").volume().export(
    main_title="My Map",
    animate=True,
    frames=120,
    frame_rate=30,
)
```

### `plot()`

```python
def plot(
    width=720,
    height=720,
    give_url: bool = False,
    external_browser: bool = False,
    wait: float = 0.3,
) -> str | None
```

Launches (or reuses) the local Browzarr server and opens the view configured on this
object.

| Argument | Default | Description |
|----------|---------|-------------|
| `width` | `720` | Iframe width in Jupyter/Colab. |
| `height` | `720` | Iframe height in Jupyter/Colab. |
| `give_url` | `False` | When `True`, returns the hosted URL string instead of opening anything. |
| `external_browser` | `False` | Force opening in an external browser, bypassing environment detection. |
| `wait` | `0.3` | Seconds to wait before opening, so the server is ready. |

Return value: the URL string when `give_url=True`, otherwise `None`.

```python
bz.plot()
bz.plot(give_url=True)          # -> "https://browzarr.io/latest/?data=..."
bz.plot(width=900, height=600)  # larger iframe in notebooks
bz.plot(external_browser=True)  # always open in the OS browser
```

Where the view opens is auto-detected. See [Environments](environment.md).

---

## Session lifecycle

### `BrowzarrSession.shutdown()`

A single local server is shared across all `Browzarr` instances in the same process, so
repeated `.plot()` calls reuse it instead of spawning duplicates.

To stop the shared server and free its port:

```python
from browzarr.api import BrowzarrSession

BrowzarrSession.shutdown()
```

---

## Module functions

### `build_browzarr()`

Rebuilds the bundled frontend distribution from the upstream source.

```python
from browzarr import build_browzarr

build_browzarr()
```

Requires [pnpm](https://pnpm.io/installation) on your `PATH`.

1. Downloads the latest source from the `main` branch of the upstream repo.
2. Runs `pnpm install` and `pnpm run build`.
3. Replaces `web/dist` with the freshly built output.

The build output is written in the package data directory, which requires write access.

### `update_browzarr()`

Updates the bundled frontend from the upstream prebuilt `python-dist` branch — faster
than a full source rebuild.

```python
from browzarr import update_browzarr

update_browzarr()
```

Downloads the tarball, extracts it, and replaces `web/dist`.

### `main()`

The command-line entry point registered as the `browzarr` console script. Run it from a
terminal:

```bash
browzarr
```
