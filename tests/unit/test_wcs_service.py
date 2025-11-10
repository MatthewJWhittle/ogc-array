import numpy as np
import pytest
import requests

from tilearray.service.base import TileGeometry
from tilearray.service.config import WCSConfig
from tilearray.service.wcs import WCSParser, WCSService
from tilearray.types import BoundingBox, CRS, Format


def test_wcs_parser_parses_capabilities_example():
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"
                  xmlns:ows="http://www.opengis.net/ows/1.1"
                  version="2.0.1">
    <ows:ServiceIdentification>
        <ows:Title>Example Service</ows:Title>
        <ows:Abstract>Sample abstract</ows:Abstract>
    </ows:ServiceIdentification>
    <wcs:Contents>
        <wcs:CoverageSummary>
            <wcs:CoverageId>coverage-1</wcs:CoverageId>
        </wcs:CoverageSummary>
    </wcs:Contents>
    <wcs:SupportedFormat>image/tiff</wcs:SupportedFormat>
    <wcs:SupportedCRS>EPSG:4326</wcs:SupportedCRS>
</wcs:Capabilities>"""

    parser = WCSParser("http://example.com/wcs")
    capabilities = parser.parse_get_capabilities(xml)

    assert capabilities.service_title == "Example Service"
    assert capabilities.supported_formats == [Format.GEOTIFF]
    assert capabilities.supported_crs == [CRS.EPSG_4326]
    assert capabilities.coverages[0].identifier == "coverage-1"


def test_wcs_service_build_tile_request():
    service = WCSService(
        "http://example.com/wcs",
        coverage_id="coverage-1",
        output_format=Format.GEOTIFF,
        crs=CRS.EPSG_4326,
    )

    geometry = TileGeometry(
        bbox=BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326),
        width=256,
        height=256,
        crs=CRS.EPSG_4326,
    )

    request = service.build_tile_request(geometry)

    assert request.params["coverageId"] == "coverage-1"
    assert request.params["width"] == "256"
    assert request.params["height"] == "256"
    subset_params = request.params["subset"]
    assert isinstance(subset_params, list)
    assert any(part.startswith("Long(") for part in subset_params)
    assert any(part.startswith("Lat(") for part in subset_params)
    assert request.output_format == Format.GEOTIFF
    assert request.crs == CRS.EPSG_4326
    assert request.bbox == geometry.bbox


def test_wcs_service_requires_coverage_id():
    service = WCSService("http://example.com/wcs")
    geometry = TileGeometry(
        bbox=BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326),
        width=16,
        height=16,
        crs=CRS.EPSG_4326,
    )

    with pytest.raises(ValueError):
        service.build_tile_request(geometry)


def test_wcs_plan_tiles_with_resolution():
    service = WCSService(
        "http://example.com/wcs",
        coverage_id="coverage-1",
        output_format=Format.GEOTIFF,
        crs=CRS.EPSG_4326,
    )
    bbox = BoundingBox(min_x=0, min_y=0, max_x=1000, max_y=1000, crs=CRS.EPSG_4326)

    tiles = list(service.plan_tiles(bbox, (500, 500), resolution=(1.0, 1.0)))
    assert len(tiles) == 4
    assert {tile.width for tile in tiles} == {500}
    assert {tile.height for tile in tiles} == {500}


def test_wcs_config_build_service_raises_for_missing_coverage(monkeypatch):
    config = WCSConfig.from_url("http://example.com/wcs", coverage_id="missing")

    def fake_describe(self, coverage_id=None, **params):
        raise requests.HTTPError("not found")

    monkeypatch.setattr(WCSService, "describe_coverage", fake_describe)

    with pytest.raises(ValueError, match="missing"):
        config.build_service()
