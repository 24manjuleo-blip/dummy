import type { Ephemeris } from "@/lib/data";
import { nextChange, type Vis } from "@/lib/events";
import { fmtDuration, fmtUTC, idxToMs } from "@/lib/time";
import { SUN, EARTH } from "./colors";

function Card({ label, value, sub, color }: { label: string; value: string; sub: string; color: string }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-3" style={{ borderTopColor: color, borderTopWidth: 3 }}>
      <div className="text-xs uppercase tracking-wide text-slate-400">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-slate-400">{sub}</div>
    </div>
  );
}

export default function Cards({ eph, vis, idx }: { eph: Ephemeris; vis?: Vis; idx: number }) {
  const sm = eph.step_minutes;
  const when = (j: number | null) => (j === null ? "no change in data window" : fmtUTC(idxToMs(eph, j)));
  const dur = (j: number | null) => (j === null ? "beyond window" : fmtDuration(j - idx, sm));
  const sunV = vis?.sun[idx], earthV = vis?.earth[idx];
  const sn = vis ? nextChange(vis.sun, idx) : null, en = vis ? nextChange(vis.earth, idx) : null;
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Card label="Sun elevation now" value={`${eph.sun_el[idx].toFixed(2)}°`} color={SUN}
        sub={`${eph.sun_az[idx].toFixed(2)}° azimuth · ${sunV === undefined ? "terrain visibility not evaluated" : sunV ? "above terrain horizon" : "below terrain horizon"}`} />
      <Card label={sunV === undefined ? "Sun azimuth" : sunV ? "Time until sunset" : "Time until sunrise"} value={sunV === undefined ? `${eph.sun_az[idx].toFixed(2)}°` : dur(sn)} sub={sunV === undefined ? "clockwise from north" : when(sn)} color={SUN} />
      <Card label={earthV === undefined ? "Earth elevation" : "Earth visible"} value={earthV === undefined ? `${eph.earth_el[idx].toFixed(2)}°` : earthV ? "Yes" : "No"} color={EARTH}
        sub={earthV === undefined ? `Azimuth ${eph.earth_az[idx].toFixed(2)}° · terrain visibility not evaluated` : `Elevation ${eph.earth_el[idx].toFixed(2)}° · azimuth ${eph.earth_az[idx].toFixed(2)}° · Horizons body center`} />
      <Card label={earthV === undefined ? "Earth azimuth" : earthV ? "Time until Earthset" : "Time until Earthrise"} value={earthV === undefined ? `${eph.earth_az[idx].toFixed(2)}°` : dur(en)} sub={earthV === undefined ? "clockwise from north" : when(en)} color={EARTH} />
    </div>
  );
}
