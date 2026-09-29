# Volume Plot

The `volume()` plot type renders a **3D volume** of your data — every grid cell is
drawn as a colored voxel. It's ideal for seeing the vertical structure of a field
(e.g. humidity or temperature through the atmosphere).

```python
Browzarr(dataset="gs://store", variable="temperature").volume().plot()
```

In addition to the [common options](common-options.md), a volume plot accepts the
options below.

---

## Volume options

### `transparency`
`float` — Global opacity of the rendered volume, from `0.0` (fully transparent) to
`1.0` (opaque). Lower values let you see through the volume to structures behind it.

```python
.volume(transparency=0.15)
```

### `nan_transparency`
`float` — Opacity applied to cells whose value is missing (NaN / `fill_value`). Raise
this to make holes more visible.

```python
.volume(nan_transparency=0.8)
```

### `step_size`
`float` — Sampling step through the volume. Larger values skip more cells, which is
faster but coarser; smaller values are denser and heavier on the GPU.

```python
.volume(step_size=1.0)
```

### `use_frag_opt`
`bool` — Enable fragment-shader optimizations. Turn this on for large or dense volumes
to improve performance.

```python
.volume(use_frag_opt=True)
```

---

## Example

```python
from browzarr import Browzarr

Browzarr(
    dataset="gs://some-zarr-store",
    variable="specific_humidity",
    z_slice=(0, 80),
).volume(
    colormap="viridis",
    value_range=(0.0, 0.02),
    transparency=0.1,
    step_size=1.0,
    use_frag_opt=True,
    lon_extent=(-130.0, -60.0),
    lat_extent=(20.0, 55.0),
).plot()
```
