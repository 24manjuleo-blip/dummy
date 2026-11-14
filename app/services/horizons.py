import re
from datetime import timezone
import httpx

class HorizonsError(RuntimeError): pass

def _utc(value):
    return value.astimezone(timezone.utc).strftime("%Y-%b-%d %H:%M")

def parse_observer_table(text: str) -> list[dict]:
    """Parse observer rows only after the output explicitly names AZ/EL columns."""
    match = re.search(r"\$\$SOE\s*(.*?)\s*\$\$EOE", text, re.S)
    if not match: raise HorizonsError("Horizons response contains no observer data block ($$SOE/$$EOE)")
    preamble = text[:match.start()]
    if not re.search(r"Azimuth__.*?Elevation", preamble, re.I | re.S):
        raise HorizonsError("Horizons response does not identify the expected azimuth/elevation columns")
    # Horizons observer rows begin with calendar date and time, may include presence flags,
    # then give named table values in header order. Quantity 4 is the only requested quantity.
    row_re = re.compile(r"^\s*(\d{4}-[A-Za-z]{3}-\d{2})\s+(\d{2}:\d{2})\s+(?:[ *i]{0,2}\s+)?([-+]?\d+(?:\.\d*)?)\s+([-+]?\d+(?:\.\d*)?)\s*$")
    out=[]
    for row in match.group(1).strip().splitlines():
        m=row_re.match(row)
        if not m: continue
        date_iso=__import__("datetime").datetime.strptime(m.group(1), "%Y-%b-%d").strftime("%Y-%m-%d")
        out.append({"time_utc":date_iso+"T"+m.group(2)+":00Z","azimuth_deg":float(m.group(3)),"elevation_deg":float(m.group(4))})
    if not out: raise HorizonsError("Could not parse numeric AZ/EL rows from the documented observer table")
    return out

async def fetch_observer_ephemeris(req, settings):
    results={}
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        for target in req.targets:
            params={"format":"json","COMMAND":f"'{target}'","OBJ_DATA":"NO","MAKE_EPHEM":"YES","EPHEM_TYPE":"OBSERVER","CENTER":"coord@301","COORD_TYPE":"GEODETIC","SITE_COORD":f"{req.longitude_deg},{req.latitude_deg},{req.altitude_m/1000}","START_TIME":f"'{_utc(req.start_utc)}'","STOP_TIME":f"'{_utc(req.stop_utc)}'","STEP_SIZE":f"'{req.step_minutes} m'","QUANTITIES":"'4'","ANG_FORMAT":"DEG","EXTRA_PREC":"YES"}
            try:
                response=await client.get(settings.horizons_url,params=params); response.raise_for_status(); payload=response.json()
            except (httpx.HTTPError, ValueError) as exc: raise HorizonsError(f"Horizons request failed for target {target}: {exc}") from exc
            if payload.get("error"): raise HorizonsError(f"Horizons rejected target {target}: {payload['error']}")
            if not isinstance(payload.get("result"),str): raise HorizonsError(f"Horizons response for target {target} has no result text")
            results[str(target)]={"rows":parse_observer_table(payload["result"]),"source":"LIVE NASA JPL HORIZONS","target_id":str(target),"raw_signature":payload.get("signature")}
    return {"site":req.model_dump(mode="json"),"start_utc":req.start_utc.isoformat(),"stop_utc":req.stop_utc.isoformat(),"step_minutes":req.step_minutes,"coordinate_convention":"Horizons observer table quantity 4 returns airless apparent topocentric AZ/EL; geometric elevation is not separately computed; atmospheric refraction is not applied; terrain obstruction is not included","targets":results}
