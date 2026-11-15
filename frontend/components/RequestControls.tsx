"use client";
import type { UtcWindow } from "@/lib/api";

export function initialUtcStart() {
  const now = new Date();
  now.setUTCMinutes(0, 0, 0);
  return { date: now.toISOString().slice(0, 10), time: now.toISOString().slice(11, 16) };
}

export function makeUtcWindow(date: string, time: string, days: number): UtcWindow {
  const start = new Date(`${date}T${time}:00Z`);
  const stop = new Date(start.getTime() + days * 24 * 60 * 60 * 1000);
  return { startUtc: start.toISOString(), stopUtc: stop.toISOString(), stepMinutes: 60 };
}

export default function RequestControls({ date, time, days, onDate, onTime, onDays }: {
  date: string; time: string; days: number;
  onDate: (value: string) => void; onTime: (value: string) => void; onDays: (value: number) => void;
}) {
  return (
    <section className="rounded-lg border border-slate-700 bg-slate-900 p-3" aria-label="Horizons request window">
      <h2 className="font-semibold">Live analysis window</h2>
      <p className="mb-3 text-xs text-slate-400">UTC only · Horizons sample interval 60 minutes. Changing these values requests fresh backend data.</p>
      <div className="flex flex-wrap items-end gap-3 text-sm">
        <label className="grid gap-1 text-slate-300">Start date (UTC)
          <input type="date" value={date} onChange={(event) => onDate(event.target.value)} className="rounded bg-slate-800 px-2 py-1" />
        </label>
        <label className="grid gap-1 text-slate-300">Start time (UTC)
          <input type="time" value={time} onChange={(event) => onTime(event.target.value)} className="rounded bg-slate-800 px-2 py-1" />
        </label>
        <label className="grid gap-1 text-slate-300">Window
          <select value={days} onChange={(event) => onDays(Number(event.target.value))} className="rounded bg-slate-800 px-2 py-1">
            {[1, 3, 7, 14, 30].map((value) => <option key={value} value={value}>{value} day{value > 1 ? "s" : ""}</option>)}
          </select>
        </label>
      </div>
    </section>
  );
}
