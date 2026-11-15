"use client";
import { useMemo, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { initialUtcStart, makeUtcWindow } from "@/components/RequestControls";
import RequestControls from "@/components/RequestControls";
import { useSites, useSiteData } from "@/lib/useSiteData";
import SiteChips from "@/components/SiteChips";
import SkyView from "@/components/SkyView";
import Cards from "@/components/Cards";
import TimeControls from "@/components/TimeControls";
import Timeline from "@/components/Timeline";
import Heatmap from "@/components/Heatmap";

const moonTrek = "https://trek.nasa.gov/moon/";
const quickMap = "https://quickmap.lroc.asu.edu/";

function ExternalTool({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <a href={href} target="_blank" rel="noreferrer" className="block rounded-lg border border-slate-700 bg-slate-900 p-3 hover:border-sky-500">
      <span className="font-medium text-sky-300">{title} ↗</span>
      <span className="mt-1 block text-xs text-slate-400">{description}</span>
    </a>
  );
}

export default function Planner() {
  const sites = useSites();
  const [siteId, setSiteId] = useState<string | null>(null);
  const [idx, setIdx] = useState(0);
  const initial = useMemo(() => initialUtcStart(), []);
  const [date, setDate] = useState(initial.date);
  const [time, setTime] = useState(initial.time);
  const [days, setDays] = useState(7);
  const window = useMemo(() => makeUtcWindow(date, time, days), [date, time, days]);
  const site = sites.data?.find((candidate) => candidate.id === (siteId ?? sites.data?.[0]?.id)) ?? null;
  const data = useSiteData(site, window);
  const count = data.eph?.sun_el.length ?? 0;
  const currentIndex = count ? Math.min(idx, count - 1) : 0;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Mission planner</h1>
        <p className="mt-1 text-sm text-slate-400">Request live Sun and Earth positions for a candidate lunar site. Terrain-relative visibility is shown only when the backend returns a complete, provenance-checked DEM horizon.</p>
      </div>

      <div className="rounded-md border border-amber-600/70 bg-amber-950/50 p-3 text-sm text-amber-100">
        Candidate names and coordinates in the supplied catalog are marked MOCK / unverified. Horizons values are live for the displayed coordinates; they do not validate the candidate location. No bundled precomputed fixture is used as a fallback.
      </div>

      {sites.error && <p role="alert" className="rounded border border-red-700 bg-red-950 p-3 text-sm text-red-200">Could not load candidate sites: {sites.error}</p>}
      {sites.loading && <p className="text-sm text-slate-400">Loading candidate site catalog…</p>}
      {sites.data && <SiteChips sites={sites.data} value={site?.id ?? null} onChange={setSiteId} />}

      {site && (
        <section className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm">
          <div className="font-medium">{site.name} <span className="text-slate-400">({site.lat.toFixed(2)}° latitude, {site.lon.toFixed(2)}° longitude)</span></div>
          <p className="mt-1 text-slate-300">{site.description}</p>
          {site.source_url.startsWith("http") && <a href={site.source_url} target="_blank" rel="noreferrer" className="text-sky-400 underline">Candidate source</a>}
        </section>
      )}

      <RequestControls date={date} time={time} days={days}
        onDate={(value) => value && setDate(value)} onTime={(value) => value && setTime(value)} onDays={setDays} />

      {data.loading && <p role="status" className="text-sm text-slate-300">Requesting NASA/JPL Horizons data from the backend…</p>}
      {data.error && <div role="alert" className="rounded-md border border-red-700 bg-red-950 p-3 text-sm text-red-200"><strong>Live ephemeris unavailable.</strong> {data.error}<p className="mt-1 text-xs">Backend: {API_BASE_URL}. Check the backend process and its allowed CORS origins. No fixture values have been substituted.</p></div>}

      {data.eph && (
        <>
          <div className="flex flex-wrap justify-between gap-2 rounded border border-slate-800 bg-slate-950 p-2 text-xs text-slate-300">
            <span>Source: {data.eph.provenance}</span>
            <span>Response cache: {data.cache ?? "not reported"}</span>
            <span>All timestamps UTC</span>
          </div>
          <div className="rounded border border-amber-700/70 bg-amber-950/30 p-2 text-xs text-amber-100">
            Coordinates queried: {site?.lat.toFixed(4)}°, {site?.lon.toFixed(4)}°. The candidate coordinates remain unverified.
          </div>
          <Cards eph={data.eph} vis={data.vis} idx={currentIndex} />
          <TimeControls eph={data.eph} vis={data.vis} idx={currentIndex} setIdx={setIdx} />
          {data.hz && (
            <>
              <h2 className="pt-1 text-lg font-semibold">Local terrain horizon and sky view</h2>
              <SkyView eph={data.eph} hz={data.hz} idx={currentIndex} />
            </>
          )}
          {data.terrainMessage && (
            <div className={`rounded-md border p-3 text-sm ${data.vis ? "border-emerald-800 bg-emerald-950/30 text-emerald-100" : "border-amber-700 bg-amber-950/30 text-amber-100"}`}>
              <strong>{data.vis ? "Terrain analysis returned" : "Terrain analysis not available"}.</strong> {data.terrainMessage}
              {data.terrainProvenance && <p className="mt-1 text-xs">Visibility source: {data.terrainProvenance}. The rule is body-center elevation above interpolated terrain horizon; it is not full-disk visibility or a communications link budget.</p>}
              {data.terrainMetadata && <details className="mt-2"><summary className="cursor-pointer">DEM metadata</summary><pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(data.terrainMetadata, null, 2)}</pre></details>}
            </div>
          )}
          {data.vis ? (
            <>
              <h2 className="pt-2 text-lg font-semibold">Terrain-relative visibility timeline</h2>
              <Timeline eph={data.eph} vis={data.vis} idx={currentIndex} setIdx={setIdx} />
              <h2 className="pt-2 text-lg font-semibold">Sunlight by date and hour</h2>
              <Heatmap eph={data.eph} sun={data.vis.sun} setIdx={setIdx} />
            </>
          ) : (
            <p className="rounded border border-slate-700 bg-slate-900 p-3 text-sm text-slate-300">Visibility timeline and sunlight heatmap are withheld because no complete terrain-adjusted visibility response is available. Sun and Earth angles above are Horizons body-center values only.</p>
          )}
        </>
      )}

      <section className="space-y-2">
        <div>
          <h2 className="text-lg font-semibold">NASA lunar mapping tools</h2>
          <p className="text-xs text-slate-400">These external sites provide the actual map interfaces; this app does not recreate their visualizations. Both currently restrict third-party iframe embedding, so the buttons open the official tools directly.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <ExternalTool title="NASA Moon Trek" description="Open NASA's lunar terrain and mapping tool." href={moonTrek} />
          <ExternalTool title="LROC QuickMap" description="Open the official LROC imagery and map interface." href={quickMap} />
        </div>
      </section>
    </div>
  );
}
