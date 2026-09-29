# Common Plot Options

These options are available on **every** plot type: `volume()`, `points()`, `flat()`,
and `sphere()`. They control shared visual styling, data mapping, extent, masking, and
camera position.

They are passed directly as keyword arguments to the plot method:

```python
Browzarr(dataset="gs://store", variable="temp").volume(
    colormap="inferno",
    value_range=(270, 310),
    show_borders=True,
)
```

> Parameter names are automatically camel-cased for the frontend. Use snake_case in
> Python (`camera_position`), and it is delivered as `cameraPosition` to the browser.

---

## Color & colorbar

### `colormap`
`str` — The colormap to apply. Pass any colormap name Browzarr supports (e.g.
`"inferno"`, `"turbo"`, `"viridis"`).

```python
.volume(colormap="turbo")
```

### `flip_colormap`
`bool` — Reverse the colormap direction.

```python
.volume(flip_colormap=True)
```

### `value_range`
`tuple[float, float]` — Explicit minimum/maximum values mapped to the ends of the
colormap. Fixed range keeps colors consistent across frames or comparisons.

```python
.volume(value_range=(270, 310))
```

### `fill_value`
`float` — Value to treat as the data fill/missing value.

```python
.volume(fill_value=-9999.0)
```

---

## Data extent & resolution

### `lon_extent` / `lat_extent`
`tuple[float, float]` — Restrict the data to a longitude / latitude window:
`(min, max)`.

```python
.volume(lon_extent=(-125.0, -66.0), lat_extent=(24.0, 50.0))
```

### `lon_resolution` / `lat_resolution`
`float` — Grid resolution (degrees) for longitude / latitude sampling.

```python
.volume(lon_resolution=0.5, lat_resolution=0.5)
```

### `interp_pixels`
`bool` — Interpolate between pixels for smoother rendering.

```python
.volume(interp_pixels=True)
```

---

## Borders

### `show_borders`
`bool` — Draw country/coastline borders over the plot.

```python
.volume(show_borders=True)
```

### `border_width`
`float` — Line width of the borders.

```python
.volume(border_width=1.5)
```

### `border_color`
`str` — Border color (CSS color string, e.g. hex or name).

```python
.volume(border_color="#ffffff")
```

---

## Masking

### `mask_feature`
`Literal[0, 1, 2]` — Mask data by geographic feature:

| Value | Meaning |
|-------|---------|
| `0` | No mask |
| `1` | Mask **land** (show ocean data only) |
| `2` | Mask **ocean** (show land data only) |

```python
.volume(mask_feature=1)  # keep only ocean data
```

### `mask_value`
`float` — The value to assign to masked-out regions.

```python
.volume(mask_feature=1, mask_value=-9999.0)
```

---

## Projection / reprojection

### `use_ortho`
`bool` — Use an orthographic (3D globe) projection. Off by default for `flat` plots.

```python
.flat(use_ortho=True)
```

### `native_CRS` / `dest_CRS`
`str` — Reproject the data from `native_CRS` to `dest_CRS` (CRS codes/names Browzarr
supports). When **both** are provided, reprojection is enabled automatically.

```python
.volume(native_CRS="EPSG:4326", dest_CRS="EPSG:3857")
```

---

## Camera

### `camera_position`
`Vector3` — A 3D camera position `{x, y, z}`. Pass a dict with `x`, `y`, `z` keys.

```python
.volume(camera_position={"x": 0.0, "y": 0.0, "z": 5.0})
```

The camera position is forwarded to the frontend as a separate `camera` query parameter.

---

## Example using many common options

```python
from browzarr import Browzarr

Browzarr(
    dataset="gs://some-zarr-store",
    variable="temperature",
    z_slice=(0, 30),
).volume(
    colormap="RdYlBu_r",
    flip_colormap=False,
    value_range=(250, 320),
    show_borders=True,
    border_color="#222222",
    lon_extent=(-130.0, -60.0),
    lat_extent=(20.0, 55.0),
    mask_feature=1,
    mask_value=-9999.0,
    camera_position={"x": 10.0, "y": -5.0, "z": 8.0},
).plot()
```
