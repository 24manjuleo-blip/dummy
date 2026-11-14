#!/usr/bin/env python3
"""Validate and convert the official PDS3 LDEM_85S_40M product to a lunar GeoTIFF.

The output stores HEIGHT relative to the PDS reference sphere in metres (DN * 0.5),
not planetary radius (DN * 0.5 + OFFSET). This is intentionally product-specific.
"""
import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
import rasterio
from pyproj import CRS
from rasterio.transform import from_origin

EXPECTED={
    "DATA_SET_ID":"LRO-L-LOLA-4-GDR-V1.0",
    "LINES":"7584",
    "LINE_SAMPLES":"7584",
    "SAMPLE_TYPE":"LSB_INTEGER",
    "SAMPLE_BITS":"16",
    "RECORD_TYPE":"FIXED_LENGTH",
    "UNIT":"METER",
    "SCALING_FACTOR":"0.5",
    "OFFSET":"1737400.",
    "MAP_PROJECTION_TYPE":"POLAR STEREOGRAPHIC",
    "MAP_SCALE":"40 <m/pix>",
    "KEYWORD_LATITUDE_TYPE":"PLANETOCENTRIC",
    "A_AXIS_RADIUS":"1737.4 <km>",
    "B_AXIS_RADIUS":"1737.4 <km>",
    "C_AXIS_RADIUS":"1737.4 <km>",
    "CENTER_LATITUDE":"-90 <deg>",
    "CENTER_LONGITUDE":"0 <deg>",
    "POSITIVE_LONGITUDE_DIRECTION":"EAST",
    "MINIMUM_LATITUDE":"-90 <deg>",
    "MAXIMUM_LATITUDE":"-85 <deg>",
    "COORDINATE_SYSTEM_TYPE":"BODY-FIXED ROTATING",
    "COORDINATE_SYSTEM_NAME":"MEAN EARTH/POLAR AXIS OF DE421",
}
SOURCE_URL="https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/DATA/LOLA_GDR/polar/img/"
RADIUS_M=1_737_400.0

def parse_label(text):
    fields={}
    for line in text.splitlines():
        line=re.sub(r"/\*.*?\*/", "", line).strip()
        if not line or line.startswith("/*") or "=" not in line: continue
        key,value=line.split("=",1); key=key.strip().upper(); value=value.strip()
        if key in EXPECTED or key in {"RECORD_BYTES","FILE_RECORDS","DERIVED_MINIMUM","DERIVED_MAXIMUM","SAMPLE_PROJECTION_OFFSET","LINE_PROJECTION_OFFSET","MAP_SCALE","OFFSET","SCALING_FACTOR","LINE_SAMPLES","LINES","SAMPLE_BITS","SAMPLE_TYPE","UNIT","COORDINATE_SYSTEM_NAME","COORDINATE_SYSTEM_TYPE"}:
            fields[key]=value
    return fields

def normal(value):
    return value.strip().strip('"').upper()

def file_sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()

def validate_xml(xml_path,rows,cols):
    root=ET.parse(xml_path).getroot()
    def values(local):
        return [node.text.strip() for node in root.iter() if node.tag.rsplit("}",1)[-1]==local and node.text and node.text.strip()]
    checks={
        "file_name":"ldem_85s_40m.img", "data_type":"SignedLSB2", "unit":"METER",
        "scaling_factor":"0.5", "value_offset":"1737400.",
        "north_bounding_coordinate":"-85", "south_bounding_coordinate":"-90",
        "map_projection_name":"Polar Stereographic", "pixel_resolution_x":"40",
        "pixel_resolution_y":"40", "latitude_type":"Planetocentric",
        "coordinate_system_name":"MEAN EARTH/POLAR AXIS OF DE421",
        "upperleft_corner_x":"-151680.0", "upperleft_corner_y":"151680.0",
    }
    for key,wanted in checks.items():
        actual=values(key)
        if wanted not in actual:
            raise ValueError(f"PDS4 XML {key}={actual!r}; expected {wanted!r}")
    dims=[]
    axes=[]
    for axis in root.iter():
        if axis.tag.rsplit("}",1)[-1]=="Axis_Array":
            d={c.tag.rsplit("}",1)[-1]: (c.text or "").strip() for c in axis}
            axes.append((d.get("axis_name"),d.get("elements")))
    if sorted(int(n) for _,n in axes if n) != sorted([rows,cols]):
        raise ValueError(f"PDS4 XML axes {axes!r} do not match label dimensions {rows}x{cols}")
    description=" ".join(values("description"))
    if "HEIGHT = (DN * SCALING_FACTOR)" not in description or "PLANETARY_RADIUS = (DN * SCALING_FACTOR) + VALUE_OFFSET" not in description:
        raise ValueError("PDS4 XML does not distinguish relative HEIGHT from planetary radius as expected")
    return {"logical_identifier":next(iter(values("logical_identifier")),None),"scaling_factor":"0.5","value_offset_m":"1737400","body_fixed_frame":"MEAN EARTH/POLAR AXIS OF DE421","dimensions":axes}

def validate_and_convert(image_path,label_path,output_path,xml_path):
    image_path,label_path,output_path,xml_path=map(Path,(image_path,label_path,output_path,xml_path))
    text=label_path.read_text(errors="strict")
    fields=parse_label(text)
    for key,wanted in EXPECTED.items():
        actual=fields.get(key)
        if actual is None or normal(actual)!=normal(wanted):
            raise ValueError(f"PDS label {key}={actual!r}; expected {wanted!r}")
    if not re.search(r"HEIGHT\s*=\s*\(DN\s*\*\s*SCALING_FACTOR\)",text,re.I):
        raise ValueError("PDS label does not contain the expected HEIGHT=DN*SCALING_FACTOR formula")
    if not re.search(r"PLANETARY_RADIUS\s*=\s*\(DN\s*\*\s*SCALING_FACTOR\)\s*\+\s*OFFSET",text,re.I):
        raise ValueError("PDS label does not distinguish height from planetary radius as expected")
    rows,cols=int(fields["LINES"]),int(fields["LINE_SAMPLES"])
    xml_metadata=validate_xml(xml_path,rows,cols)
    if int(fields["RECORD_BYTES"]) != cols*2 or int(fields["FILE_RECORDS"]) != rows:
        raise ValueError("PDS3 record layout does not match the declared 16-bit image dimensions")
    if image_path.stat().st_size != rows*cols*2:
        raise ValueError(f"IMG size {image_path.stat().st_size} bytes does not match {rows}x{cols} signed 16-bit samples")
    raw=np.memmap(image_path,dtype="<i2",mode="r",shape=(rows,cols))
    raw_min,raw_max=int(raw.min()),int(raw.max())
    for key,actual in (("DERIVED_MINIMUM",raw_min),("DERIVED_MAXIMUM",raw_max)):
        if int(fields[key])!=actual:
            raise ValueError(f"PDS {key}={fields[key]} differs from actual IMG extrema {actual}")
    scale=float(fields["SCALING_FACTOR"])
    if scale != 0.5: raise ValueError("Unexpected height scale; refusing conversion")
    # The PDS comments explicitly define HEIGHT = DN * scaling factor.
    # OFFSET is added only to obtain planetary radius, not to the relative terrain HEIGHT.
    height=(np.asarray(raw,dtype=np.float32)*np.float32(scale))
    crs=CRS.from_proj4(f"+proj=stere +lat_0=-90 +lat_ts=-90 +lon_0=0 +a={RADIUS_M} +b={RADIUS_M} +units=m +no_defs +type=crs")
    scale_m=float(re.search(r"MAP_SCALE\s*=\s*([0-9.]+)",text,re.I).group(1))
    sample_offset=float(re.search(r"SAMPLE_PROJECTION_OFFSET\s*=\s*([0-9.]+)",text,re.I).group(1))
    line_offset=float(re.search(r"LINE_PROJECTION_OFFSET\s*=\s*([0-9.]+)",text,re.I).group(1))
    if not math.isclose(sample_offset,(cols-1)/2) or not math.isclose(line_offset,(rows-1)/2):
        raise ValueError("PDS3 pixel registration offsets do not align with symmetric pixel centers")
    transform=from_origin(-(cols*scale_m/2),(rows*scale_m/2),scale_m,scale_m)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with rasterio.open(output_path,"w",driver="GTiff",height=rows,width=cols,count=1,dtype="float32",crs=crs,transform=transform,compress="deflate",predictor=3,tiled=True) as dst:
        dst.write(height,1)
        dst.update_tags(1,product="LDEM_85S_40M",source_dataset=normal(fields["DATA_SET_ID"]),source_image=image_path.name,source_label=label_path.name,source_label_sha256=file_sha256(label_path),height_units="m",height_definition="DN * SCALING_FACTOR",scaling_factor=scale,planetary_radius_offset_m=RADIUS_M,vertical_reference="height relative to the 1,737,400 m reference sphere; no geoid correction applied",coordinate_frame=normal(fields["COORDINATE_SYSTEM_NAME"]),latitude_type="PLANETOCENTRIC",pixel_registration="as documented by PDS label",source_url=SOURCE_URL+image_path.name)
    with rasterio.open(output_path) as ds:
        bounds=[ds.bounds.left,ds.bounds.bottom,ds.bounds.right,ds.bounds.top]
        raster_info={"crs_wkt":ds.crs.to_wkt(),"resolution_m":list(ds.res),"bounds_m":bounds}
    return {"status":"LABEL_AND_IMG_VALIDATED","product":"LDEM_85S_40M","dataset_id":normal(fields["DATA_SET_ID"]),"image":str(image_path),"image_size_bytes":image_path.stat().st_size,"image_sha256":file_sha256(image_path),"label":str(label_path),"label_sha256":file_sha256(label_path),"pds4_label":str(xml_path),"pds4_label_sha256":file_sha256(xml_path),"pds4_metadata":xml_metadata,"dimensions":[rows,cols],"sample":"signed little-endian int16","raw_minmax_dn":[raw_min,raw_max],"height_minmax_m_relative_to_reference_sphere":[raw_min*scale,raw_max*scale],"height_scale_m_per_dn":scale,"height_formula":"HEIGHT_m = DN * 0.5; do NOT add OFFSET for height","planetary_radius_formula":"PLANETARY_RADIUS_m = DN * 0.5 + 1,737,400","vertical_reference":"relative to a 1,737,400 m reference sphere; not geoid-corrected topography","projection":"polar stereographic, spherical Moon; 40 m/pixel; planetocentric latitude; 85S to 90S","body_fixed_frame":normal(fields["COORDINATE_SYSTEM_NAME"]),"output_geotiff":str(output_path),"output_sha256":file_sha256(output_path),"geotiff":raster_info}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--img",default="data/lola/ldem_85s_40m.img")
    p.add_argument("--label",default="data/lola/ldem_85s_40m.lbl")
    p.add_argument("--xml",default="data/lola/ldem_85s_40m.xml")
    p.add_argument("--out",default="data/lola/ldem_85s_40m_height.tif")
    p.add_argument("--report",default="data/lola/ldem_85s_40m_validation.json")
    a=p.parse_args()
    report=validate_and_convert(a.img,a.label,a.out,a.xml)
    Path(a.report).write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__": main()
