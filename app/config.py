from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Lunar Landing Site Navigator API"
    cors_origins: str = "http://localhost:3000"
    cache_ttl_seconds: int = 900
    horizons_url: str = "https://ssd.jpl.nasa.gov/api/horizons.api"
    moontrek_base: str = "https://trek.nasa.gov"
    quickmap_url: str = "https://quickmap.lroc.asu.edu/"
    dem_path: str | None = None
    dem_root: str | None = None
    site_coordinate_frame_id: str | None = None
    dem_coordinate_frame_id: str | None = None
    lunar_radius_m: float = 1_737_400.0
    model_config = SettingsConfigDict(env_file=".env", env_prefix="LUNAR_", extra="ignore")
    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def terrain_ready(self) -> bool:
        if not (self.dem_path and self.dem_root and self.site_coordinate_frame_id and self.dem_coordinate_frame_id):
            return False
        if self.site_coordinate_frame_id.strip() != self.dem_coordinate_frame_id.strip():
            return False
        try:
            from .services.terrain import resolve_approved_dem
            resolve_approved_dem(self.dem_path, self.dem_root)
            return True
        except (OSError, ValueError):
            return False
        except Exception:
            return False

@lru_cache
def get_settings() -> Settings:
    return Settings()
