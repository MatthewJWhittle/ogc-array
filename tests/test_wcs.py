"""
Tests for tilearray.ogc.wcs module.

Tests WCS parsing, client functionality, and tile adapter.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

import tilearray as ta
from tilearray.types import BoundingBox, CRS, Format, CoverageDescription, ServiceCapabilities, TileRequest, TileResponse, WCSResponse


class TestWCS:
    """Test WCS functionality."""
    
    def test_wcs_parser_basic(self):
        """Test basic WCS parsing functionality."""
        from tilearray.ogc.wcs import WCSParser
        
        parser = WCSParser()
        assert parser is not None
        
        print("✅ WCSParser created successfully")
    
    def test_wcs_client_basic(self):
        """Test basic WCS client functionality."""
        from tilearray.ogc.wcs import WCSClient
        
        client = WCSClient("http://test.com/wcs")
        assert client.base_url == "http://test.com/wcs"
        
        print("✅ WCSClient created successfully")
    
    def test_wcs_tile_adapter_basic(self):
        """Test basic WCS tile adapter functionality."""
        from tilearray.ogc.wcs import WCSTileAdapter
        
        adapter = WCSTileAdapter()
        assert adapter is not None
        
        print("✅ WCSTileAdapter created successfully")
    
    def test_wcs_tile_adapter_create_request(self):
        """Test WCS tile adapter request creation."""
        from tilearray.ogc.wcs import WCSTileAdapter
        
        adapter = WCSTileAdapter()
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        
        request = adapter.create_tile_request(
            service_url="http://test.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            width=256,
            height=256,
            output_format=Format.GEOTIFF,
            crs=CRS.EPSG_4326
        )
        
        assert isinstance(request, TileRequest)
        assert request.url == "http://test.com/wcs"
        assert "coverageId" in request.params
        assert request.params["coverageId"] == "test_coverage"
        assert request.params["width"] == "256"
        assert request.params["height"] == "256"
        
        print(f"✅ Created WCS tile request: {request}")
    
    def test_wcs_client_get_capabilities(self):
        """Test WCS client get capabilities."""
        from tilearray.ogc.wcs import WCSClient
        
        client = WCSClient("http://test.com/wcs")
        
        # Mock the HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"<test>capabilities</test>"
            mock_get.return_value = mock_response
            
            response = client.get_capabilities()
            
            assert isinstance(response, WCSResponse)
            assert response.status_code == 200
            assert response.data == b"<test>capabilities</test>"
            
            print(f"✅ WCS get capabilities: {response}")
    
    def test_wcs_client_describe_coverage(self):
        """Test WCS client describe coverage."""
        from tilearray.ogc.wcs import WCSClient
        
        client = WCSClient("http://test.com/wcs")
        
        # Mock the HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"<test>coverage description</test>"
            mock_get.return_value = mock_response
            
            response = client.describe_coverage("test_coverage")
            
            assert isinstance(response, WCSResponse)
            assert response.status_code == 200
            assert response.data == b"<test>coverage description</test>"
            
            print(f"✅ WCS describe coverage: {response}")
    
    def test_wcs_client_get_coverage(self):
        """Test WCS client get coverage."""
        from tilearray.ogc.wcs import WCSClient
        
        client = WCSClient("http://test.com/wcs")
        
        # Mock the HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"test image data"
            mock_get.return_value = mock_response
            
            response = client.get_coverage(
                coverage_id="test_coverage",
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                width=256,
                height=256,
                output_format=Format.GEOTIFF,
                crs=CRS.EPSG_4326
            )
            
            assert isinstance(response, TileResponse)
            assert response.status_code == 200
            assert response.data == b"test image data"
            
            print(f"✅ WCS get coverage: {response}")
    
    def test_wcs_parser_parse_capabilities(self):
        """Test WCS parser parse capabilities."""
        from tilearray.ogc.wcs import WCSParser
        
        parser = WCSParser()
        
        # Mock XML content
        xml_content = b"""
        <wcs:Capabilities xmlns:wcs="http://www.opengis.net/wcs/2.0">
            <ows:ServiceIdentification>
                <ows:Title>Test WCS Service</ows:Title>
            </ows:ServiceIdentification>
            <wcs:Contents>
                <wcs:CoverageSummary>
                    <wcs:CoverageId>test_coverage</wcs:CoverageId>
                    <ows:WGS84BoundingBox>
                        <ows:LowerCorner>0 0</ows:LowerCorner>
                        <ows:UpperCorner>10 10</ows:UpperCorner>
                    </ows:WGS84BoundingBox>
                </wcs:CoverageSummary>
            </wcs:Contents>
        </wcs:Capabilities>
        """
        
        capabilities = parser.parse_get_capabilities(xml_content)
        
        assert isinstance(capabilities, ServiceCapabilities)
        assert capabilities.title == "Test WCS Service"
        assert len(capabilities.coverages) == 1
        assert capabilities.coverages[0].identifier == "test_coverage"
        
        print(f"✅ Parsed WCS capabilities: {capabilities}")
    
    def test_wcs_parser_parse_describe_coverage(self):
        """Test WCS parser parse describe coverage."""
        from tilearray.ogc.wcs import WCSParser
        
        parser = WCSParser()
        
        # Mock XML content
        xml_content = b"""
        <wcs:CoverageDescription xmlns:wcs="http://www.opengis.net/wcs/2.0">
            <gml:identifier>test_coverage</gml:identifier>
            <gml:name>Test Coverage</gml:name>
            <wcs:domainSet>
                <gml:RectifiedGrid>
                    <gml:limits>
                        <gml:GridEnvelope>
                            <gml:low>0 0</gml:low>
                            <gml:high>100 100</gml:high>
                        </gml:GridEnvelope>
                    </gml:limits>
                </gml:RectifiedGrid>
            </wcs:domainSet>
        </wcs:CoverageDescription>
        """
        
        coverage = parser.parse_describe_coverage(xml_content)
        
        assert isinstance(coverage, CoverageDescription)
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        
        print(f"✅ Parsed WCS coverage description: {coverage}")
    
    def test_wcs_error_handling(self):
        """Test WCS error handling."""
        from tilearray.ogc.wcs import WCSClient
        
        client = WCSClient("http://test.com/wcs")
        
        # Test network error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            with pytest.raises(requests.RequestException, match="Network error"):
                client.get_capabilities()
            
            print("✅ WCS network error handling works correctly")
        
        # Test HTTP error
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.HTTPError("Server error")
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.HTTPError, match="Server error"):
                client.get_capabilities()
            
            print("✅ WCS HTTP error handling works correctly")
    
    def test_wcs_integration_basic(self):
        """Test basic WCS integration."""
        from tilearray.ogc.wcs import WCSClient, WCSParser, WCSTileAdapter
        
        # Test that all components work together
        client = WCSClient("http://test.com/wcs")
        parser = WCSParser()
        adapter = WCSTileAdapter()
        
        assert client is not None
        assert parser is not None
        assert adapter is not None
        
        print("✅ WCS integration components work together")
    
    def test_wcs_service_creation(self):
        """Test WCS service creation through public API."""
        service = ta.create_wcs_service(
            url="http://test.com/wcs",
            coverage_id="test_coverage",
            resolution=(256, 256),
            output_format="image/tiff",
            crs="EPSG:4326"
        )
        
        assert service["type"] == "WCS"
        assert service["url"] == "http://test.com/wcs"
        assert service["coverage_id"] == "test_coverage"
        assert service["resolution"] == (256, 256)
        assert service["format"] == "image/tiff"
        assert service["crs"] == "EPSG:4326"
        
        print(f"✅ Created WCS service: {service}")
