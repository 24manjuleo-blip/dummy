#!/usr/bin/env python3
"""Fetch one LOLA PDS raster and detached label; inspect metadata before processing.
Usage: python scripts/fetch_lola_product.py https://.../product.img --out data/raw
"""
import argparse, json, re
from pathlib import Path
from urllib.parse import urlparse
import httpx

def parse_label(text):
    # Lightweight PDS keyword reader for inventory only; product interpretation remains label-specific.
    keys=("DATA_SET_ID","PRODUCT_ID","PRODUCT_TYPE","LINES","LINE_SAMPLES","SAMPLE_BITS","SAMPLE_TYPE","MAP_PROJECTION_TYPE","CENTER_LATITUDE","CENTER_LONGITUDE","MINIMUM_LATITUDE","MAXIMUM_LATITUDE","WESTERNMOST_LONGITUDE","EASTERNMOST_LONGITUDE","SCALING_FACTOR","OFFSET","MAP_RESOLUTION","MAP_SCALE","A_AXIS_RADIUS","B_AXIS_RADIUS","C_AXIS_RADIUS","COORDINATE_SYSTEM_NAME")
    found={}
    for key in keys:
        m=re.search(r"^\s*"+key+r"\s*=\s*(.+?)\s*$",text,re.M|re.I)
        if m: found[key]=m.group(1).strip().strip('"')
    return found

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('--out',default='data/raw'); args=ap.parse_args()
    url=args.url
    if not url.lower().endswith('.img'): raise SystemExit('Supply a PDS IMG URL, not a browse image or unlabelled file.')
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True); name=Path(urlparse(url).path).name
    label_url=url[:-4]+'.lbl'
    with httpx.Client(timeout=180,follow_redirects=True) as client:
        for source,target in ((url,out/name),(label_url,out/(name[:-4]+'.lbl'))):
            r=client.get(source); r.raise_for_status(); target.write_bytes(r.content); print(f'Downloaded {source} ({len(r.content)} bytes)')
    label=(out/(name[:-4]+'.lbl')).read_text(errors='replace'); metadata=parse_label(label)
    report={"raster":name,"label":name[:-4]+'.lbl',"source_url":url,"metadata_inventory":metadata,"warning":"Do not interpret values or georeference until the full PDS label, attached SIS, units, scaling/offset, CRS, coverage, vertical datum, and byte order are reviewed. This script intentionally does not silently convert unknown detached-label rasters."}
    (out/(name+'.metadata.json')).write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
