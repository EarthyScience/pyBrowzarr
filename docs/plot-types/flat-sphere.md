# Flat & Sphere Plots

The `flat()` and `sphere()` plot types both render a **2D surface** (one value per
longitude/latitude pair) that can be *displaced* — pushed up or down — to give the
field a physical, terrain-like height.

- **`flat()`** renders the surface on a flat plane (or as an orthographic globe when
  `use_ortho=True`).
- **`sphere()`** renders the surface on a globe.

Both accept the same set of options (plus the shared
[common options](common-options.md)).

```python
Browzarr(dataset="gs://store", variable="sea_level").flat().plot()
Browzarr(dataset="gs://store", variable="sea_level").sphere().plot()
```

---

## Shared flat/sphere options

### `displace_faces`
`bool` — Vertically displace (bump) the surface faces by the data value. Set this to
`True` to turn the flat field into 3D relief.

```python
.flat(displace_faces=True)
```

### `displacement`
`float` — Multiplier controlling how far each face is displaced. Higher values produce
more exaggerated relief.

```python
.flat(displace_faces=True, displacement=2.0)
```

### `offset_negatives`
`bool` — Shift negative values so they don't dip below the base surface. Useful when
you want only upward relief.

```python
.flat(offset_negatives=True)
```

---

## Examples

```python
from browzarr import Browzarr

# Displaced flat surface (relief map)
Browzarr(
    dataset="gs://some-zarr-store",
    variable="sea_surface_height",
).flat(
    colormap="RdYlGn",
    value_range=(-2.0, 2.0),
    displace_faces=True,
    displacement=1.5,
    offset_negatives=True,
).plot()

# Displaced globe
Browzarr(
    dataset="gs://some-zarr-store",
    variable="sea_surface_height",
).sphere(
    colormap="RdYlGn",
    value_range=(-2.0, 2.0),
    displace_faces=True,
    displacement=1.0,
).plot()
```
