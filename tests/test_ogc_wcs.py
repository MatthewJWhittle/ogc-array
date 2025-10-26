"""Tests for OGC WCS functionality."""

import pytest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch
from tilearray.ogc import WCSParser, WCSClient
from tilearray.types import (
    ServiceCapabilities, CoverageDescription, BoundingBox, SpatialExtent,
    CRS, Format, TileRequest, WCSResponse
)


class TestWCSParser:
    """Test WCS XML parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = WCSParser("http://example.com/wcs")
    
    def test_parse_get_capabilities_basic(self):
        """Test basic GetCapabilities parsing."""
        xml_content = """
        <wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"
                          xmlns:ows="http://www.opengis.net/ows/1.1">
            <ows:ServiceIdentification>
                <ows:Title>Test WCS Service</ows:Title>
                <ows:Abstract>A test WCS service</ows:Abstract>
            </ows:ServiceIdentification>
            <ows:ServiceProvider>
                <ows:ProviderName>Test Provider</ows:ProviderName>
            </ows:ServiceProvider>
            <ows:OperationsMetadata>
                <ows:Operation name="GetCapabilities">
                    <ows:DCP>
                        <ows:HTTP>
                            <ows:Get href="http://example.com/wcs"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
            </ows:OperationsMetadata>
        </wcs:Capabilities>
        """
        
        capabilities = self.parser.parse_get_capabilities(xml_content)
        
        assert capabilities.service_title == "Test WCS Service"
        assert capabilities.service_abstract == "A test WCS service"
        assert capabilities.service_provider == "Test Provider"
        assert capabilities.service_url == "http://example.com/wcs"
        assert "GetCapabilities" in capabilities.supported_operations
    
    def test_parse_get_capabilities_with_coverages(self):
        """Test GetCapabilities parsing with coverages."""
        xml_content = """
        <wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"
                          xmlns:ows="http://www.opengis.net/ows/1.1">
            <ows:ServiceIdentification>
                <ows:Title>Test WCS Service</ows:Title>
            </ows:ServiceIdentification>
            <ows:OperationsMetadata>
                <ows:Operation name="GetCapabilities">
                    <ows:DCP>
                        <ows:HTTP>
                            <ows:Get href="http://example.com/wcs"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
            </ows:OperationsMetadata>
            <wcs:Contents>
                <wcs:CoverageSummary>
                    <wcs:Identifier>test_coverage</wcs:Identifier>
                    <wcs:Title>Test Coverage</wcs:Title>
                    <wcs:Abstract>A test coverage</wcs:Abstract>
                    <ows:WGS84BoundingBox>
                        <ows:LowerCorner>0 0</ows:LowerCorner>
                        <ows:UpperCorner>10 10</ows:UpperCorner>
                    </ows:WGS84BoundingBox>
                </wcs:CoverageSummary>
            </wcs:Contents>
        </wcs:Capabilities>
        """
        
        capabilities = self.parser.parse_get_capabilities(xml_content)
        
        assert len(capabilities.coverages) == 1
        coverage = capabilities.coverages[0]
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        assert coverage.abstract == "A test coverage"
        assert coverage.spatial_extent.bbox.min_x == 0
        assert coverage.spatial_extent.bbox.min_y == 0
        assert coverage.spatial_extent.bbox.max_x == 10
        assert coverage.spatial_extent.bbox.max_y == 10
    
    def test_parse_describe_coverage_basic(self):
        """Test basic DescribeCoverage parsing."""
        xml_content = """
        <wcs:CoverageDescription xmlns:wcs="http://www.opengis.net/wcs/2.0"
                               xmlns:gml="http://www.opengis.net/gml/3.2">
            <wcs:CoverageId>test_coverage</wcs:CoverageId>
            <gml:name>Test Coverage</gml:name>
            <gml:description>A test coverage</gml:description>
            <gml:boundedBy>
                <gml:Envelope>
                    <gml:lowerCorner>0 0</gml:lowerCorner>
                    <gml:upperCorner>10 10</gml:upperCorner>
                </gml:Envelope>
            </gml:boundedBy>
        </wcs:CoverageDescription>
        """
        
        coverage = self.parser.parse_describe_coverage(xml_content)
        
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        assert coverage.abstract == "A test coverage"
        assert coverage.spatial_extent.bbox.min_x == 0
        assert coverage.spatial_extent.bbox.min_y == 0
        assert coverage.spatial_extent.bbox.max_x == 10
        assert coverage.spatial_extent.bbox.max_y == 10
    
    def test_parse_invalid_xml(self):
        """Test parsing invalid XML."""
        invalid_xml = "<invalid>xml<unclosed>"
        
        with pytest.raises(ValueError, match="Invalid XML content"):
            self.parser.parse_get_capabilities(invalid_xml)
    
    def test_parse_missing_elements(self):
        """Test parsing XML with missing elements."""
        xml_content = """
        <wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0">
        </wcs:Capabilities>
        """
        
        capabilities = self.parser.parse_get_capabilities(xml_content)
        
        assert capabilities.service_title == "WCS Service"  # Default
        assert capabilities.service_abstract is None
        assert capabilities.service_provider is None
        assert capabilities.service_url == "http://example.com/wcs"
        assert len(capabilities.coverages) == 0


class TestWCSClient:
    """Test WCS client functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = WCSClient("http://example.com/wcs")
    
    @patch('requests.Session.get')
    def test_get_capabilities_success(self, mock_get):
        """Test successful GetCapabilities request."""
        # Mock response
        mock_response = Mock()
        mock_response.text = """
        <wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0"
                          xmlns:ows="http://www.opengis.net/ows/1.1">
            <ows:ServiceIdentification>
                <ows:Title>Test WCS Service</ows:Title>
            </ows:ServiceIdentification>
            <ows:OperationsMetadata>
                <ows:Operation name="GetCapabilities">
                    <ows:DCP>
                        <ows:HTTP>
                            <ows:Get href="http://example.com/wcs"/>
                        </ows:HTTP>
                    </ows:DCP>
                </ows:Operation>
            </ows:OperationsMetadata>
        </wcs:Capabilities>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        capabilities = self.client.get_capabilities()
        
        assert capabilities.service_title == "Test WCS Service"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['service'] == 'WCS'
        assert call_args[1]['params']['version'] == '2.0.1'
        assert call_args[1]['params']['request'] == 'GetCapabilities'
    
    @patch('requests.Session.get')
    def test_describe_coverage_success(self, mock_get):
        """Test successful DescribeCoverage request."""
        # Mock response
        mock_response = Mock()
        mock_response.text = """
        <wcs:CoverageDescription xmlns:wcs="http://www.opengis.net/wcs/2.0"
                                 xmlns:gml="http://www.opengis.net/gml/3.2">
            <wcs:CoverageId>test_coverage</wcs:CoverageId>
            <gml:name>Test Coverage</gml:name>
            <gml:boundedBy>
                <gml:Envelope>
                    <gml:lowerCorner>0 0</gml:lowerCorner>
                    <gml:upperCorner>10 10</gml:upperCorner>
                </gml:Envelope>
            </gml:boundedBy>
        </wcs:CoverageDescription>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        coverage = self.client.describe_coverage("test_coverage")
        
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['service'] == 'WCS'
        assert call_args[1]['params']['version'] == '2.0.1'
        assert call_args[1]['params']['request'] == 'DescribeCoverage'
        assert call_args[1]['params']['coverageId'] == 'test_coverage'
    
    @patch('requests.Session.get')
    def test_get_coverage_success(self, mock_get):
        """Test successful GetCoverage request."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"test data"
        mock_response.headers = {
            'Content-Type': 'image/tiff',
            'Content-Length': '9'
        }
        mock_response.url = "http://example.com/wcs"
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        
        response = self.client.get_coverage(
            coverage_id="test_coverage",
            bbox=bbox,
            width=256,
            height=256
        )
        
        assert response.success is True
        assert response.data == b"test data"
        assert response.status_code == 200
        assert response.error_message is None
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['service'] == 'WCS'
        assert call_args[1]['params']['version'] == '2.0.1'
        assert call_args[1]['params']['request'] == 'GetCoverage'
        assert call_args[1]['params']['coverageId'] == 'test_coverage'
    
    @patch('requests.Session.get')
    def test_get_coverage_failure(self, mock_get):
        """Test failed GetCoverage request."""
        # Mock response with error
        mock_get.side_effect = Exception("Network error")
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        
        response = self.client.get_coverage(
            coverage_id="test_coverage",
            bbox=bbox,
            width=256,
            height=256
        )
        
        assert response.success is False
        assert "Network error" in response.error_message
        assert response.data is None


class TestWCSIntegration:
    """Integration tests for WCS functionality."""
    
    def test_wcs_tile_adapter(self):
        """Test WCS tile adapter parameter conversion."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        
        from tilearray.ogc import WCSTileAdapter
        tile_request = WCSTileAdapter.create_tile_request(
            base_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            width=256,
            height=256,
            output_format=Format.GEOTIFF,
            crs=CRS.EPSG_4326
        )
        
        assert tile_request.url == "http://example.com/wcs"
        assert tile_request.params["service"] == "WCS"
        assert tile_request.params["version"] == "2.0.1"
        assert tile_request.params["request"] == "GetCoverage"
        assert tile_request.params["coverageId"] == "test_coverage"
        assert tile_request.params["width"] == "256"
        assert tile_request.params["height"] == "256"
        assert tile_request.params["format"] == Format.GEOTIFF.value
        assert tile_request.output_format == Format.GEOTIFF
    
    def test_coverage_description_validation(self):
        """Test coverage description validation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        spatial_extent = SpatialExtent(bbox=bbox)
        
        coverage = CoverageDescription(
            identifier="test_coverage",
            title="Test Coverage",
            spatial_extent=spatial_extent,
            supported_formats=[Format.GEOTIFF, Format.NETCDF],
            supported_crs=[CRS.EPSG_4326, CRS.EPSG_3857]
        )
        
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        assert len(coverage.supported_formats) == 2
        assert Format.GEOTIFF in coverage.supported_formats
        assert Format.NETCDF in coverage.supported_formats
        assert len(coverage.supported_crs) == 2
        assert CRS.EPSG_4326 in coverage.supported_crs
        assert CRS.EPSG_3857 in coverage.supported_crs
