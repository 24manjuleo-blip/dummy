import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache
from .config import get_settings
from .schemas import EphemerisRequest,HorizonRequest,VisibilityRequest,CompareRequest
from .services.horizons import fetch_observer_ephemeris,HorizonsError
from .services.moontrek import get_catalog
from .services.terrain import compute_horizon,TerrainUnavailable
from .services.analysis import site_visibility
from .services.resources import resources

settings=get_settings(); logging.basicConfig(level=logging.INFO); log=logging.getLogger("lunar_navigator")
cache=TTLCache(maxsize=128,ttl=settings.cache_ttl_seconds)
app=FastAPI(title=settings.app_name,version="0.1.0",description="NASA-backed lunar ephemeris and DEM-terrain analysis. Terrain remains unavailable until an approved lunar-frame DEM is configured.")
app.add_middleware(CORSMiddleware,allow_origins=settings.cors_origin_list,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])
@app.get("/api/v1/health")
async def health():
    return {"status":"ok","services":{"horizons":"configured","moontrek":"capabilities fetched on demand","terrain":"configured" if settings.terrain_ready else "unavailable: approved DEM root, DEM file, and matching lunar frame IDs are required"}}
@app.get("/api/v1/nasa/resources")
async def nasa_resources(): return resources(settings)
@app.get("/api/v1/nasa/moontrek/layers")
async def moontrek_layers():
    try:return await get_catalog()
    except Exception as e: log.exception("Moon Trek capabilities failure"); raise HTTPException(502,f"Could not retrieve/parse NASA Moon Trek GetCapabilities: {e}")
@app.post("/api/v1/nasa/horizons/ephemeris")
async def horizons(req:EphemerisRequest):
    key="h:"+req.model_dump_json()
    if key in cache:return {**cache[key],"cache":"HIT"}
    try: result=await fetch_observer_ephemeris(req,settings); cache[key]=result; return {**result,"cache":"MISS"}
    except HorizonsError as e: log.warning("Horizons error: %s",e); raise HTTPException(502,str(e))
@app.post("/api/v1/terrain/horizon")
async def terrain(req:HorizonRequest):
    try:
        return compute_horizon(req.latitude_deg,req.longitude_deg,req.altitude_m,req.azimuth_step_deg,req.max_distance_m,req.mast_height_m,dem_path=settings.dem_path,approved_root=settings.dem_root,site_frame_id=settings.site_coordinate_frame_id,dem_frame_id=settings.dem_coordinate_frame_id,lunar_radius_m=settings.lunar_radius_m)
    except TerrainUnavailable as e: raise HTTPException(503,str(e))
    except Exception as e: log.exception("Terrain calculation failed"); raise HTTPException(422,f"DEM processing failed: {e}")
@app.post("/api/v1/analysis/site-visibility")
async def visibility(req:VisibilityRequest):
    try:return site_visibility(req.ephemeris,req.horizon)
    except (KeyError,TypeError,ValueError) as e: raise HTTPException(422,f"Invalid ephemeris or horizon contract: {e}")
@app.post("/api/v1/analysis/site-comparison")
async def compare(req:CompareRequest):
    results=[]
    for site in req.sites:
        try:
            eph=await fetch_observer_ephemeris(site,settings)
            h=compute_horizon(site.latitude_deg,site.longitude_deg,site.altitude_m,dem_path=settings.dem_path,approved_root=settings.dem_root,site_frame_id=settings.site_coordinate_frame_id,dem_frame_id=settings.dem_coordinate_frame_id,lunar_radius_m=settings.lunar_radius_m)
            results.append({"site_name":site.name,"latitude_deg":site.latitude_deg,"longitude_deg":site.longitude_deg,"visibility":site_visibility(eph,h)})
        except TerrainUnavailable as e: raise HTTPException(503,str(e))
        except Exception as e: log.exception("Comparison failed"); raise HTTPException(502,f"Comparison failed for {site.name or 'site'}: {e}")
    return {"sites":results,"provenance":"LIVE NASA ephemerides + configured approved lunar DEM; no precomputed/mock results"}
