# Implementation report

## Implemented and validated

- Separate FastAPI service with environment configuration, request validation, CORS, caching, NASA resource endpoints, interactive API documentation, and live JPL Horizons parsing.
- Terrain horizon sampling is fail-closed: every requested sample along every ray must be inside raster bounds and valid. Any out-of-bounds or nodata sample aborts the full response; no ray silently skips missing data. Sampling is no finer than the DEM pixel size. Successful results report complete coverage and include label-derived raster provenance when available.
- Added the official PDS LOLA `LDEM_85S_40M` data, its detached PDS3 label and PDS4 XML, a strict product-specific converter, and a SHA-256 validation manifest under `data/lola/`. The converter checked the label-declared 7,584×7,584 signed little-endian 16-bit layout against the IMG byte count and observed DN extrema; cross-checked both labels' scale, offset, projection, bounds, pixel origin, and frame; and produced a 40 m lunar polar-stereographic GeoTIFF.
- Verified product interpretation: height is `DN × 0.5 m` relative to a 1,737,400 m reference sphere; the offset is added to calculate planetary radius, not to this relative-height surface. This is not geoid-corrected topography. Frame is `MEAN EARTH/POLAR AXIS OF DE421`, planetocentric latitude, with 85°S–90°S coverage. See `docs/LOLA_PRODUCT_VALIDATION.md` and `data/lola/ldem_85s_40m_validation.json`.
- Removed the static WMTS tile template. The API now retains the live `ResourceURL` candidates returned by each layer's GetCapabilities document, and the integration guide directs clients to use that advertised template. A live NASA response was verified in this run.
- Kept the supplied reference ZIP's useful practices: explicit candidate-coordinate caveats, product provenance, bounds-aware sampling, and independent validation guidance. No changes were made to the original frontend repository.

## Verification performed

`pytest -q`: **15 passed**. Tests cover science calculations, lunar CRS/frame guards, approved DEM path containment, HTTP rejection of client paths, failure for out-of-bounds and nodata ray samples, and verbatim live WMTS ResourceURL parsing with no invented fallback.

The downloaded PDS source is 115,034,112 bytes with SHA-256 `1609e9b860748e0b9952a7239c51b37d3b2a799d35e9fc3c258526711cc1e51d`. The PDS3 label SHA-256 is `d8105776af7fb79b1862ffa3946d013ec34f4dc6a00b7f6bff22ef8f768a5d3d`; the PDS4 XML SHA-256 is `e246e7bcb6773a6a114d0fb17760655e64b46a8b4afc15ea67eb98c5820e58ff`.

A processing-only smoke test read the real converted raster and produced a complete 72-bin profile at the reference archive's unverified candidate coordinate (-89.9°, 0°) for a 10 km range. A second smoke test at its unverified (-85.9°, 0°) candidate with a 50 km range correctly failed at 27.28 km when a ray reached the -85° raster boundary. These tests verify processing and coverage behavior, not the candidate coordinates or scientific accuracy of a landing-site analysis.

The live Moon Trek GetCapabilities request returned a `ResourceURL` for the sample layer; the API response contained that exact template and all advertised resource URLs. Existing live Horizons/Moon Trek smoke tests remain development checks, not deployment validation.

## Remaining limitations and deployment steps

The product is a 40 m/pixel south-polar grid, not the reference ZIP's derived 5 m/pixel site-specific PGDA GeoTIFFs. It does not cover sites outside 85°S–90°S, and even a site inside that band may lack the requested full ray radius. The candidate site coordinates remain unverified and carry no independently validated input frame. Do not configure the site frame or use these candidates as live analysis sites until their source coordinates and DE421 mean-Earth frame are confirmed. No transformation between different lunar body-fixed frames is implemented.

No independent terrain-horizon reference comparison, uncertainty propagation, high-resolution hazard analysis, or mission-grade end-to-end scientific validation has been performed. The spherical curvature, ray interpolation, temporal crossing interpolation, point-center body treatment, and 40 m gridded product's own interpolation limitations remain. This is research/prototype software, not an operational landing-safety system.

The service has not been deployed. Configure the approved DEM path only after coordinate provenance is established; then set production CORS, authentication/rate limits, protected raster storage, and frontend API base URL. Leave terrain unavailable until these checks are satisfied.
