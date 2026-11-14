/**
 * Example only: adapt successful API responses to the unchanged frontend types in lib/data.ts.
 * Never call these conversion helpers with mock or precomputed values while labeling them LIVE NASA DATA.
 */
export type ApiRow = { time_utc: string; azimuth_deg: number; elevation_deg: number };
export type ApiEphemeris = { targets: Record<string, { rows: ApiRow[] }> };
export type ApiTerrain = { azimuth_step_deg: number; azimuth_deg: number[]; elevation_deg: number[]; mast_height_m: number; dem_source: string };
export function toFrontendEphemeris(siteId: string, api: ApiEphemeris) {
  const sun = api.targets["10"]?.rows;
  const earth = api.targets["399"]?.rows;
  if (!sun?.length || !earth?.length) throw new Error("Live API response must include non-empty Sun (10) and Earth (399) rows");
  const times = sun.map((r) => r.time_utc);
  if (earth.length !== sun.length || earth.some((r, i) => r.time_utc !== times[i]))
    throw new Error("Sun and Earth series must have the same UTC timestamps");
  const step = times.length > 1 ? (Date.parse(times[1]) - Date.parse(times[0])) / 60_000 : 0;
  if (!Number.isInteger(step) || step < 1) throw new Error("Cannot infer a valid time step from timestamps");
  return {
    site_id: siteId,
    start_utc: times[0],
    step_minutes: step,
    sun_az: sun.map((r) => r.azimuth_deg),
    sun_el: sun.map((r) => r.elevation_deg),
    earth_az: earth.map((r) => r.azimuth_deg),
    earth_el: earth.map((r) => r.elevation_deg),
    provenance: "LIVE NASA JPL HORIZONS — airless apparent topocentric center angles",
  };
}
export function toFrontendHorizon(siteId: string, api: ApiTerrain) {
  if (api.azimuth_step_deg !== 1 || api.elevation_deg.length !== 360)
    throw new Error("The current SkyView component expects exactly 360 one-degree horizon bins");
  return {
    site_id: siteId,
    az_step_deg: 1,
    elev_deg: api.elevation_deg,
    mast_height_m: api.mast_height_m,
    dem_source: `COMPUTED FROM USER-PROVIDED DEM: ${api.dem_source}`,
  };
}
