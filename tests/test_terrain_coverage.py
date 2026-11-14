import math
import numpy as np
import pytest
import rasterio
from pyproj import CRS, Transformer
from rasterio.transform import from_origin
from app.services.terrain import compute_horizon, IncompleteDEMCoverage

RADIUS=1_737_400.0
FRAME="MOON_ME_DE421"

def make_dem(path, *, nodata=-9999.0):
    polar=CRS.from_proj4(f"+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +a={RADIUS} +b={RADIUS} +units=m +no_defs")
    geographic=CRS.from_proj4(f"+proj=longlat +a={RADIUS} +b={RADIUS} +no_defs +type=crs")
    transform=from_origin(-1000,1000,10,10)
    data=np.zeros((201,201),dtype="float32")
    with rasterio.open(path,"w",driver="GTiff",height=201,width=201,count=1,dtype="float32",crs=polar,transform=transform,nodata=nodata) as ds:
        ds.write(data,1)
    lat,lon=-89.99,0.0
    return polar,geographic,transform,lat,lon

def test_horizon_reports_incomplete_dem_bounds_instead_of_skipping(tmp_path):
    dem=tmp_path/"small.tif"
    make_dem(dem)
    with pytest.raises(IncompleteDEMCoverage,match="coverage is incomplete"):
        compute_horizon(-89.99,0,azimuth_step_deg=1,max_distance_m=1500,dem_path=dem,approved_root=tmp_path,site_frame_id=FRAME,dem_frame_id=FRAME)

def test_horizon_reports_nodata_ray_sample_instead_of_skipping(tmp_path):
    dem=tmp_path/"hole.tif"
    polar,geographic,transform,lat,lon=make_dem(dem)
    radius=RADIUS
    az=90.0; distance=25.0; angular=distance/radius
    lat2=math.asin(math.sin(math.radians(lat))*math.cos(angular)+math.cos(math.radians(lat))*math.sin(angular)*math.cos(math.radians(az)))
    lon2=math.radians(lon)+math.atan2(math.sin(math.radians(az))*math.sin(angular)*math.cos(math.radians(lat)),math.cos(angular)-math.sin(math.radians(lat))*math.sin(lat2))
    x,y=Transformer.from_crs(geographic,polar,always_xy=True).transform(math.degrees(lon2),math.degrees(lat2))
    with rasterio.open(dem,"r+") as ds:
        row,col=ds.index(x,y)
        ds.write(np.array([[-9999.0]],dtype="float32"),1,window=((row,row+1),(col,col+1)))
    with pytest.raises(IncompleteDEMCoverage,match="masked/nodata elevation"):
        compute_horizon(lat,lon,azimuth_step_deg=1,max_distance_m=100,dem_path=dem,approved_root=tmp_path,site_frame_id=FRAME,dem_frame_id=FRAME)

def test_horizon_reports_complete_coverage_when_all_rays_are_valid(tmp_path):
    dem=tmp_path/"complete.tif"
    make_dem(dem)
    result=compute_horizon(-89.99,0,azimuth_step_deg=1,max_distance_m=100,dem_path=dem,approved_root=tmp_path,site_frame_id=FRAME,dem_frame_id=FRAME)
    assert len(result["elevation_deg"])==360
    assert result["coverage"]=="complete for all requested samples through max_distance_m"
    assert result["ray_step_m"]==25
