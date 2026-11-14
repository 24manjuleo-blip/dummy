import math
from pathlib import Path

class TerrainUnavailable(RuntimeError):
    pass

class IncompleteDEMCoverage(TerrainUnavailable):
    pass

def resolve_approved_dem(dem_path, approved_root):
    """Only resolve a trusted configured file inside the explicitly approved DEM root."""
    if not dem_path or not approved_root:
        raise TerrainUnavailable("DEM is unavailable: configure both a trusted DEM file and LUNAR_DEM_ROOT allowlist")
    try:
        root = Path(approved_root).expanduser().resolve(strict=True)
        path = Path(dem_path).expanduser().resolve(strict=True)
    except OSError as exc:
        raise TerrainUnavailable("Configured DEM root or file does not exist or cannot be resolved") from exc
    if not root.is_dir() or not path.is_file():
        raise TerrainUnavailable("Configured DEM root must be a directory and the approved DEM must be a file")
    if not path.is_relative_to(root):
        raise TerrainUnavailable("Configured DEM is outside the approved LUNAR_DEM_ROOT")
    return path

def lunar_geographic_crs(lunar_radius_m):
    """A spherical Moon longitude/latitude CRS; not terrestrial EPSG:4326."""
    from pyproj import CRS
    return CRS.from_proj4(f"+proj=longlat +R={lunar_radius_m} +no_defs +type=crs")

def validate_lunar_crs(raster_crs, site_frame_id, dem_frame_id, lunar_radius_m):
    """Require explicit matching body-fixed frames and a Moon-sized raster CRS."""
    from pyproj import CRS, Transformer
    if not site_frame_id or not dem_frame_id:
        raise TerrainUnavailable("Lunar coordinate-frame metadata is required for both site coordinates and the DEM")
    if site_frame_id.strip() != dem_frame_id.strip():
        raise TerrainUnavailable(f"Site frame {site_frame_id!r} does not match DEM frame {dem_frame_id!r}; an explicit validated frame transformation is required")
    try:
        raster = CRS.from_user_input(raster_crs)
    except Exception as exc:
        raise TerrainUnavailable(f"Could not parse the DEM's declared lunar CRS: {exc}") from exc
    if raster.to_epsg() == 4326:
        raise TerrainUnavailable("EPSG:4326 is an Earth CRS and is not accepted as a lunar body-fixed DEM CRS")
    try:
        a = float(raster.ellipsoid.semi_major_metre)
    except (AttributeError, TypeError, ValueError) as exc:
        raise TerrainUnavailable("DEM CRS does not declare a lunar ellipsoid/radius") from exc
    if not math.isfinite(a) or abs(a - lunar_radius_m) > 1000:
        raise TerrainUnavailable(f"DEM CRS ellipsoid radius {a:g} m is not consistent with configured lunar radius {lunar_radius_m:g} m")
    try:
        return Transformer.from_crs(lunar_geographic_crs(lunar_radius_m), raster, always_xy=True)
    except Exception as exc:
        raise TerrainUnavailable(f"Cannot transform configured lunar body-fixed coordinates into DEM CRS: {exc}") from exc

def _masked_or_nodata(sample, nodata):
    if getattr(sample, "mask", False):
        return True
    value=float(sample)
    return not math.isfinite(value) or (nodata is not None and value == nodata)

def compute_horizon(lat_deg, lon_deg, altitude_m=0, azimuth_step_deg=1, max_distance_m=50000, mast_height_m=0, dem_path=None, approved_root=None, site_frame_id=None, dem_frame_id=None, lunar_radius_m=1737400.0, ray_step_m=25):
    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        raise TerrainUnavailable("Install rasterio and numpy to analyze a georeferenced lunar DEM") from exc
    if not 1 <= azimuth_step_deg <= 10 or max_distance_m < 25 or ray_step_m < 1:
        raise ValueError("Invalid horizon sampling parameters")
    path = resolve_approved_dem(dem_path, approved_root)
    azimuths = list(range(0, 360, azimuth_step_deg))
    elevations = []
    with rasterio.open(path) as ds:
        if ds.crs is None:
            raise TerrainUnavailable("DEM has no declared CRS; refusing to infer coordinates")
        tags = ds.tags(1)
        to_raster = validate_lunar_crs(ds.crs, site_frame_id, dem_frame_id, lunar_radius_m)
        inv = ~ds.transform
        def sample(lat, lon, azimuth=None, distance=None):
            # Site and ray coordinates are Moon body-fixed lat/lon in the configured matching frame.
            x, y = to_raster.transform(lon, lat)
            row, col = ds.index(x, y)
            if row < 0 or row >= ds.height or col < 0 or col >= ds.width:
                where = "site" if azimuth is None else f"azimuth {azimuth}° at {distance:g} m"
                raise IncompleteDEMCoverage(f"DEM coverage is incomplete at {where}; refusing to publish a partial horizon")
            value = next(ds.sample([(x, y)], indexes=1, masked=True))[0]
            if _masked_or_nodata(value, ds.nodata):
                where = "site" if azimuth is None else f"azimuth {azimuth}° at {distance:g} m"
                raise IncompleteDEMCoverage(f"DEM contains masked/nodata elevation at {where}; refusing to publish a partial horizon")
            return float(value)
        site = sample(lat_deg, lon_deg)
        site += altitude_m + mast_height_m
        # Respect native ground resolution: do not repeatedly sample the same cell at a finer spacing.
        pixel_x = math.hypot(ds.transform.a, ds.transform.d)
        pixel_y = math.hypot(ds.transform.b, ds.transform.e)
        step_m = max(float(ray_step_m), pixel_x, pixel_y)
        distances = list(np.arange(step_m, max_distance_m, step_m, dtype=float))
        if not distances or distances[-1] < max_distance_m:
            distances.append(float(max_distance_m))
        for az in azimuths:
            best = -90.0
            for distance in distances:
                angular = distance / lunar_radius_m
                lat2 = math.asin(math.sin(math.radians(lat_deg)) * math.cos(angular) + math.cos(math.radians(lat_deg)) * math.sin(angular) * math.cos(math.radians(az)))
                lon2 = math.radians(lon_deg) + math.atan2(math.sin(math.radians(az)) * math.sin(angular) * math.cos(math.radians(lat_deg)), math.cos(angular) - math.sin(math.radians(lat_deg)) * math.sin(lat2))
                lon2_deg = ((math.degrees(lon2) + 180) % 360) - 180
                z = sample(math.degrees(lat2), lon2_deg, az, distance)
                # Approximate spherical lunar-curvature drop, using elevation relative to the reference sphere.
                angle = math.degrees(math.atan2(z - site, distance)) - math.degrees(distance / (2 * lunar_radius_m))
                best = max(best, angle)
            if not math.isfinite(best):
                raise IncompleteDEMCoverage(f"DEM returned no finite horizon at azimuth {az}°")
            elevations.append(best)
    return {
        "latitude_deg": lat_deg, "longitude_deg": lon_deg,
        "site_coordinate_frame": site_frame_id, "dem_coordinate_frame": dem_frame_id,
        "azimuth_step_deg": azimuth_step_deg, "azimuth_deg": azimuths,
        "elevation_deg": elevations, "mast_height_m": mast_height_m,
        "max_distance_m": max_distance_m, "ray_step_m": step_m,
        "dem_source": path.name,
        "dem_metadata": {key: tags[key] for key in ("product", "source_dataset", "source_image", "source_label", "source_label_sha256", "source_url", "height_units", "height_definition", "scaling_factor", "planetary_radius_offset_m", "vertical_reference", "coordinate_frame", "latitude_type") if key in tags},
        "provenance": "COMPUTED FROM CONFIGURED APPROVED DEM; lunar CRS ellipsoid and matching body-fixed frame checked",
        "lunar_radius_m": lunar_radius_m,
        "coverage":"complete for all requested samples through max_distance_m",
        "limitations": ["Incomplete bounds or nodata at any ray point aborts the result; no partial horizon is returned", "Frame equality is required; no transformation between distinct lunar body-fixed frames is implemented", "PDS vertical datum, scaling, registration, and units must be validated for the selected product", "DEM interpolation and native-resolution ray sampling can miss narrower features", "Horizon output is terrain geometry, not ephemeris"]
    }
