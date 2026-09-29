# pyBrowzarr Documentation

pyBrowzarr is a Python package that serves the pre-built [Browzarr](https://browzarr.io)
WebGPU/WebGL Earth-science visualization frontend from a local HTTP server and opens it
in your browser (or notebook). It gives you a Pythonic, chainable API to configure a
plot and launch it with a single call.

## What you can do

- Plot 3D or flat visualizations of Zarr/NetCDF datasets.
- Choose among four plot types: **volume**, **points**, **flat**, and **sphere**.
- Tune shared and plot-type-specific options (colormaps, extents, transparency, and more).
- Export the result or script an animation with walkthrough keyframes.
- Run from a terminal, Jupyter/JupyterLab, VS Code, or Google Colab automatically.

## Installation

```bash
pip install browzarr
```

The `browzarr` command-line launcher is also installed:

```bash
browzarr
```

A pre-built frontend comes bundled with the package. See
[Build & Update](build-and-update.md) to rebuild it from source or update it.

## First plot

```python
from browzarr import Browzarr

Browzarr(dataset="gs://some-zarr-store", variable="temperature").volume().plot()
```

That's it — a configured Browzarr view opens in your default browser.

## Documentation map

| Guide | Covers |
|-------|--------|
| [Quickstart](quickstart.md) | Install, `Browzarr` basics, slicing, launching a plot |
| [API Reference](api-reference.md) | Full reference for `Browzarr`, its methods, and module functions |
| [Plot Types](plot-types/common-options.md) | Options shared by every plot type |
| [Plot Types · Volume](plot-types/volume.md) | Volume plot options and examples |
| [Plot Types · Points](plot-types/points.md) | Points/point-cloud plot options and examples |
| [Plot Types · Flat & Sphere](plot-types/flat-sphere.md) | Flat and sphere plot options and examples |
| [Export & Animation](export.md) | The `export()` method, export options, keyframes, and animation |
| [Environments](environment.md) | Behavior in terminal, Jupyter, VS Code, and Colab |
| [Build & Update](build-and-update.md) | `build_browzarr()` and `update_browzarr()` |
