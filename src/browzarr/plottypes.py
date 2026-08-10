from dataclasses import dataclass, asdict
from typing import Literal, TypedDict
import re

def snake_to_camel(s: str) -> str:
    return re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), s)

class Vector3(TypedDict):
    x: float
    y: float
    z: float

@dataclass
class PlotBase():
    colormap: str | None = None
    flip_colormap: bool | None = None
    show_borders: bool | None = None
    border_width: float | None = None
    border_color: str | None = None
    lon_extent: tuple[float, float] | None = None
    lat_extent: tuple[float, float] | None = None
    lon_resolution: float | None = None
    lat_resolution: float | None = None
    interp_pixels: bool | None = None
    use_ortho: bool | None = None
    fill_value: float | None = None
    mask_feature: Literal[0, 1, 2] | None = None # 0=no mask, 1=mask land, 2=mask ocean
    mask_value: float | None = None
    camera_position: Vector3 | None = None 
    value_range: tuple[float, float] | None = None
    native_CRS: str | None = None
    dest_CRS: str | None = None

    @property
    def plottype(self) -> str:
        return self.__class__.__name__.lower()

    def to_spec(self) -> dict:
        """Serialize to the JSON blob the JS frontend expects."""
        param_dict = {"plot_type": self.plottype, **asdict(self)}
        return {snake_to_camel(k): v for k, v in param_dict.items() if v is not None}

@dataclass
class Volume(PlotBase):
    transparency: float | None = None
    nan_transparency: float | None = None
    step_size: float | None = None
    use_frag_opt: bool | None = None

    

@dataclass
class Points(PlotBase):
    point_size: float | None = None
    time_scale: float | None = None
    scale_points: bool | None = None



@dataclass
class Flat(PlotBase):
    displace_faces: bool | None = None
    displacement: float | None = None
    offset_negatives: bool | None = None



@dataclass
class Sphere(PlotBase):
    displace_faces: bool | None = None
    displacement: float | None = None
    offset_negatives: bool | None = None