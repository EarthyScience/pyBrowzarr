# Quickstart

This guide gets you from install to your first plot.

## 1. Install

```bash
pip install browzarr
```

## 2. Create a Browzarr session

A `Browzarr` object describes *what* to visualize. You give it a dataset and a variable,
then optionally constrain which data to load.

```python
from browzarr import Browzarr

bz = Browzarr(dataset="gs://some-zarr-store", variable="temperature")
```

### Constructor fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dataset` | `str` | *(required)* | Zarr store path or NetCDF `.nc` / `.nc4` / `.netcdf` file. |
| `variable` | `str` | *(required)* | The variable name to visualize. |
| `x_slice` | `tuple[int, int \| None]` | `(0, None)` | X-axis slice (start, stop). `None` means "to the end". |
| `y_slice` | `tuple[int, int \| None]` | `(0, None)` | Y-axis slice. |
| `z_slice` | `tuple[int, int \| None]` | `(0, None)` | Z-axis slice. |
| `extra_params` | `dict` | `{}` | Additional parameters merged into the plot state (advanced, see [API Reference](api-reference.md)). |

NetCDF paths are detected automatically (any path containing `.nc`, `.nc4`, or `.netcdf`).

```python
# Load only a subset of a large dataset
bz = Browzarr(
    dataset="gs://some-zarr-store",
    variable="temperature",
    z_slice=(0, 50),
    y_slice=(10, 200),
    x_slice=(10, 200),
)
```

## 3. Choose a plot type

Pick one plot method to configure the visualization. Each returns the same `Browzarr`
object so you can keep chaining or store it.

```python
bz.volume()      # 3D volume render
# bz.points()    # point cloud
# bz.flat()      # flat (3D-displaceable) surface
# bz.sphere()    # globe/sphere
```

You can pass options directly:

```python
bz.volume(colormap="inferno", transparency=0.5)
```

## 4. Launch the plot

```python
bz.plot()
```

`plot()` starts (or reuses) a local server and opens the view. Where it appears depends
on your environment — see [Environments](environment.md).

### Getting the URL instead of opening a browser

```python
url = bz.plot(give_url=True)
print(url)  # https://browzarr.io/latest/?data=...
```

## Full example

```python
from browzarr import Browzarr

Browzarr(
    dataset="gs://some-zarr-store",
    variable="temperature",
    z_slice=(0, 40),
).volume(
    colormap="turbo",
    transparency=0.6,
    value_range=(270, 310),
).plot()
```

## Next steps

- Explore plot-specific options: [Plot Types](plot-types/common-options.md)
- Full API details: [API Reference](api-reference.md)
- Export and animate: [Export & Animation](export.md)
