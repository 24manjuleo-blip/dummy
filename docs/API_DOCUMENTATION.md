# API documentation

Base URL: `http://localhost:8000`. Interactive OpenAPI: `/docs`. Errors use JSON `{"detail":"..."}`.

## Health and resources

`GET /api/v1/health` returns service status and whether a DEM is configured. `GET /api/v1/nasa/resources` returns source URLs and source type/provenance.

## Moon Trek WMTS

`GET /api/v1/nasa/moontrek/layers` performs a live HTTPS GET of the configured verified sample GetCapabilities XML, then returns layer identifiers, title, advertised formats/styles, WGS84 bounds, ResourceURL template, matrix set identifiers, CRS, and advertised matrix IDs. Failure to fetch/parse is HTTP 502. Polar CRS identifiers in the response are not configured layer endpoints.

## Horizons ephemeris

`POST /api/v1/nasa/horizons/ephemeris`

```json
{
  "latitude_deg": -89.5,
  "longitude_deg": 0.0,
  "altitude_m": 0,
  "name": "Example site",
  "targets": ["10", "399"],
  "start_utc": "2026-11-15T00:00:00Z",
  "stop_utc": "2026-11-15T06:00:00Z",
  "step_minutes": 60
}
```

Targets default to `10` Sun and `399` Earth. Horizons query settings specify observer ephemeris, Moon center 301, user geodetic site, UTC period, step size, and quantity 4. The response is an object with site/time metadata, target-keyed arrays of `{time_utc, azimuth_deg, elevation_deg}`, Horizons signature, source label `LIVE NASA JPL HORIZONS`, and cache status. The exact table is checked for named azimuth/elevation fields; changed formats fail rather than being interpreted by position. This endpoint returns Horizons airless apparent topocentric center angles; it does not return a separate geometric-elevation series or apply atmospheric refraction. Time interval is limited to 366 days; interval and target list are validated. Upstream/protocol failures produce HTTP 502; cached successful values include `cache: HIT`.

Example of the output row from a real successful request in the development check: `{"time_utc":"2026-Nov-15T00:00:00Z","azimuth_deg":91.710071449,"elevation_deg":-24.422309707}` for a Sun observer query at latitude/longitude zero. This example is evidence of parser format only, not bundled or reused as endpoint data.

## Terrain horizon

`POST /api/v1/terrain/horizon`

```json
{"latitude_deg":-89.5,"longitude_deg":0,"altitude_m":0,"azimuth_step_deg":1,"max_distance_m":50000,"mast_height_m":0}
```

Requests do not accept filesystem paths. The service uses only server-configured `LUNAR_DEM_PATH` after resolving it inside the approved `LUNAR_DEM_ROOT`. Successful output includes sampled azimuth/elevation arrays, DEM filename, embedded label-derived `dem_metadata` when available, matched frame IDs, lunar radius, range, a `coverage` field confirming every requested sample was present, and limitations. HTTP 503 means no approved DEM/frame configuration is available **or** any ray sample reaches raster bounds/nodata; the API does not return a partial horizon. HTTP 422 identifies other raster or processing failures. EPSG:4326 is rejected as an Earth CRS, and the DEM CRS must advertise a lunar-sized ellipsoid. The configured site-frame ID and label-verified DEM-frame ID must match exactly; no inter-frame transformation is implemented.

## Site visibility analysis

`POST /api/v1/analysis/site-visibility`

```json
{
  "ephemeris": {"targets":{"10":{"rows":[{"time_utc":"2026-11-15T00:00:00Z","azimuth_deg":90,"elevation_deg":10}]}}},
  "horizon": {"azimuth_step_deg":1,"elevation_deg":[0,0,0,0]}
}
```

The request schema is intentionally generic to allow existing validated payloads. `results` contains timestamped per-body samples with terrain horizon, angular clearance, and boolean `terrain_adjusted_visible`, plus crossing/window summaries. Visibility rule: Horizons returned center elevation must exceed interpolated terrain horizon at the corresponding azimuth. Event times are approximate linear crossings between samples, with the sampling interval and request-bound truncation stated. HTTP 422 means payload contract fields are missing/invalid.

## Site comparison

`POST /api/v1/analysis/site-comparison` accepts `{"sites":[<2..20 EphemerisRequest objects>]}`. Each site gets live ephemerides and a terrain calculation from configured DEM. This endpoint is unavailable without valid configured coverage and returns HTTP 503 if terrain is not configured or HTTP 502 for an upstream computation failure. Unknown request fields such as `dem_path` are rejected.
