import math
from datetime import datetime, timezone

def horizon_at(horizon, az):
    step=horizon["azimuth_step_deg"]; values=horizon["elevation_deg"]
    a=(az%360)/step; i=int(math.floor(a)); f=a-i; j=(i+1)%len(values)
    return values[i]*(1-f)+values[j]*f

def _parse_time(row):
    value=row.get("time_utc")
    if not value: return None
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)

def event_summary(rows):
    """Estimate terrain-relative crossings and duration windows by linear interpolation."""
    if len(rows)<2: return {"windows":[],"crossings":[],"continuous_sunlight_max_minutes":None,"continuous_darkness_max_minutes":None}
    values=[r["elevation_deg"]-r["terrain_horizon_elevation_deg"] for r in rows]
    times=[_parse_time(r) for r in rows]
    if any(t is None for t in times): return {"windows":[],"crossings":[],"continuous_sunlight_max_minutes":None,"continuous_darkness_max_minutes":None,"note":"Rows lack timestamps; events cannot be determined"}
    transitions={}; crossings=[]
    for i in range(1,len(rows)):
        left,right=values[i-1],values[i]
        if (left>0)!=(right>0):
            frac=abs(left)/(abs(left)+abs(right)) if (abs(left)+abs(right)) else .5
            when=times[i-1]+(times[i]-times[i-1])*frac
            rising=right>0; transitions[i]=when
            crossings.append({"time_utc":when.isoformat().replace("+00:00","Z"),"event":"terrain-relative rise" if rising else "terrain-relative set","interpolation":"linear between samples"})
    visible=[v>0 for v in values]
    def windows_for(mask):
        found=[]; start=None
        for i,on in enumerate(mask):
            if on and start is None: start=times[0] if i==0 else transitions.get(i,times[i])
            if not on and start is not None:
                stop=transitions.get(i,times[i])
                found.append({"start_utc":start.isoformat().replace("+00:00","Z"),"end_utc":stop.isoformat().replace("+00:00","Z"),"duration_minutes":max(0,(stop-start).total_seconds()/60)})
                start=None
        if start is not None:
            stop=times[-1]
            found.append({"start_utc":start.isoformat().replace("+00:00","Z"),"end_utc":stop.isoformat().replace("+00:00","Z"),"duration_minutes":max(0,(stop-start).total_seconds()/60)})
        return found
    sun_windows=windows_for(visible); dark_windows=windows_for([not v for v in visible])
    return {"windows":sun_windows,"crossings":crossings,"continuous_sunlight_max_minutes":max((w["duration_minutes"] for w in sun_windows),default=0.0),"continuous_darkness_max_minutes":max((w["duration_minutes"] for w in dark_windows),default=0.0),"window_is_truncated_at_request_bounds":True,"sampling_interval_minutes":(times[1]-times[0]).total_seconds()/60}

def site_visibility(ephemeris, horizon):
    targets=ephemeris["targets"]
    out={}
    for target,data in targets.items():
        rows=[]
        for row in data["rows"]:
            alt=row["elevation_deg"]; az=row["azimuth_deg"]; terrain=horizon_at(horizon,az)
            rows.append({**row,"terrain_horizon_elevation_deg":terrain,"terrain_adjusted_visible":alt>terrain,"elevation_type":"airless apparent topocentric center elevation returned by Horizons observer table quantity 4","terrain_offset_deg":alt-terrain})
        out[target]={"samples":rows,"events":event_summary(rows)}
    return {"results":out,"provenance":{"ephemeris":"LIVE NASA JPL HORIZONS response","terrain":"Computed DEM horizon supplied by request","visibility_rule":"body center elevation > linearly interpolated local terrain horizon at azimuth","limitation":"Bodies are point centers; no angular size or local sub-pixel terrain uncertainties are modeled. Events and durations are linearly interpolated between requested samples; report sampling interval and truncation."}}

def summarize_sites(site_results):
    return {"sites":[{"name":s.get("site_name"),"latitude_deg":s.get("latitude_deg"),"longitude_deg":s.get("longitude_deg"),"visibility":s.get("visibility")} for s in site_results],"note":"Comparison is deterministic and uses supplied analysis; values remain tagged by provenance."}
