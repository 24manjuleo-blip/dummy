# NASA and lunar data-source verification

## JPL Horizons

The documented GET endpoint is `https://ssd.jpl.nasa.gov/api/horizons.api`. It returns a JSON wrapper whose `result` is Horizons formatted text. The API documentation warns of HTTP-200 payload errors; code checks both. A live observer request was performed on 2026-11-15 and confirmed the response's named column is `Azimuth__(a-app)__Elevation`, with airless apparent topocentric angles and azimuth clockwise from north. The implementation explicitly requests quantity 4 and rejects unnamed columns. Data limits and model coverage remain determined by request/output and Horizons documentation.

## Moon Trek WMTS

NASA documents WMTS. Verified live capabilities URL: `https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/WMTSCapabilities.xml`. Its exact sample identifiers include layer `LRO_WAC_Mosaic_Global_303ppd_v02`, style `default`, matrix set `default028mm`, CRS `urn:ogc:def:crs:EPSG::104903`, bounds −180..180 by −90..90, `image/jpeg`, extension `.jpg`, and matrices 0–8 with 256×256 tiles. The runtime API reparses the source metadata. The sample is not evidence that other layers have identical settings.

The NASA API configuration advertises CRS identifiers for equirectangular `urn:ogc:def:crs:EPSG::104903`, north polar `urn:ogc:def:crs:IAU2000::30118`, and south polar `urn:ogc:def:crs:IAU2000::30120`. Polar product metadata was not verified, so no polar tile template is supplied.

## QuickMap

The requested QuickMap host redirects to `https://quickmap.lroc.im-ldi.com/`. The observed live response sets `X-Frame-Options: sameorigin` and CSP `frame-ancestors 'self'`; use an external launch link, not an iframe. No stable public raster/tile API was verified. LROC terms distinguish PDS products from non-PDS interface imagery; check attribution and usage terms for imagery used beyond external linking.

## LOLA PDS Geosciences

Verified PDS archive root: `https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/`; the downloaded `LDEM_85S_40M` label identifies `LRO-L-LOLA-4-GDR-V1.0`. Its PDS3 detached label and PDS4 XML are included with the 115,034,112-byte IMG under `data/lola/`. The label gives 7,584×7,584 samples, signed 16-bit little-endian integers, 40 m/pixel polar stereographic coverage from 85°S to the south pole, planetocentric latitude, east-positive longitude, and body-fixed `MEAN EARTH/POLAR AXIS OF DE421`. The label explicitly distinguishes relative height `DN × SCALING_FACTOR` from planetary radius `DN × SCALING_FACTOR + OFFSET`; its factor is 0.5 m/DN and offset is the 1,737,400 m reference-sphere radius. The product is not geoid-corrected. The included product-specific converter verifies label dimensions and actual raw DN extrema before producing a GeoTIFF. An examined `LDAC_10` count grid is not an elevation model and must not be used as terrain. PGDA product 78 has high-resolution site-specific derived GeoTIFFs, but the product selected here is the labeled PDS raster.

The Geosciences mirror is updated periodically; the LOLA page directs users to the LOLA Data Node/ODE for the latest release. Dataset examples and limitations are recorded in the README and scientific assumptions document.

## PGDA

PGDA is a dataset catalog with published file URLs, not a general spatial-query API in the pages reviewed. Verified product-page examples: ID 54 SLDEM2015; ID 69 Lunar Polar Illumination; ID 95 LOLA MOON_PA gridded data. Product 95 distinguishes `MOON_PA DE421` from `MOON_ME`; product page reports a material frame shift. Product 69 says zoomed-out COG overview values are averages, and different polar resolutions/projections are listed by coverage. Do not infer registration, frame, nodata, or coverage from a page ID alone.

## Sources

- [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [JPL Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
- [NASA Moon Trek API documentation](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=moon)
- [Verified Moon Trek sample WMTS capabilities](https://trek.nasa.gov/tiles/Moon/EQ/LRO_WAC_Mosaic_Global_303ppd_v02/1.0.0/WMTSCapabilities.xml)
- [LROC QuickMap](https://quickmap.lroc.asu.edu/)
- [LROC QuickMap help](https://quickmap.lroc.im-ldi.com/help)
- [LROC terms](https://lroc.im-ldi.com/about/terms)
- [PDS Geosciences LOLA archive](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)
- [PDS LOLA polar IMG directory](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/DATA/LOLA_GDR/polar/img/)
- [LDEM_85S_40M detached label](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/DATA/LOLA_GDR/polar/img/ldem_85s_40m.lbl)
- [LOLA GDRDEM product documentation](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/LOLA/GDR/GDRDEM.htm)
- [LOLA FAQ](https://pds-geosciences.wustl.edu/missions/lro/lola_faq.htm)
- [NASA PGDA](https://pgda.gsfc.nasa.gov/)
- [PGDA SLDEM2015 product 54](https://pgda.gsfc.nasa.gov/products/54)
- [PGDA Lunar Polar Illumination product 69](https://pgda.gsfc.nasa.gov/products/69)
- [PGDA LOLA MOON_PA product 95](https://pgda.gsfc.nasa.gov/products/95)
