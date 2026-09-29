# Points Plot

The `points()` plot type renders your data as a **point cloud** — one point per grid
cell, positioned by its coordinates and colored by value. It works well for sparse
data, wind/tracer fields, or when you want a lightweight view of a large domain.

```python
Browzarr(dataset="gs://store", variable="wind_speed").points().plot()
```

In addition to the [common options](common-options.md), a points plot accepts the
options below.

---

## Points options

### `point_size`
`float` — Radius/size of each rendered point, in pixels.

```python
.points(point_size=3.0)
```

### `time_scale`
`float` — Time scaling factor for time-animated point fields. Slows or speeds up how
point values evolve over time.

```python
.points(time_scale=0.5)
```

### `scale_points`
`bool` — Scale point size by the data value (larger for stronger values). When off,
all points render at `point_size`.

```python
.points(scale_points=True, point_size=2.0)
```

---

## Example

```python
from browzarr import Browzarr

Browzarr(
    dataset="gs://some-zarr-store",
    variable="wind_speed",
    z_slice=(0, 1),
).points(
    colormap="turbo",
    point_size=4.0,
    scale_points=True,
    value_range=(0.0, 40.0),
    lon_extent=(-130.0, -60.0),
    lat_extent=(20.0, 55.0),
).plot()
```
