import httpx
from defusedxml import ElementTree as ET

SAMPLE_CAPABILITIES = "https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/WMTSCapabilities.xml"

def parse_capabilities(xml: bytes, source_url: str) -> list[dict]:
    root=ET.fromstring(xml); ns={"ows":"http://www.opengis.net/ows/1.1","wmts":"http://www.opengis.net/wmts/1.0"}
    matrices={}
    for s in root.findall(".//wmts:TileMatrixSet",ns):
        ident=s.findtext("ows:Identifier",namespaces=ns); crs=s.findtext("ows:SupportedCRS",namespaces=ns)
        if ident: matrices[ident]={"crs":crs,"matrices":[m.findtext("ows:Identifier",namespaces=ns) for m in s.findall("wmts:TileMatrix",ns)]}
    result=[]
    for layer in root.findall(".//wmts:Layer",ns):
        ident=layer.findtext("ows:Identifier",namespaces=ns); title=layer.findtext("ows:Title",namespaces=ns)
        resources=[{"format":r.get("format"),"resource_type":r.get("resourceType"),"template":r.get("template")} for r in layer.findall("wmts:ResourceURL",ns)]
        links=[]
        for link in layer.findall("wmts:TileMatrixSetLink",ns):
            mid=link.findtext("wmts:TileMatrixSet",namespaces=ns)
            links.append({"tile_matrix_set":mid,"metadata":matrices.get(mid)})
        bbox=[]
        for b in layer.findall("ows:WGS84BoundingBox",ns): bbox.append({"lower":b.findtext("ows:LowerCorner",namespaces=ns),"upper":b.findtext("ows:UpperCorner",namespaces=ns)})
        result.append({"id":ident,"title":title,"formats":[f.text for f in layer.findall("wmts:Format",ns)],"styles":[{"id":s.findtext("ows:Identifier",namespaces=ns),"is_default":s.get("isDefault")} for s in layer.findall("wmts:Style",ns)],"tile_matrix_sets":links,"wgs84_bounds":bbox,"resource_urls":resources,"resource_template":next((r["template"] for r in resources if r.get("resource_type")=="tile"),None),"capabilities_url":source_url,"provenance":"NASA Moon Trek WMTS GetCapabilities"})
    return result

async def get_layer_capabilities(url: str):
    async with httpx.AsyncClient(timeout=35,follow_redirects=True) as client:
        r=await client.get(url); r.raise_for_status()
        if "xml" not in r.headers.get("content-type"," ").lower() and not r.content.lstrip().startswith(b"<?xml"): raise RuntimeError("Capabilities endpoint did not return XML")
        return parse_capabilities(r.content,str(r.url))

async def get_catalog():
    return {"status":"verified_sample_only","sample_capabilities_url":SAMPLE_CAPABILITIES,"layers":await get_layer_capabilities(SAMPLE_CAPABILITIES),"projection_crs_identifiers":{"equirectangular":"urn:ogc:def:crs:EPSG::104903","north_pole":"urn:ogc:def:crs:IAU2000::30118","south_pole":"urn:ogc:def:crs:IAU2000::30120"},"note":"Tile URL templates are returned live from each layer's WMTS ResourceURL in GetCapabilities; no static tile URL fallback is used. Only the sample equirectangular layer capabilities are verified/configured. Query further products' own GetCapabilities before enabling them; polar CRS identifiers alone do not identify product coverage."}
