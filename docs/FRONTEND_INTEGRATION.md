# Next.js frontend integration guide

## Repository review and compatibility boundary

The public repository was cloned read-only to inspect it. It is a Next.js 16 / React 19 static-style frontend using local JSON files through `lib/data.ts` and `lib/useSiteData.ts`. Its current contract is documented in the repository's `CONTRACT.md`: `sites.json`, parallel ephemeris arrays, `horizon/<id>.json` with a 360-value `elev_deg`, and summary text. Planner components `SiteChips`, `Cards`, `SkyView`, `TimeControls`, `Timeline`, `Heatmap`, and `MockBanner` consume that shape. The repository includes Planner, Compare, and About routes under `app/compare/page.tsx` and `app/about/page.tsx`. No changes to the repository are included in this package.

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in the frontend `.env.local` for local use. Do not expose secrets in `NEXT_PUBLIC_` variables. Set backend `LUNAR_CORS_ORIGINS` to the exact frontend origin.

## Endpoint-to-frontend mapping

- `/api/v1/nasa/horizons/ephemeris` supplies timestamped Sun/Earth named observer rows. The frontend currently expects parallel `sun_az`, `sun_el`, `earth_az`, `earth_el` arrays and `start_utc`/`step_minutes`. Build a client adapter that checks timestamp spacing and body IDs before transforming rows into those arrays; do not infer columns or label placeholder files live.
- `/api/v1/terrain/horizon` supplies `azimuth_deg[]` and `elevation_deg[]`. Convert to the existing `Horizon` contract only after verifying azimuth step is 1 degree and the output has 360 bins. Preserve DEM filename, source citation, mast and provenance in `dem_source` or adjacent metadata. For coarser steps, interpolate on client/server deliberately instead of passing an invalid shape. The endpoint does not accept file paths from the browser; approved DEM selection is server configuration only.
- `/api/v1/analysis/site-visibility` accepts ephemeris and horizon JSON, then returns terrain-adjusted booleans, event estimates and provenance. Its result does not currently exactly match `lib/events.ts`'s `Vis` array. Convert the sample booleans using the same aligned timestamps; the existing component event calculations remain useful locally.
- `/api/v1/analysis/site-comparison` is a server-side live evaluation and requires a configured DEM; calls without one return an explicit error.
- `/api/v1/nasa/moontrek/layers` fetches live capabilities for one verified sample layer. Construct the map tile request from the returned `ResourceURL` template and advertised metadata; do not generalize this sample to polar projections.
- `/api/v1/nasa/resources` supplies data-source links and QuickMap launch metadata.

## Existing code and offline behavior

Keep the existing dashboard, time controls, sky visualization, timeline, heatmap, and summary UX. Replace `public/data/ephemeris/<id>.json` with the adapted Horizons series and `public/data/horizon/<id>.json` with terrain only after a real configured DEM response succeeds. Keep `public/data/sites.json` as the curated location catalog unless the backend is explicitly extended to own it. Replace `public/data/summaries.json` only with text derived from numerical results; there is no summary-generation endpoint in this package. The TypeScript example [frontend-adapter.ts](frontend-adapter.ts) converts response shapes without altering the repo. Replace local public JSON only when a backend response for the matching site and time range has succeeded and has a live/computed provenance label. Retain local fixture fallback only if it remains visibly labeled **MOCK DATA** or **PRECOMPUTED DATA**. Do not silently swap to mock values after request errors.

Use loading skeletons or small status messages; display API validation/network failures without erasing the selected site. Keep last-known/cached responses only with their original timestamps and source state. For offline operation, label whether the shown response is cached or precomputed, and clearly state no live NASA fetch occurred. Resource/QuickMap links can remain independent of ephemeris status.

## Suggested adapter sequence

1. Load site selection and map catalog, retaining fallback status labels.
2. Request ephemeris for the selected site's UTC window, coordinate and interval.
3. Request terrain horizon only when a validated DEM is configured and the site falls inside its coverage. The current repository’s candidate sites are explicitly marked MOCK and include no coordinate-frame field; do not treat them as live sites or assign a frame by assumption. The deployment team must establish the intended site frame and verify that it exactly matches the selected DEM product frame before configuring either frame variable.
4. Join data by timestamp, not by assumed array length.
5. Derive visibility locally using the same azimuth interpolation rule or use API visibility output, but do not apply terrain twice.
6. Display geometric/apparent convention and terrain DEM provenance next to metrics.
7. For mission-delay comparison, rerun same site coordinates at shifted UTC windows, then compare timestamps/events with a consistent time grid.

CORS is restricted by backend configuration; do not set wildcard origins in deployment without an explicit security review. FastAPI interactive API docs are available at `/docs` and OpenAPI JSON at `/openapi.json`.
