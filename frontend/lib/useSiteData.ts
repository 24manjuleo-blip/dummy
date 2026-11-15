"use client";
import { useEffect, useState } from "react";
import { loadLiveSiteData, loadSites, type SiteData, type UtcWindow } from "./api";
import type { Site } from "./data";

export function useSites() {
  const [state, setState] = useState<{ data?: Site[]; error?: string; loading: boolean }>({ loading: true });
  useEffect(() => {
    let alive = true;
    loadSites().then(
      (data) => alive && setState({ data, loading: false }),
      (error) => alive && setState({ error: error instanceof Error ? error.message : String(error), loading: false }),
    );
    return () => { alive = false; };
  }, []);
  return state;
}

export function useSiteData(site: Site | null, window: UtcWindow) {
  const key = site ? `${site.id}:${window.startUtc}:${window.stopUtc}:${window.stepMinutes}` : null;
  const [state, setState] = useState<{ key: string | null; data?: SiteData; error?: string }>({ key: null });
  useEffect(() => {
    if (!site || !key) return;
    const controller = new AbortController();
    loadLiveSiteData(site, window, controller.signal).then(
      (data) => setState({ key, data }),
      (error) => {
        if (!controller.signal.aborted) setState({ key, error: error instanceof Error ? error.message : String(error) });
      },
    );
    return () => controller.abort();
  }, [key, site, window]);
  const ready = key !== null && state.key === key;
  return {
    eph: ready ? state.data?.eph : undefined,
    hz: ready ? state.data?.hz : undefined,
    vis: ready ? state.data?.vis : undefined,
    terrainMessage: ready ? state.data?.terrainMessage : undefined,
    terrainProvenance: ready ? state.data?.terrainProvenance : undefined,
    terrainMetadata: ready ? state.data?.terrainMetadata : undefined,
    cache: ready ? state.data?.cache : undefined,
    error: ready ? state.error : undefined,
    loading: key !== null && !ready,
  };
}
