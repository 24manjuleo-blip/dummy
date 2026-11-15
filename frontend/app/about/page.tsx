export default function About() {
  return (
    <article className="space-y-4 text-sm leading-relaxed text-slate-300">
      <h1 className="text-2xl font-bold text-slate-100">About / Method</h1>
      <p>This central planner connects official lunar mapping tools with a FastAPI service for live NASA/JPL Horizons ephemerides and, when configured and supported, a local terrain-horizon calculation. It is a prototype decision-support aid, not a flight-certified system and not endorsed by NASA.</p>
      <h2 className="text-lg font-semibold text-slate-100">Sources and provenance</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Sun and Earth azimuth/elevation: live observer ephemeris requested from NASA/JPL Horizons through the project backend. The app displays response cache status and UTC timestamps.</li>
        <li>Terrain horizon: computed by the backend from its server-configured, approved LOLA DEM only when complete coverage and matching lunar coordinate-frame checks succeed. The browser cannot choose a DEM file.</li>
        <li>NASA Moon Trek and LROC QuickMap are the actual external mapping interfaces. Their current response headers restrict third-party iframe embedding, so the app links to the official sites instead of pretending to embed them.</li>
        <li>Candidate names and coordinates in the supplied frontend catalog are marked MOCK / unverified; live Horizons values describe only those entered coordinates and do not validate a landing site.</li>
      </ul>
      <h2 className="text-lg font-semibold text-slate-100">Method</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>Horizons returns airless apparent topocentric body-center azimuth/elevation for the selected coordinate and UTC time grid.</li>
        <li>Where the backend supplies a complete 360-bin, one-degree DEM horizon, terrain visibility uses the backend&apos;s result: body-center elevation greater than the interpolated terrain horizon at that azimuth.</li>
        <li>Rise/set events are linearly interpolated between requested samples and are approximate; reported windows are bounded by the requested time interval.</li>
      </ul>
      <h2 className="text-lg font-semibold text-slate-100">Scientific limits</h2>
      <ul className="list-disc space-y-1 pl-5">
        <li>The current LOLA DEM covers 85°S–90°S and terrain calculations are restricted to the supported Shackleton Rim site; no terrain visibility is inferred elsewhere.</li>
        <li>Visibility uses the center of the Sun or Earth, not the full solar or Earth disk. Atmospheric refraction is not modeled.</li>
        <li>Earth visibility is not a communication link budget. No link margin, antenna pointing, occultation by other bodies, or operational readiness is implied.</li>
        <li>DEM resolution, frame alignment, vertical reference, and coordinate provenance bound terrain conclusions. Missing or incomplete data is reported as unavailable, never clear sky.</li>
        <li>Verify all outputs against mission-grade sources before operational use.</li>
      </ul>
    </article>
  );
}
