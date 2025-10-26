"""Tests for OGC tile functionality."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os
import requests

from tilearray.tiles import (
    fetch_tile, save_tile, create_tile_grid_for_bbox, estimate_optimal_tile_size
)
from tilearray.types import BoundingBox, CRS, Format, TileRequest, TileResponse
from tilearray.ogc import WCSTileAdapter, WMSTileAdapter, WMTSAdapter


class TestTileRequest:
    """Test TileRequest dataclass."""
    
    def test_tile_request_creation(self):
        """Test creating a tile request."""
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"},
            headers={"Accept": "image/tiff"},
            timeout=30,
            retries=3
        )
        
        assert request.url == "http://example.com/wcs"
        assert request.params == {"service": "WCS", "request": "GetCoverage"}
        assert request.headers == {"Accept": "image/tiff"}
        assert request.timeout == 30
        assert request.retries == 3


class TestTileResponse:
    """Test TileResponse dataclass."""
    
    def test_successful_response(self):
        """Test successful tile response."""
        response = TileResponse(
            data=b"fake_tile_data",
            content_type="image/tiff",
            status_code=200,
            headers={"content-length": "100"},
            url="http://example.com/tile",
            success=True
        )
        
        assert response.data == b"fake_tile_data"
        assert response.content_type == "image/tiff"
        assert response.status_code == 200
        assert response.success is True
        assert response.error_message is None
    
    def test_failed_response(self):
        """Test failed tile response."""
        response = TileResponse(
            data=b"",
            content_type="",
            status_code=404,
            headers={},
            url="http://example.com/tile",
            success=False,
            error_message="Not found"
        )
        
        assert response.data == b""
        assert response.success is False
        assert response.error_message == "Not found"


class TestFetchTile:
    """Test fetch_tile function."""
    
    def test_fetch_tile_success(self):
        """Test successful tile fetch."""
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"}
        )
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"fake_tile_data"
        mock_response.headers = {"content-type": "image/tiff"}
        mock_response.url = "http://example.com/wcs?service=WCS&request=GetCoverage"
        
        with patch('requests.get', return_value=mock_response):
            response = fetch_tile(request)
            
            assert response.success is True
            assert response.data == b"fake_tile_data"
            assert response.content_type == "image/tiff"
            assert response.status_code == 200
    
    def test_fetch_tile_failure(self):
        """Test failed tile fetch."""
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"}
        )
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_response.headers = {}
        mock_response.url = "http://example.com/wcs?service=WCS&request=GetCoverage"
        
        with patch('requests.get', return_value=mock_response):
            response = fetch_tile(request)
            
            assert response.success is False
            assert response.status_code == 404
            assert "HTTP 404" in response.error_message
    
    def test_fetch_tile_network_error(self):
        """Test network error handling."""
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"},
            retries=0  # No retries to make test simpler
        )
        
        # Mock requests.get to raise a requests.RequestException
        mock_get = Mock(side_effect=requests.RequestException("Network error"))
        
        with patch('tilearray.tiles.requests.get', mock_get):
            response = fetch_tile(request)
            
            assert response.success is False
            assert "Network error" in response.error_message
    
    def test_fetch_tile_invalid_request(self):
        """Test invalid request parameters."""
        # Test missing URL
        with pytest.raises(ValueError, match="URL is required"):
            fetch_tile(TileRequest(url="", params={}))
        
        # Test missing params
        with pytest.raises(ValueError, match="Request parameters are required"):
            fetch_tile(TileRequest(url="http://example.com", params={}))


class TestSaveTile:
    """Test save_tile function."""
    
    def test_save_successful_tile(self):
        """Test saving a successful tile."""
        response = TileResponse(
            data=b"fake_tile_data",
            content_type="image/tiff",
            status_code=200,
            headers={},
            url="http://example.com/tile",
            success=True
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "tile.tiff"
            result = save_tile(response, output_path)
            
            assert result is True
            assert output_path.exists()
            assert output_path.read_bytes() == b"fake_tile_data"
    
    def test_save_failed_tile(self):
        """Test saving a failed tile."""
        response = TileResponse(
            data=b"",
            content_type="",
            status_code=404,
            headers={},
            url="http://example.com/tile",
            success=False,
            error_message="Not found"
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "tile.tiff"
            result = save_tile(response, output_path)
            
            assert result is False
            assert not output_path.exists()


class TestWCSTileAdapter:
    """Test WCS tile adapter."""
    
    def test_create_wcs_tile_request(self):
        """Test creating WCS tile request."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        
        request = WCSTileAdapter.create_tile_request(
            base_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            width=256,
            height=256,
            output_format=Format.GEOTIFF,
            crs=CRS.EPSG_4326
        )
        
        assert request.url == "http://example.com/wcs"
        assert request.params["service"] == "WCS"
        assert request.params["request"] == "GetCoverage"
        assert request.params["coverageId"] == "test_coverage"
        assert request.params["width"] == "256"
        assert request.params["height"] == "256"
        assert request.params["format"] == "image/tiff"
        assert "subset" in request.params
        assert request.output_format == Format.GEOTIFF
        assert request.crs == CRS.EPSG_4326
    
    def test_create_wcs_tile_request_with_additional_params(self):
        """Test WCS request with additional parameters."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        
        request = WCSTileAdapter.create_tile_request(
            base_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            version="2.0.1",
            custom_param="value"
        )
        
        assert request.params["version"] == "2.0.1"
        assert request.params["custom_param"] == "value"


class TestWMSTileAdapter:
    """Test WMS tile adapter."""
    
    def test_create_wms_tile_request(self):
        """Test creating WMS tile request."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        
        request = WMSTileAdapter.create_tile_request(
            base_url="http://example.com/wms",
            layers="test_layer",
            bbox=bbox,
            width=256,
            height=256,
            output_format=Format.GEOTIFF
        )
        
        assert request.url == "http://example.com/wms"
        assert request.params["service"] == "WMS"
        assert request.params["request"] == "GetMap"
        assert request.params["layers"] == "test_layer"
        assert request.params["width"] == 256
        assert request.params["height"] == 256
        assert request.params["format"] == "image/tiff"
        assert "bbox" in request.params
        assert request.output_format == Format.GEOTIFF
    
    def test_create_wms_tile_request_multiple_layers(self):
        """Test WMS request with multiple layers."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        
        request = WMSTileAdapter.create_tile_request(
            base_url="http://example.com/wms",
            layers=["layer1", "layer2"],
            bbox=bbox
        )
        
        assert request.params["layers"] == "layer1,layer2"


class TestWMTSAdapter:
    """Test WMTS adapter."""
    
    def test_create_wmts_tile_request(self):
        """Test creating WMTS tile request."""
        request = WMTSAdapter.create_tile_request(
            base_url="http://example.com/wmts",
            layer="test_layer",
            tile_matrix_set="test_matrix_set",
            tile_matrix="0",
            tile_row=0,
            tile_col=0,
            output_format=Format.GEOTIFF
        )
        
        assert request.url == "http://example.com/wmts"
        assert request.params["service"] == "WMTS"
        assert request.params["request"] == "GetTile"
        assert request.params["layer"] == "test_layer"
        assert request.params["tilematrixset"] == "test_matrix_set"
        assert request.params["tilematrix"] == "0"
        assert request.params["tilerow"] == 0
        assert request.params["tilecol"] == 0
        assert request.params["format"] == "image/tiff"
        assert request.output_format == Format.GEOTIFF


class TestTileGridUtilities:
    """Test tile grid utility functions."""
    
    def test_create_tile_grid_for_bbox(self):
        """Test creating tile grid for bounding box."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        tiles = create_tile_grid_for_bbox(bbox, tile_size=5.0)
        
        assert len(tiles) == 4  # 2x2 grid
        assert tiles[0].min_x == 0
        assert tiles[0].min_y == 0
        assert tiles[0].max_x == 5
        assert tiles[0].max_y == 5
    
    def test_estimate_optimal_tile_size(self):
        """Test estimating optimal tile size."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        tile_size = estimate_optimal_tile_size(bbox, target_pixels=100)
        
        assert tile_size > 0
        assert tile_size <= 1.0
