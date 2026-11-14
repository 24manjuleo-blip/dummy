from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Site(StrictModel):
    latitude_deg: float = Field(ge=-90, le=90)
    longitude_deg: float = Field(ge=-180, le=360)
    altitude_m: float = Field(default=0, ge=-12000, le=100000)
    name: str | None = None

class EphemerisRequest(Site):
    targets: list[str] = Field(default_factory=lambda: ["10", "399"], min_length=1, max_length=8, description="Horizons body IDs; 10=Sun, 399=Earth")
    start_utc: datetime
    stop_utc: datetime
    step_minutes: int = Field(default=60, ge=1, le=1440)
    @field_validator("start_utc", "stop_utc")
    @classmethod
    def require_timezone(cls, v):
        if v.tzinfo is None: raise ValueError("Datetime must include timezone; use ISO-8601 UTC such as 2026-11-15T00:00:00Z")
        return v
    @field_validator("stop_utc")
    @classmethod
    def check_order(cls, v, info):
        start = info.data.get("start_utc")
        if start and (v <= start or (v-start).total_seconds() > 366*86400): raise ValueError("stop_utc must be after start_utc and within 366 days")
        return v

class HorizonRequest(Site):
    azimuth_step_deg: int = Field(default=1, ge=1, le=10)
    max_distance_m: int = Field(default=50000, ge=100, le=500000)
    mast_height_m: float = Field(default=0, ge=0, le=100)

class VisibilityRequest(StrictModel):
    ephemeris: dict
    horizon: dict

class CompareRequest(StrictModel):
    sites: list[EphemerisRequest] = Field(min_length=2, max_length=20)

class ErrorResponse(StrictModel):
    detail: str
