"use client";
import { useMemo, useState } from "react";
import { initialUtcStart, makeUtcWindow } from "@/components/RequestControls";
import RequestControls from "@/components/RequestControls";
import { useSites, useSiteData } from "@/lib/useSiteData";
import type { Site } from "@/lib/data";
import type { UtcWindow } from "@/lib/api";
import Cards from "@/components/Cards";
import SkyView from "@/components/SkyView";
import { dayStr, idxToMs, nSteps } from "@/lib/time";
import { both, countVisible, windowStats } from "@/lib/events";

function SiteColumn({ site, window, idx, setIdx }: { site: Site; window: UtcWindow; idx: number; setIdx: (i: number) => void }) {
  const data = useSiteData(site, window);
  if (data.loading) return <div className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-sm text-slate-400">Loading live Horizons for {site.name}…</div>;
  if (data.error) return <div role="alert" className="rounded-lg border border-red-800 bg-red-950 p-3 text-sm text-red-200"><h3 className="font-semibold">{site.name}</h3>{data.error}</div>;
  if (!data.eph) return null;
  const i = Math.min(idx, data.eph.sun_el.length - 1);
  const n = nSteps(data.eph);
  const percentage = (values: boolean[]) => ((100 * countVisible(values, 0, n)) / n).toFixed(0);
  return (
    <article className="space-y-3 rounded-lg border border-slate-700 bg-slate-950 p-3">
      <header><h3 className="font-semibold">{site.name}</h3><p className="text-xs text-slate-400">{site.lat.toFixed(2)}°, {site.lon.toFixed(2)}° · candidate coordinates unverified</p></header>
      <div className="text-xs text-slate-400">{data.eph.provenance} · UTC grid · {new Date(idxToMs(data.eph, i)).toISOString().replace("T", " ").slice(0, 16)} UTC</div>
      <Cards eph={data.eph} vis={data.vis} idx={i} />
      <label className="block text-xs text-slate-400">Shared UTC time index
        <input type="range" min={0} max={n - 1} value={i} onChange={(event) => setIdx(Number(event.target.value))} className="mt-1 w-full" aria-label={`Time index for ${site.name}`} />
      </label>
      {data.hz ? <SkyView eph={data.eph} hz={data.hz} idx={i} /> : <p className="rounded border border-slate-800 bg-slate-900 p-2 text-xs text-amber-100">{data.terrainMessage ?? "Terrain profile unavailable; no visibility percentage is inferred."}</p>}
      {data.vis && <p className="text-sm text-slate-300">Window: Sun visible {percentage(data.vis.sun)}% · Earth visible {percentage(data.vis.earth)}% · both {percentage(both(data.vis.sun, data.vis.earth))}%</p>}
      {data.vis && data.terrainProvenance && <p className="text-xs text-slate-500">Visibility: {data.terrainProvenance}. Body-center rule; not a link-budget result.</p>}
    </article>
  );
}

function WhatChanged({ site, window }: { site: Site; window: UtcWindow }) {
  const data = useSiteData(site, window);
  const [fromDate, setFromDate] = useState("");
  const [slippedDate, setSlippedDate] = useState("");
  const [days, setDays] = useState(1);
  const stats = useMemo(() => {
    if (!data.eph || !data.vis) return null;
    const eph = data.eph;
    const start = Date.parse(eph.start_utc);
    const rangeStart = dayStr(start);
    const rangeEnd = dayStr(idxToMs(eph, nSteps(eph) - 1));
    const first = fromDate || rangeStart;
    const second = slippedDate || dayStr(start + 24 * 60 * 60 * 1000);
    const length = Math.floor((days * 1440) / eph.step_minutes);
    const index = (date: string) => Math.round((Date.parse(`${date}T00:00:00Z`) - start) / (eph.step_minutes * 60_000));
    const a = index(first), b = index(second);
    return { rangeStart, rangeEnd, first, second, A: windowStats(data.vis, a, a + length, eph.step_minutes), B: windowStats(data.vis, b, b + length, eph.step_minutes), clipped: a < 0 || b < 0 || a + length > nSteps(eph) || b + length > nSteps(eph) };
  }, [data.eph, data.vis, fromDate, slippedDate, days]);
  if (data.loading) return <p className="text-sm text-slate-400">Loading live terrain analysis…</p>;
  if (!stats) return <p className="rounded border border-amber-700 bg-amber-950/30 p-3 text-sm text-amber-100">Mission-slip comparison requires a complete backend terrain visibility response. It is not calculated from fixture data.</p>;
  const rows: [string, "sunH" | "earthH" | "bothH" | "longestDarkH"][] = [["Sunlit hours", "sunH"], ["Earth-visible hours", "earthH"], ["Sun AND Earth hours", "bothH"], ["Longest dark stretch (h)", "longestDarkH"]];
  return (
    <div className="space-y-3 rounded-lg border border-slate-700 bg-slate-900 p-3">
      <div className="flex flex-wrap gap-3 text-sm">
        <label>Original date (UTC) <input type="date" min={stats.rangeStart} max={stats.rangeEnd} value={stats.first} onChange={(event) => setFromDate(event.target.value)} className="rounded bg-slate-800 px-2 py-1" /></label>
        <label>Slipped date (UTC) <input type="date" min={stats.rangeStart} max={stats.rangeEnd} value={stats.second} onChange={(event) => setSlippedDate(event.target.value)} className="rounded bg-slate-800 px-2 py-1" /></label>
        <label>Mission window <select value={days} onChange={(event) => setDays(Number(event.target.value))} className="rounded bg-slate-800 px-2 py-1">{[1, 3, 7, 14].map((value) => <option value={value} key={value}>{value} day{value > 1 ? "s" : ""}</option>)}</select></label>
      </div>
      {stats.clipped && <p className="text-sm text-amber-300">Part of a window falls outside the requested data range; totals are truncated.</p>}
      <table className="w-full text-sm"><thead><tr className="text-left text-slate-400"><th>Metric</th><th>Original</th><th>Slipped</th><th>Change</th></tr></thead><tbody>{rows.map(([label, key]) => { const delta = stats.B[key] - stats.A[key]; return <tr key={key} className="border-t border-slate-800"><td className="py-1">{label}</td><td>{stats.A[key].toFixed(1)}</td><td>{stats.B[key].toFixed(1)}</td><td>{delta > 0 ? "+" : ""}{delta.toFixed(1)}</td></tr>; })}</tbody></table>
      <p className="text-xs text-slate-500">Computed from the live Horizons series and backend terrain-adjusted visibility; event durations are sample-dependent.</p>
    </div>
  );
}

export default function Compare() {
  const catalog = useSites();
  const all = catalog.data ?? [];
  const [picked, setPicked] = useState<string[] | null>(null);
  const [idx, setIdx] = useState(0);
  const [slipSiteId, setSlipSiteId] = useState<string | null>(null);
  const initial = useMemo(() => initialUtcStart(), []);
  const [date, setDate] = useState(initial.date);
  const [time, setTime] = useState(initial.time);
  const [days, setDays] = useState(7);
  const window = useMemo(() => makeUtcWindow(date, time, days), [date, time, days]);
  const selectedIds = (picked ?? all.slice(0, 2).map((site) => site.id)).filter((id) => all.some((site) => site.id === id));
  const selected = selectedIds.map((id) => all.find((site) => site.id === id)!).filter(Boolean);
  const toggle = (id: string) => {
    const next = selectedIds.includes(id) ? selectedIds.filter((value) => value !== id) : [...selectedIds, id].slice(-3);
    setPicked(next.length ? next : selectedIds);
  };
  const slipSite = all.find((site) => site.id === (slipSiteId ?? selected[0]?.id)) ?? null;

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Site comparison</h1>
      <p className="text-sm text-slate-400">Compare live Horizons positions for two or three candidate coordinates on the same UTC grid. Terrain-relative percentages appear only where the backend returns complete terrain visibility.</p>
      {catalog.error && <p role="alert" className="text-sm text-red-300">Could not load candidates: {catalog.error}</p>}
      <div className="flex flex-wrap gap-3 text-sm">
        {all.map((site) => <label key={site.id} className="flex items-center gap-1"><input type="checkbox" checked={selectedIds.includes(site.id)} onChange={() => toggle(site.id)} /> {site.name}</label>)}
        <span className="text-slate-500">(choose 2–3)</span>
      </div>
      <RequestControls date={date} time={time} days={days} onDate={(value) => value && setDate(value)} onTime={(value) => value && setTime(value)} onDays={setDays} />
      <div className="grid gap-4 lg:grid-cols-2">{selected.map((site) => <SiteColumn key={site.id} site={site} window={window} idx={idx} setIdx={setIdx} />)}</div>
      <section className="space-y-3">
        <h2 className="pt-2 text-xl font-semibold">What changed if the mission slips?</h2>
        <p className="text-sm text-slate-400">For a selected site, compare live terrain-relative daylight and Earth visibility over equal-length UTC windows. Requires actual backend terrain results.</p>
        {all.length > 0 && <select value={slipSite?.id ?? ""} onChange={(event) => setSlipSiteId(event.target.value)} className="rounded bg-slate-800 px-2 py-1 text-sm">{all.map((site) => <option key={site.id} value={site.id}>{site.name}</option>)}</select>}
        {slipSite && <WhatChanged key={slipSite.id} site={slipSite} window={window} />}
      </section>
    </div>
  );
}
