from dataclasses import dataclass, asdict
from typing import Literal, TypedDict, NotRequired

class Vector3(TypedDict):
    x: float
    y: float
    z: float


@dataclass
class PlotBase(TypedDict):
    colormap: NotRequired[str]
    flip_colormap: NotRequired[bool]
    show_borders: NotRequired[bool]
    border_width: NotRequired[float]
    border_color: NotRequired[str]
    lon_extent: NotRequired[tuple[float, float]]
    lat_extent: NotRequired[tuple[float, float]]
    lon_resolution: NotRequired[float]
    lat_resolution: NotRequired[float]
    interp_pixels: NotRequired[bool]
    use_ortho: NotRequired[bool]
    fill_value: NotRequired[float]
    mask_feature: NotRequired[Literal[0, 1, 2]] # 0=no mask, 1=mask land, 2=mask ocean
    mask_value: NotRequired[float]
    camera_position: NotRequired[Vector3]
    value_range: NotRequired[tuple[float, float]]
    native_CRS: NotRequired[str]
    dest_CRS: NotRequired[str]

    

@dataclass
class Volume(PlotBase):
    transparency: NotRequired[float]
    nan_transparency: NotRequired[float]
    step_size: NotRequired[float]
    use_frag_opt: NotRequired[bool]
    

@dataclass
class Points(PlotBase):
    point_size: NotRequired[float]
    time_scale: NotRequired[float]
    scale_points: NotRequired[bool]



@dataclass
class Flat(PlotBase):
    displace_faces: NotRequired[bool]
    displacement: NotRequired[float]
    offset_negatives: NotRequired[bool]


@dataclass
class Sphere(PlotBase):
    displace_faces: NotRequired[bool]
    displacement: NotRequired[float]
    offset_negatives: NotRequired[bool]

@dataclass
class Export(TypedDict):
    include_background: NotRequired[bool]
    include_colorbar: NotRequired[bool]
    include_axis: NotRequired[bool]
    cbar_loc: NotRequired[str]
    cbar_num: NotRequired[float]
    custom_res: NotRequired[tuple[float, float]]
    main_title: NotRequired[str]
    cbar_label: NotRequired[str]
    cbar_units: NotRequired[str]
    animate: NotRequired[bool]
    frames: NotRequired[float]
    frame_rate: NotRequired[float]
    orbit: NotRequired[bool]
    orbit_deg: NotRequired[float]
    use_time: NotRequired[bool]
    time_rate: NotRequired[float]
    loop_time: NotRequired[bool]
    keyframes: NotRequired[object]
    keyframes_path: NotRequired[str]
    preview: NotRequired[bool]