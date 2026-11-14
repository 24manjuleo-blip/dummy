# Scientific assumptions, conventions, and limitations

## Ephemeris conventions

The service queries JPL Horizons observer-table quantity 4 for targets 10 (Sun) and 399 (Earth), using the Moon-centered user geodetic site convention (`CENTER=coord@301`, longitude, latitude, altitude in km). A real live request was verified on 2026-11-15. Horizons labels the returned angles “airless apparent” topocentric azimuth/elevation; no terrestrial atmospheric refraction is applied. The API response notes light-time, gravitational deflection, stellar aberration, precession and nutation compensation. Values are parsed only after verifying the response names the AZ/EL columns. Request output and exact conventions may evolve, so API payload errors and changed formats fail visibly.

The backend sends time-interval requests in UTC, with a configured minute step. Site longitude is east-positive; API accepts −180..360° and Horizons normalizes it. User altitude is meters at the site input and converted to kilometers for Horizons. This package does not separately calculate geometric elevation, so consumers must not label this returned series “geometric.” It is not a model for a specific lander/antenna state or a high-precision mission navigation solution.

## Terrain horizon and visibility

Ephemeris elevation and terrain visibility are separate. The terrain analyzer samples only a server-configured DEM located within an approved directory. It rejects EPSG:4326 and requires a CRS whose ellipsoid radius is lunar-sized. Site/raster transforms use a spherical lunar longitude/latitude CRS, and require an exact match between explicitly configured site and DEM body-fixed frame IDs; it does not transform between different frames. It ray-samples no finer than the raster native pixel resolution (and otherwise uses the configured minimum step) up to the requested range and applies an approximate spherical lunar curvature drop using 1,737,400 m lunar radius. Any requested point beyond raster bounds or at masked/nodata content raises an incomplete-coverage error; no partial horizon vector is returned. This CRS/frame gate does not validate raster vertical units, datum, registration, sample scaling, or whether values are elevations; those remain product-label/SIS validation requirements. Horizon angle is the maximum sampled elevation angle from the site tangent plane. Body-center visibility is true only when the returned ephemeris center elevation is above interpolated DEM horizon elevation for that azimuth.

This horizon algorithm is a practical approximation, not a validated landing-safety product. Raster registration, interpolation, DEM geolocation, vertical datum and scaling/offset must be checked from each PDS label. Angular sample spacing and finite ray spacing can miss narrow ridges. The implementation does not model horizon uncertainty, local slopes below pixel scale, boulder-scale hazards, refracted light, or extended-body disk overlap. It does not estimate communications link margin.

The event detector linearly interpolates between requested time samples where body-center elevation relative to the terrain horizon changes sign. Rise/set times are therefore resolution-dependent, not exact contact solutions. Durations are limited by request start/stop bounds and explicitly reported as truncated. Sunrise/sunset terminology means center-of-Sun terrain-horizon crossing, not solar-limb contact. The same logic applied to Earth is Earthrise/Earthset, not an Earth visibility/link budget.

## LOLA and PGDA raster policy

Raw LOLA IMG files have detached PDS labels. Always inspect the actual selected product label and supporting SIS before applying sample type, byte order, dimensions, map projection, coverage, scale/offset, coordinate frame, or vertical datum. One checked 10-pixel/degree file was a count grid, not an elevation raster. The elevation conversion documented for certain GDR products must not be applied to unrelated products. Never interpret a browse image as an analysis DEM.

PGDA's MOON_PA DE421 products and MOON_ME products are not interchangeable without coordinate transformation; catalog pages report a material frame difference. Polar illumination products' COG overview values may be averaged when zoomed out and must not be treated as full-resolution samples.

## Product status labels

- **LIVE NASA DATA**: a response retrieved during the API request from a named NASA/JPL endpoint.
- **COMPUTED FROM USER-PROVIDED DEM**: derived locally from a specified file. This does not certify product metadata or science validation.
- **PRECOMPUTED DATA**: not included in this package.
- **MOCK DATA**: not included or served by this backend.

## Not yet independently validated

No mission-grade end-to-end validation against a certified lunar lander ephemeris, surveyed terrain horizon, or precision sunrise/sunset reference has been performed. The curvature model, horizon interpolation and temporal event interpolation need comparison against independent reference calculations before mission operations use. Moon Trek polar product capabilities were not verified and are intentionally not configured. A downloaded and product-specifically validated PDS LOLA `LDEM_85S_40M` raster/labels are included. It covers 85°S–90°S at 40 m/pixel in the `MEAN EARTH/POLAR AXIS OF DE421` body-fixed frame. Its values are converted as `height_m=DN×0.5`, relative to the 1,737,400 m reference sphere, without geoid correction. The input candidate site coordinates are still unverified, the DEM only covers the south-polar latitude band, requested rays may exceed its bounds, and no independent end-to-end horizon validation has been completed.
