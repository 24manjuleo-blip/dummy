from .moontrek import SAMPLE_CAPABILITIES

def resources(settings):
    return {"items":[{"name":"JPL Horizons API","url":settings.horizons_url,"kind":"LIVE EPHEMERIS API","provenance":"NASA/JPL"},{"name":"Moon Trek WMTS capabilities (verified sample)","url":SAMPLE_CAPABILITIES,"kind":"LIVE WMTS","provenance":"NASA Moon Trek"},{"name":"LRO LOLA PDS Geosciences archive","url":"https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/","kind":"PDS FILE ARCHIVE","provenance":"NASA PDS Geosciences Node"},{"name":"NASA PGDA","url":"https://pgda.gsfc.nasa.gov/","kind":"DATA CATALOG AND PUBLISHED FILE LINKS","provenance":"NASA GSFC"},{"name":"LROC QuickMap","url":settings.quickmap_url,"kind":"EXTERNAL VISUALIZATION; IFRAME BLOCKED","provenance":"LROC / Arizona State University"}]}
