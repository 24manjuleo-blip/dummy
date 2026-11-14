from app.services.moontrek import parse_capabilities

XML_TEMPLATE=b'''<?xml version="1.0"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1">
  <Contents>
    <Layer>
      <ows:Identifier>live-layer</ows:Identifier>
      <ows:Title>Live layer</ows:Title>
      <ows:WGS84BoundingBox><ows:LowerCorner>-180 -90</ows:LowerCorner><ows:UpperCorner>180 90</ows:UpperCorner></ows:WGS84BoundingBox>
      <ows:Identifier>live-layer</ows:Identifier>
      <Format>image/png</Format>
      <Style isDefault="true"><ows:Identifier>live-style</ows:Identifier></Style>
      <TileMatrixSetLink><TileMatrixSet>live-matrix</TileMatrixSet></TileMatrixSetLink>
      <ResourceURL format="image/png" resourceType="tile" template="https://tiles.example.test/new-path/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png"/>
      <ResourceURL format="application/json" resourceType="FeatureInfo" template="https://tiles.example.test/info/{TileMatrix}/{TileRow}/{TileCol}.json"/>
    </Layer>
    <TileMatrixSet>
      <ows:Identifier>live-matrix</ows:Identifier><ows:SupportedCRS>urn:example:moon:crs</ows:SupportedCRS>
      <TileMatrix><ows:Identifier>zoom-0</ows:Identifier></TileMatrix>
    </TileMatrixSet>
  </Contents>
</Capabilities>'''

def test_resource_templates_are_taken_verbatim_from_capabilities():
    layers=parse_capabilities(XML_TEMPLATE,"https://capabilities.example.test/WMTS.xml")
    assert len(layers)==1
    layer=layers[0]
    assert layer["resource_template"]=="https://tiles.example.test/new-path/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png"
    assert layer["resource_urls"][1]["template"]=="https://tiles.example.test/info/{TileMatrix}/{TileRow}/{TileCol}.json"
    assert layer["tile_matrix_sets"][0]["tile_matrix_set"]=="live-matrix"
    assert layer["tile_matrix_sets"][0]["metadata"]["matrices"]==["zoom-0"]

def test_missing_resource_url_never_falls_back_to_a_hardcoded_template():
    xml=XML_TEMPLATE.replace(b'<ResourceURL format="image/png" resourceType="tile" template="https://tiles.example.test/new-path/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.png"/>',b'')
    layer=parse_capabilities(xml,"https://capabilities.example.test/WMTS.xml")[0]
    assert layer["resource_template"] is None
    assert layer["resource_urls"][0]["resource_type"]=="FeatureInfo"
