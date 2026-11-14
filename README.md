# Lunar Landing Site Navigator — FastAPI backend

Independent integration package for the existing Next.js frontend. This directory was developed separately from the public repository. No commit or push was made, and the frontend checkout was only read for compatibility. This backend does not serve mock/precomputed science values.

## Quick start

Requires Python 3.11+ and internet access for NASA endpoints. For terrain analysis, install system GDAL libraries as required by Rasterio. Terrain stays unavailable until a genuine LOLA elevation raster, approved storage root, lunar CRS, and matching site/DEM body-fixed frame IDs are configured after label/SIS review.

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env                # Windows: copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: `http://localhost:8000/docs`; OpenAPI JSON: `/openapi.json`. Health endpoint: `GET /api/v1/health`. Configure `LUNAR_CORS_ORIGINS=http://localhost:3000` and set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in the frontend's local environment. No NASA API key is required for the included public endpoints.

## API

The API endpoints include:

- `GET /api/v1/health`
- `GET /api/v1/nasa/resources`
- `GET /api/v1/nasa/moontrek/layers` — fetches and parses a real sample layer GetCapabilities document at request time.
- `POST /api/v1/nasa/horizons/ephemeris` — requests live Sun/Earth observer ephemeris from NASA/JPL.
- `POST /api/v1/terrain/horizon` — computes a local horizon from a server-configured and allowlisted DEM. The client cannot supply a filesystem path. Returns HTTP 503 unless the approved raster, lunar CRS and matching body-fixed frame IDs are configured.
- `POST /api/v1/analysis/site-visibility` — compares explicit Horizons samples with DEM terrain horizon and estimates crossings.
- `POST /api/v1/analysis/site-comparison` — multi-site live comparison; requires a configured valid DEM.

Full request/response examples and error semantics are in [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md). `docs/openapi.yaml` is a concise endpoint index; runtime `/openapi.json` is authoritative.

## NASA integration and scientific boundaries

Horizons is used for observer ephemeris only. A live request on 2026-11-15 verified `CENTER=coord@301`, geodetic `SITE_COORD` order (east longitude, latitude, altitude km), and quantity 4's named AZ/EL output. The parser refuses unnamed or altered table formats. Returned angles are Horizons “airless apparent” topocentric center values. DEM terrain visibility is separate and never inferred from those angles alone.

Moon Trek uses actual WMTS GetCapabilities XML. One equirectangular sample layer is configured and identified as a sample, not a universal tile template. Polar layer products are not configured pending product-specific capabilities checks. QuickMap is linked externally: its live response currently sends `X-Frame-Options: sameorigin` and `CSP frame-ancestors 'self'`, preventing third-party iframes.

A real PDS LOLA `LDEM_85S_40M` polar height grid and its detached PDS3 `.lbl` plus PDS4 `.xml` are included under `data/lola/`. The product-specific `scripts/prepare_lola_85s_40m.py` validates its sample encoding, byte count, label scale/offset, measured DN extrema, polar projection, south-polar coverage and `MEAN EARTH/POLAR AXIS OF DE421` frame, then generates a lunar-CRS height GeoTIFF. Its PDS-defined height is `DN × 0.5 m` relative to the 1,737,400 m reference sphere; the offset is added only to obtain planetary radius, and no geoid correction is performed. Run `python scripts/prepare_lola_85s_40m.py` to create the derived raster. Do not enable it with frontend candidate sites until those coordinates and their coordinate frame are verified. The terrain algorithm now aborts if any requested ray sample is outside raster bounds or nodata; it will not silently skip holes or return an artificially low partial horizon. The service still enforces server-side approved DEM paths, lunar CRS, and exact site/DEM frame-ID match.

For the selected dataset's label verification, checksum, and scale/datum/frame interpretation, see [LOLA_PRODUCT_VALIDATION.md](docs/LOLA_PRODUCT_VALIDATION.md) and `data/lola/ldem_85s_40m_validation.json`. For source-specific NASA findings and caveats, see [NASA_SOURCES.md](docs/NASA_SOURCES.md); for scientific assumptions, see [SCIENTIFIC_ASSUMPTIONS.md](docs/SCIENTIFIC_ASSUMPTIONS.md). Keep the DEM/frame environment variables blank until the site's coordinate source and frame are verified against the raster frame.

## Tests

Run `pytest -q`. Unit tests cover named-column Horizons parsing, fail-closed handling of unknown formats, azimuth interpolation including north wrap, terrain visibility comparison, aborted incomplete-coverage/nodata rays, and verbatim live WMTS ResourceURL parsing. These are software tests, not mission-grade scientific validation. Live endpoints may fail due to network, rate limits, maintenance, or source changes; API requests report errors rather than substitute data.

## Deployment notes

Use a managed ASGI host with HTTPS, pinned dependencies, monitored logs, resource/time limits, and explicit CORS origins. Store DEMs in protected mounted storage; do not accept arbitrary user paths in a public deployment. Terrain endpoints accept no file path from the client. The service resolves only the configured DEM within its approved root; use a server-side asset ID mapping if supporting several approved rasters. Add request authentication/rate limits and data licensing review if exposing to the internet. Retest actual source capabilities and record retrieval times before operational use.
