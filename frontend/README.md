# Lunar Landing Site Navigator — Frontend

This is the original Next.js frontend adapted to connect to the FastAPI backend in the parent repository. The planner, site picker, UTC controls, sky-view component, visibility timeline, sunlight heatmap, comparison page, mission-slip workflow, and About/Method route are retained.

## Run locally

1. Start the backend from the repository root using its existing setup. The frontend's default API base is `http://127.0.0.1:8081`; set `LUNAR_CORS_ORIGINS` in the backend to the exact frontend origin, commonly `http://localhost:3000`.
2. In this directory, copy `.env.example` to `.env.local` if you need to override the default API address.
3. Install and run:

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. Run `npm test`, `npm run lint`, and `npm run build` for checks.

## Data and scientific limits

Horizons requests are sent to the backend for the selected catalog coordinates and requested UTC window. The supplied site catalog labels its coordinates as MOCK/unverified; a live response describes only the selected numeric coordinates and does not validate a candidate landing site. The application never substitutes bundled data after a request failure.

The UI calls the backend terrain and site-visibility endpoints only for the Shackleton Rim candidate. Terrain plots and visibility/event analyses are shown only when a complete, validated 360-bin one-degree horizon and timestamp-aligned backend visibility response are returned. Other candidates show live Horizons positions without inferred terrain visibility. The configured LOLA DEM covers 85°S–90°S; backend configuration, raster coverage, and body-fixed frame checks remain authoritative.

Sun and Earth values are Horizons airless apparent topocentric body-center angles. They do not include atmospheric refraction, full-disk visibility, or a complete communication link budget. Event estimates are interpolated between samples.

NASA Moon Trek and LROC QuickMap are linked directly. Their live headers currently block third-party iframe use; the app does not recreate or pretend to embed those sites.

## Structure

- `app/`: Planner, Compare, About / Method, and NASA Resources pages.
- `components/`: retained visualization and navigation components plus UTC request controls.
- `lib/api.ts`: API calls, response validation, and adapters into existing chart contracts.
- `lib/useSiteData.ts`: abortable site/time-window data hook.
- `public/data/sites.json`: original candidate catalog; entries remain visibly identified as mock/unverified.
- `public/data/ephemeris/` and `public/data/horizon/`: original fixtures retained for reference only; live UI does not load them.

No backend credentials or API keys are included in the browser bundle.
