export type Site = { id: string; name: string; lat: number; lon: number; type: "apollo" | "south_pole" | "other"; source_url: string; description: string };
export type Ephemeris = {
  site_id: string;
  start_utc: string;
  step_minutes: number;
  sun_az: number[];
  sun_el: number[];
  earth_az: number[];
  earth_el: number[];
  timestamps_utc?: string[];
  provenance?: string;
};
export type Horizon = { site_id: string; az_step_deg: number; elev_deg: number[]; mast_height_m: number; dem_source: string };
export type Summaries = Record<string, { plain_text: string; expert_text: string }>;
const B = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const get = async <T,>(path: string): Promise<T> => {
  const response = await fetch(`${B}/data/${path}`, { cache: "force-cache" });
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json() as Promise<T>;
};
export const loadSummaries = () => get<Summaries>("summaries.json");
export const horizonAt = (h: Horizon, az: number) => {
  const a = ((az % 360) + 360) % 360;
  const i = Math.floor(a);
  const f = a - i;
  return h.elev_deg[i] * (1 - f) + h.elev_deg[(i + 1) % 360] * f;
};
export const isVisible = (el: number, az: number, h: Horizon) => el > horizonAt(h, az);
