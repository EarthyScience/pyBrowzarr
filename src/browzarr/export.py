from dataclasses import dataclass, asdict
from .plot_types import snake_to_camel


@dataclass
class Export():
    include_background: bool | None = None
    include_colorbar: bool | None = None
    include_axis: bool | None = None
    cbar_loc: str | None = None
    cbar_num: float | None = None
    custom_res: tuple[float, float] | None = None
    main_title: str | None = None
    cbar_label: str | None = None
    cbar_units: str | None = None
    animate: bool | None = None
    frames: float | None = None
    frame_rate: float | None = None
    orbit: bool | None = None
    orbit_deg: float | None = None
    use_time: bool | None = None
    time_rate: float | None = None
    loop_time: bool | None = None
    keyframes: object | None = None
    keyframes_path: str | None = None
    preview: bool | None = None

    def to_spec(self) -> dict:
        """Serialize to the JSON blob the JS frontend expects."""
        param_dict = asdict(self)
        return {snake_to_camel(k): v for k, v in param_dict.items() if v is not None}