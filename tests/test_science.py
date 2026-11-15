import pytest
from app.services.horizons import parse_observer_table, HorizonsError
from app.services.analysis import horizon_at, site_visibility

SAMPLE='''Date__(UT)__HR:MN     Azimuth__(a-app)__Elevation\n$$SOE\n 2026-Nov-15 00:00  i   91.710071449 -24.422309707\n 2026-Nov-15 01:00      92.0 1.0\n$$EOE\n'''
def test_parse_named_horizons_az_el_columns():
    rows=parse_observer_table(SAMPLE)
    assert len(rows)==2 and rows[0]['azimuth_deg']==pytest.approx(91.710071449)
    assert rows[0]['elevation_deg']==pytest.approx(-24.422309707)
    assert rows[0]['time_utc']=='2026-11-15T00:00:00Z'
def test_refuse_unknown_table_columns():
    with pytest.raises(HorizonsError): parse_observer_table('Date and altitude\n$$SOE\n2026-Nov-15 blah\n$$EOE')
def test_horizon_interpolation_wraps_azimuth():
    h={'azimuth_step_deg':90,'elevation_deg':[0,10,20,30]}
    assert horizon_at(h,45)==pytest.approx(5)
    assert horizon_at(h,359)==pytest.approx(0.3333333,rel=1e-5)
def test_visibility_compares_ephemeris_to_terrain_separately():
    e={'targets':{'10':{'rows':[{'azimuth_deg':0,'elevation_deg':6},{'azimuth_deg':180,'elevation_deg':2}]}}}
    h={'azimuth_step_deg':90,'elevation_deg':[5,0,3,0]}
    result=site_visibility(e,h)['results']['10']['samples']
    assert result[0]['terrain_adjusted_visible'] is True
    assert result[1]['terrain_adjusted_visible'] is False

def test_crossing_and_durations_are_interpolated_and_truncated():
    from app.services.analysis import event_summary
    rows=[]
    for hour, elevation in enumerate([1, -1, -1, 1]):
        rows.append({'time_utc':f'2026-11-15T0{hour}:00:00Z','elevation_deg':elevation,'terrain_horizon_elevation_deg':0})
    result=event_summary(rows)
    assert result['crossings'][0]['time_utc']=='2026-11-15T00:30:00Z'
    assert result['crossings'][1]['time_utc']=='2026-11-15T02:30:00Z'
    assert result['continuous_darkness_max_minutes']==pytest.approx(120)
    assert result['window_is_truncated_at_request_bounds'] is True

def test_pds_label_inventory_extracts_keywords_without_guessing():
    from scripts.fetch_lola_product import parse_label
    data=parse_label('DATA_SET_ID = LRO-L-LOLA-4-GDR-V1.0\nSAMPLE_BITS = 16\nLINES = 1800\n')
    assert data['DATA_SET_ID']=='LRO-L-LOLA-4-GDR-V1.0'
    assert data['SAMPLE_BITS']=='16'

def test_lunar_crs_rejects_earth_epsg4326():
    from pyproj import CRS
    from app.services.terrain import validate_lunar_crs, TerrainUnavailable
    with pytest.raises(TerrainUnavailable, match='EPSG:4326'):
        validate_lunar_crs(CRS.from_epsg(4326), 'MOON_ME_DE421', 'MOON_ME_DE421', 1737400.0)

def test_lunar_crs_requires_matching_frame_and_moon_radius():
    from pyproj import CRS
    from app.services.terrain import validate_lunar_crs, TerrainUnavailable, lunar_geographic_crs
    moon_crs=lunar_geographic_crs(1737400.0)
    with pytest.raises(TerrainUnavailable, match='does not match'):
        validate_lunar_crs(moon_crs, 'MOON_ME_DE421', 'MOON_PA_DE421', 1737400.0)
    transformer=validate_lunar_crs(moon_crs, 'MOON_ME_DE421', 'MOON_ME_DE421', 1737400.0)
    assert transformer.transform(23.47, 0.67)==pytest.approx((23.47,0.67))
    with pytest.raises(TerrainUnavailable, match='radius'):
        validate_lunar_crs(CRS.from_epsg(3857), 'MOON_ME_DE421', 'MOON_ME_DE421', 1737400.0)

def test_dem_path_requires_allowlisted_root(tmp_path):
    from app.services.terrain import resolve_approved_dem, TerrainUnavailable
    approved=tmp_path/'approved'; approved.mkdir()
    inside=approved/'terrain.tif'; inside.write_text('test')
    outside=tmp_path/'other.tif'; outside.write_text('test')
    assert resolve_approved_dem(str(inside),str(approved))==inside.resolve()
    with pytest.raises(TerrainUnavailable, match='outside'):
        resolve_approved_dem(str(outside),str(approved))

def test_api_rejects_client_dem_path_and_reports_terrain_unavailable(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main

    monkeypatch.setattr(main.settings, "dem_path", None)
    monkeypatch.setattr(main.settings, "dem_root", None)
    client = TestClient(main.app)

    response = client.post(
        "/api/v1/terrain/horizon",
        json={"latitude_deg": -89.9, "longitude_deg": 0, "dem_path": "/etc/passwd"},
    )
    assert response.status_code == 422

    unavailable = client.post(
        "/api/v1/terrain/horizon",
        json={"latitude_deg": -89.9, "longitude_deg": 0},
    )
    assert unavailable.status_code == 503
