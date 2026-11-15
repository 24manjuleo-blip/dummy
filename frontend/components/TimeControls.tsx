"use client";
import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import type { Ephemeris } from "@/lib/data";
import { nextTransition, type Vis } from "@/lib/events";
import { dayStr, fmtUTC, idxToMs, msToIdx, nSteps } from "@/lib/time";

type Props = { eph: Ephemeris; vis?: Vis; idx: number; setIdx: Dispatch<SetStateAction<number>> };

export default function TimeControls({ eph, vis, idx, setIdx }: Props) {
  const n = nSteps(eph);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => setIdx((i) => (i + 1 >= n ? 0 : i + 1)), 500);
    return () => clearInterval(timer);
  }, [playing, n, setIdx]);

  const ms = idxToMs(eph, idx);
  const onDate = (value: string) => {
    if (!value) return;
    const hh = String(new Date(ms).getUTCHours()).padStart(2, "0");
    setIdx(msToIdx(eph, Date.parse(`${value}T${hh}:00:00Z`)));
  };
  const jump = (body: "sun" | "earth", target: boolean, label: string) => {
    const next = vis ? nextTransition(vis[body], idx, target) : null;
    return (
      <button key={label} disabled={next === null} onClick={() => next !== null && setIdx(next)}
        className="rounded-md border border-slate-600 px-2 py-1 text-sm hover:bg-slate-800 disabled:opacity-40">
        {label}
      </button>
    );
  };

  return (
    <div className="space-y-3 rounded-lg border border-slate-700 bg-slate-900 p-3">
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-300">
          Display date (UTC) {" "}
          <input type="date" value={dayStr(ms)} min={dayStr(idxToMs(eph, 0))} max={dayStr(idxToMs(eph, n - 1))}
            onChange={(event) => onDate(event.target.value)} className="rounded bg-slate-800 px-2 py-1" />
        </label>
        <button onClick={() => setPlaying((value) => !value)} className="rounded-md bg-sky-700 px-3 py-1 text-sm font-medium hover:bg-sky-600">
          {playing ? "Pause" : "Play"}
        </button>
        <span className="font-mono text-sm text-slate-200">{fmtUTC(ms)}</span>
        {!vis && <span className="text-xs text-amber-200">Transition buttons require terrain visibility data.</span>}
      </div>
      <input type="range" min={0} max={n - 1} value={idx} onChange={(event) => setIdx(Number(event.target.value))}
        className="w-full" aria-label="UTC time scrubber" />
      <div className="flex flex-wrap gap-2">
        {jump("sun", true, "Next sunrise")}
        {jump("sun", false, "Next sunset")}
        {jump("earth", true, "Next Earthrise")}
        {jump("earth", false, "Next Earthset")}
      </div>
    </div>
  );
}
