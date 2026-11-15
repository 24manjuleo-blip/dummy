import type { Ephemeris, Horizon, Site } from "./data";

const configuredBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8081";
export const API_BASE_URL = configuredBase.replace(/\/+$/, "");

export type UtcWindow = { startUtc: string; stopUtc: string; stepMinutes: number };
export type ApiRow = { time_utc: string; azimuth_deg: number; elevation_deg: number };
export type ApiEphemeris = {
  site?: Record<string, unknown>;
  start_utc: string;
  stop_utc: string;
  step_minutes: number;
  targets: Record<string, { rows: ApiRow[]; source?: string; target_id?: string }>;
  cache?: "HIT" | "MISS";
};
export type ApiTerrain = {
  latitude_deg: number;
  longitude_deg: number;
  site_coordinate_frame?: string;
  dem_coordinate_frame?: string;
  azimuth_step_deg: number;
  azimuth_deg: number[];
  elevation_deg: number[];
  mast_height_m: number;
  max_distance_m: number;
  ray_step_m?: number;
  dem_source: string;
  dem_metadata?: Record<string, string | number>;
  provenance: string;
  coverage: string;
  limitations?: string[];
};
export type ApiVisibility = {
  results: Record<string, { samples: (ApiRow & { terrain_horizon_elevation_deg: number; terrain_adjusted_visible: boolean; terrain_offset_deg: number })[]; events?: Record<string, unknown> }>;
  provenance: { ephemeris: string; terrain: string; visibility_rule: string; limitation: string };
};
export type SiteData = {
  eph: Ephemeris;
  hz?: Horizon;
  vis?: { sun: boolean[]; earth: boolean[] };
  terrainMessage: string;
  terrainProvenance?: string;
  terrainMetadata?: ApiTerrain["dem_metadata"];
  cache?: string;
};

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { method: "GET", signal });
}

export async function apiPost<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
}

async function apiRequest<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...init, cache: "no-store" });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error(`Cannot reach the FastAPI backend at ${API_BASE_URL}. Check that it is running and that its CORS origin allows this frontend.`);
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") detail = payload.detail;
    } catch {
      // Keep the HTTP status when the server does not return a JSON error.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

function alignedRows(payload: ApiEphemeris): { sun: ApiRow[]; earth: ApiRow[]; step: number } {
  const sunTarget = payload.targets?.["10"];
  const earthTarget = payload.targets?.["399"];
  const sun = sunTarget?.rows;
  const earth = earthTarget?.rows;
  if (!Array.isArray(sun) || sun.length < 2 || !Array.isArray(earth) || earth.length !== sun.length) {
    throw new Error("Horizons must return aligned Sun (10) and Earth (399) sample rows.");
  }
  if (sunTarget.source !== "LIVE NASA JPL HORIZONS" || earthTarget.source !== "LIVE NASA JPL HORIZONS") {
    throw new Error("The backend response does not identify both series as live NASA/JPL Horizons data.");
  }
  const timestamps = sun.map((row) => Date.parse(row.time_utc));
  if (timestamps.some((value) => !Number.isFinite(value)) || earth.some((row, i) => Date.parse(row.time_utc) !== timestamps[i])) {
    throw new Error("Horizons Sun and Earth rows must have matching valid UTC timestamps.");
  }
  const step = (timestamps[1] - timestamps[0]) / 60_000;
  if (!Number.isInteger(step) || step < 1 || step !== payload.step_minutes) {
    throw new Error("Horizons sample spacing does not match the backend's declared step_minutes.");
  }
  for (let i = 1; i < timestamps.length; i++) {
    if (timestamps[i] - timestamps[i - 1] !== step * 60_000) {
      throw new Error("Horizons rows are not on one regular UTC time grid.");
    }
  }
  for (const row of [...sun, ...earth]) {
    if (!Number.isFinite(row.azimuth_deg) || !Number.isFinite(row.elevation_deg)) {
      throw new Error("Horizons returned a non-numeric azimuth or elevation sample.");
    }
  }
  return { sun, earth, step };
}

function toFrontendEphemeris(siteId: string, payload: ApiEphemeris): Ephemeris {
  const { sun, earth, step } = alignedRows(payload);
  return {
    site_id: siteId,
    start_utc: sun[0].time_utc,
    step_minutes: step,
    sun_az: sun.map((row) => row.azimuth_deg),
    sun_el: sun.map((row) => row.elevation_deg),
    earth_az: earth.map((row) => row.azimuth_deg),
    earth_el: earth.map((row) => row.elevation_deg),
    provenance: "LIVE NASA/JPL HORIZONS · airless apparent topocentric body-center AZ/EL",
    timestamps_utc: sun.map((row) => row.time_utc),
  };
}

function toFrontendHorizon(siteId: string, payload: ApiTerrain): Horizon {
  if (payload.provenance !== "COMPUTED FROM CONFIGURED APPROVED DEM; lunar CRS ellipsoid and matching body-fixed frame checked") {
    throw new Error("Terrain response is missing the expected approved-DEM provenance.");
  }
  if (payload.coverage !== "complete for all requested samples through max_distance_m") {
    throw new Error("Terrain response does not confirm complete DEM coverage.");
  }
  if (payload.azimuth_step_deg !== 1 || payload.azimuth_deg.length !== 360 || payload.elevation_deg.length !== 360) {
    throw new Error("The existing sky-view component requires a complete 360-bin, 1-degree terrain horizon.");
  }
  if (payload.azimuth_deg.some((azimuth, index) => azimuth !== index) || payload.elevation_deg.some((value) => !Number.isFinite(value))) {
    throw new Error("Terrain horizon azimuth bins or elevations are invalid.");
  }
  return {
    site_id: siteId,
    az_step_deg: 1,
    elev_deg: payload.elevation_deg,
    mast_height_m: payload.mast_height_m,
    dem_source: `${payload.dem_source} · ${payload.provenance}`,
  };
}

function toFrontendVisibility(payload: ApiVisibility, ephemeris: ApiEphemeris): { sun: boolean[]; earth: boolean[] } {
  const sunRows = payload.results?.["10"]?.samples;
  const earthRows = payload.results?.["399"]?.samples;
  const expectedSun = ephemeris.targets["10"].rows;
  const expectedEarth = ephemeris.targets["399"].rows;
  if (!Array.isArray(sunRows) || !Array.isArray(earthRows) || sunRows.length !== expectedSun.length || earthRows.length !== expectedEarth.length) {
    throw new Error("Visibility analysis must return a terrain-adjusted result for every Horizons sample.");
  }
  const checkRows = (actual: typeof sunRows, expected: ApiRow[]) => actual.every((row, i) =>
    Date.parse(row.time_utc) === Date.parse(expected[i].time_utc) && typeof row.terrain_adjusted_visible === "boolean",
  );
  if (!checkRows(sunRows, expectedSun) || !checkRows(earthRows, expectedEarth)) {
    throw new Error("Visibility samples are not aligned with the live Horizons UTC time grid.");
  }
  if (!payload.provenance?.ephemeris?.includes("NASA JPL HORIZONS") || !payload.provenance?.terrain?.includes("DEM")) {
    throw new Error("Visibility analysis provenance is incomplete.");
  }
  return {
    sun: sunRows.map((row) => row.terrain_adjusted_visible),
    earth: earthRows.map((row) => row.terrain_adjusted_visible),
  };
}

export async function loadLiveSiteData(site: Site, window: UtcWindow, signal: AbortSignal): Promise<SiteData> {
  const ephemerisPayload = await apiPost<ApiEphemeris>("/api/v1/nasa/horizons/ephemeris", {
    latitude_deg: site.lat,
    longitude_deg: site.lon,
    altitude_m: 0,
    name: site.name,
    targets: ["10", "399"],
    start_utc: window.startUtc,
    stop_utc: window.stopUtc,
    step_minutes: window.stepMinutes,
  }, signal);
  const eph = toFrontendEphemeris(site.id, ephemerisPayload);
  const cache = ephemerisPayload.cache;

  if (site.id !== "shackleton_rim") {
    return { eph, terrainMessage: "LOLA terrain calculations are currently restricted to the Shackleton Rim candidate. No terrain visibility is inferred for this site.", cache };
  }

  try {
    const terrainPayload = await apiPost<ApiTerrain>("/api/v1/terrain/horizon", {
      latitude_deg: site.lat,
      longitude_deg: site.lon,
      altitude_m: 0,
      azimuth_step_deg: 1,
      max_distance_m: 50_000,
      mast_height_m: 0,
    }, signal);
    const hz = toFrontendHorizon(site.id, terrainPayload);
    const visibilityPayload = await apiPost<ApiVisibility>("/api/v1/analysis/site-visibility", {
      ephemeris: ephemerisPayload,
      horizon: terrainPayload,
    }, signal);
    const vis = toFrontendVisibility(visibilityPayload, ephemerisPayload);
    return {
      eph,
      hz,
      vis,
      terrainMessage: "Complete configured LOLA DEM horizon returned for the requested candidate coordinates.",
      terrainProvenance: visibilityPayload.provenance.terrain,
      terrainMetadata: terrainPayload.dem_metadata,
      cache,
    };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    return {
      eph,
      terrainMessage: `Terrain visibility unavailable: ${error instanceof Error ? error.message : String(error)}`,
      cache,
    };
  }
}

export async function loadSites(): Promise<Site[]> {
  const base = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
  const result = await fetch(`${base}/data/sites.json`, { cache: "force-cache" });
  if (!result.ok) throw new Error(`Could not load candidate sites (${result.status}).`);
  return (await result.json()) as Site[];
}
