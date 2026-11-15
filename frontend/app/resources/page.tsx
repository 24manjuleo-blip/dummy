"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";

const officialLinks = [
  { name: "NASA Moon Trek", url: "https://trek.nasa.gov/moon/", purpose: "NASA's lunar mapping and terrain visualization website." },
  { name: "LROC QuickMap", url: "https://quickmap.lroc.asu.edu/", purpose: "The actual LROC lunar imagery and interactive map interface." },
  { name: "NASA/JPL Horizons", url: "https://ssd.jpl.nasa.gov/horizons/", purpose: "Official JPL ephemeris system; this application requests observer AZ/EL through the project backend." },
  { name: "LRO LOLA PDS Geosciences archive", url: "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/", purpose: "Planetary Data System archive for LRO LOLA products." },
  { name: "NASA PGDA", url: "https://pgda.gsfc.nasa.gov/", purpose: "NASA Planetary Geodesy and Cartography Working Group data archive." },
];

type ResourceResponse = { items: { name: string; url: string; kind: string; provenance: string }[] };
type HealthResponse = { status: string; services: Record<string, string> };
type MoonTrekResponse = { status: string; sample_capabilities_url: string; layers: { id: string; title: string; provenance: string; resource_template?: string }[]; note: string };

export default function Resources() {
  const [resources, setResources] = useState<ResourceResponse>();
  const [health, setHealth] = useState<HealthResponse>();
  const [moonTrek, setMoonTrek] = useState<MoonTrekResponse>();
  const [layerError, setLayerError] = useState<string>();
  const [error, setError] = useState<string>();
  useEffect(() => {
    let active = true;
    Promise.allSettled([apiGet<ResourceResponse>("/api/v1/nasa/resources"), apiGet<HealthResponse>("/api/v1/health"), apiGet<MoonTrekResponse>("/api/v1/nasa/moontrek/layers")]).then((results) => {
      if (!active) return;
      if (results[0].status === "fulfilled") setResources(results[0].value);
      else setError(results[0].reason instanceof Error ? results[0].reason.message : String(results[0].reason));
      if (results[1].status === "fulfilled") setHealth(results[1].value);
      if (results[2].status === "fulfilled") setMoonTrek(results[2].value);
      else setLayerError(results[2].reason instanceof Error ? results[2].reason.message : String(results[2].reason));
    });
    return () => { active = false; };
  }, []);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold">NASA resources</h1>
        <p className="mt-1 text-sm text-slate-400">A central launch point for official maps, data archives, and backend-connected science services. Mapping remains on the source websites.</p>
      </header>
      <section className="rounded-md border border-slate-700 bg-slate-900 p-3 text-sm">
        <h2 className="font-semibold">Embedding status</h2>
        <p className="mt-1 text-slate-300">Moon Trek currently sends an X-Frame-Options / Content-Security-Policy frame restriction. QuickMap redirects to its official host and sends same-origin-only frame policy. Neither can be embedded in this application without bypassing the source site&apos;s controls, so these links open the official tools directly.</p>
      </section>
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Official tools and data sources</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {officialLinks.map((item) => (
            <a key={item.name} href={item.url} target="_blank" rel="noreferrer" className="rounded-lg border border-slate-700 bg-slate-900 p-4 hover:border-sky-500">
              <span className="font-medium text-sky-300">{item.name} ↗</span>
              <p className="mt-1 text-sm text-slate-400">{item.purpose}</p>
              <span className="mt-2 block break-all text-xs text-slate-500">{item.url}</span>
            </a>
          ))}
        </div>
      </section>
      <section className="space-y-2">
        <h2 className="text-lg font-semibold">Backend resource catalog</h2>
        {error && <p role="status" className="rounded border border-amber-700 bg-amber-950/30 p-3 text-sm text-amber-100">Backend resource catalog unavailable: {error}. Official links above remain available.</p>}
        {resources?.items.map((item) => (
          <div key={`${item.name}:${item.url}`} className="flex flex-col justify-between gap-2 rounded border border-slate-800 bg-slate-950 p-3 text-sm sm:flex-row">
            <div><div className="font-medium">{item.name}</div><div className="text-xs text-slate-400">{item.kind} · {item.provenance}</div></div>
            <a href={item.url} target="_blank" rel="noreferrer" className="break-all text-sky-300 underline">Open source ↗</a>
          </div>
        ))}
        {!resources && !error && <p className="text-sm text-slate-400">Loading backend catalog…</p>}
      </section>
      <section className="space-y-2 rounded-md border border-slate-700 bg-slate-900 p-3 text-sm">
        <h2 className="font-semibold">Moon Trek WMTS capabilities</h2>
        {moonTrek ? <>
          <p className="text-slate-300">Catalog status: {moonTrek.status}. This is a verified sample layer, not a general Moon Trek map embed.</p>
          <a className="break-all text-sky-300 underline" href={moonTrek.sample_capabilities_url} target="_blank" rel="noreferrer">Open capabilities document ↗</a>
          {moonTrek.layers.map((layer) => <div key={layer.id} className="rounded border border-slate-700 bg-slate-950 p-2"><div className="font-medium">{layer.title}</div><div className="text-xs text-slate-400">{layer.id} · {layer.provenance}</div>{layer.resource_template && <p className="mt-1 break-all text-xs text-slate-500">Advertised tile template: {layer.resource_template}</p>}</div>)}
          <p className="text-xs text-slate-400">{moonTrek.note}</p>
        </> : layerError ? <p className="text-amber-200">Live layer catalog unavailable: {layerError}. Use the direct Moon Trek website above.</p> : <p className="text-slate-400">Loading live layer capabilities…</p>}
      </section>
      <section className="rounded-md border border-slate-700 bg-slate-900 p-3 text-sm">
        <h2 className="font-semibold">Backend status</h2>
        {health ? <><p className="mt-1 text-emerald-300">{health.status}</p><dl className="mt-2 grid gap-1 sm:grid-cols-2">{Object.entries(health.services).map(([name, status]) => <div key={name}><dt className="inline font-medium">{name}: </dt><dd className="inline text-slate-400">{status}</dd></div>)}</dl></> : <p className="mt-1 text-slate-400">Status not available.</p>}
      </section>
      <Link href="/" className="inline-block text-sky-300 underline">Return to mission planner</Link>
    </div>
  );
}
