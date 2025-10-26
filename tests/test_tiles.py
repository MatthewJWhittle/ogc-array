"""
Tests for tilearray.tiles module.

Tests generic tile fetching functionality.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

import tilearray as ta
from tilearray.types import BoundingBox, CRS, Format, TileRequest, TileResponse


class TestTiles:
    """Test tile functionality."""
    
    def test_fetch_tile_success(self):
        """Test successful tile fetching."""
        from tilearray.tiles import fetch_tile
        
        # Mock the HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"test image data"
            mock_response.headers = {"Content-Type": "image/tiff"}
            mock_get.return_value = mock_response
            
            request = TileRequest(
                url="http://test.com/tile",
                params={"param1": "value1"},
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                format=Format.GEOTIFF
            )
            
            response = fetch_tile(request)
            
            assert isinstance(response, TileResponse)
            assert response.status_code == 200
            assert response.data == b"test image data"
            assert response.content_type == "image/tiff"
            
            print(f"✅ Fetched tile successfully: {response}")
    
    def test_fetch_tile_network_error(self):
        """Test tile fetching with network error."""
        from tilearray.tiles import fetch_tile
        
        # Mock the HTTP request to raise network error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Network error")
            
            request = TileRequest(
                url="http://test.com/tile",
                params={"param1": "value1"},
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                format=Format.GEOTIFF
            )
            
            with pytest.raises(requests.RequestException, match="Network error"):
                fetch_tile(request)
            
            print("✅ Network error handling works correctly")
    
    def test_fetch_tile_http_error(self):
        """Test tile fetching with HTTP error."""
        from tilearray.tiles import fetch_tile
        
        # Mock the HTTP request to raise HTTP error
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError("Not found")
            mock_get.return_value = mock_response
            
            request = TileRequest(
                url="http://test.com/tile",
                params={"param1": "value1"},
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                format=Format.GEOTIFF
            )
            
            with pytest.raises(requests.HTTPError, match="Not found"):
                fetch_tile(request)
            
            print("✅ HTTP error handling works correctly")
    
    def test_fetch_tile_retry_logic(self):
        """Test tile fetching retry logic."""
        from tilearray.tiles import fetch_tile
        
        # Mock the HTTP request to fail first, then succeed
        with patch('requests.get') as mock_get:
            # First call fails, second call succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 500
            mock_response_fail.raise_for_status.side_effect = requests.HTTPError("Server error")
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.content = b"test image data"
            mock_response_success.headers = {"Content-Type": "image/tiff"}
            
            mock_get.side_effect = [mock_response_fail, mock_response_success]
            
            request = TileRequest(
                url="http://test.com/tile",
                params={"param1": "value1"},
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                format=Format.GEOTIFF
            )
            
            response = fetch_tile(request)
            
            assert isinstance(response, TileResponse)
            assert response.status_code == 200
            assert response.data == b"test image data"
            
            print("✅ Retry logic works correctly")
    
    def test_save_tile_basic(self):
        """Test basic tile saving."""
        from tilearray.tiles import save_tile
        
        # Mock file operations
        with patch('builtins.open', MagicMock()) as mock_open:
            with patch('os.makedirs', MagicMock()) as mock_makedirs:
                response = TileResponse(
                    data=b"test image data",
                    content_type="image/tiff",
                    status_code=200
                )
                
                result = save_tile(response, "/test/path/tile.tiff")
                
                assert result == "/test/path/tile.tiff"
                mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
                mock_open.assert_called_once_with("/test/path/tile.tiff", "wb")
                
                print(f"✅ Saved tile to: {result}")
    
    def test_create_tile_grid_for_bbox(self):
        """Test creating tile grid for bbox."""
        from tilearray.tiles import create_tile_grid_for_bbox
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        tile_size = 2.0
        
        tiles = create_tile_grid_for_bbox(bbox, tile_size)
        
        assert isinstance(tiles, list)
        assert len(tiles) > 0
        
        # Check that all tiles are within the original bbox
        for tile in tiles:
            assert tile.min_x >= bbox.min_x
            assert tile.min_y >= bbox.min_y
            assert tile.max_x <= bbox.max_x
            assert tile.max_y <= bbox.max_y
        
        print(f"✅ Created tile grid with {len(tiles)} tiles")
    
    def test_estimate_optimal_tile_size(self):
        """Test estimating optimal tile size."""
        from tilearray.tiles import estimate_optimal_tile_size
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        target_pixels = 256
        
        tile_size = estimate_optimal_tile_size(bbox, target_pixels)
        
        assert isinstance(tile_size, float)
        assert tile_size > 0
        
        print(f"✅ Estimated optimal tile size: {tile_size}")
    
    def test_tile_request_creation(self):
        """Test tile request creation."""
        request = TileRequest(
            url="http://test.com/tile",
            params={"param1": "value1", "param2": "value2"},
            bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
            format=Format.GEOTIFF
        )
        
        assert request.url == "http://test.com/tile"
        assert request.params == {"param1": "value1", "param2": "value2"}
        assert request.format == Format.GEOTIFF
        
        print(f"✅ Created tile request: {request}")
    
    def test_tile_response_creation(self):
        """Test tile response creation."""
        response = TileResponse(
            data=b"test image data",
            content_type="image/tiff",
            status_code=200
        )
        
        assert response.data == b"test image data"
        assert response.content_type == "image/tiff"
        assert response.status_code == 200
        
        print(f"✅ Created tile response: {response}")
    
    def test_tile_processing_pipeline(self):
        """Test complete tile processing pipeline."""
        from tilearray.tiles import fetch_tile, save_tile
        
        # Mock the HTTP request
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"test image data"
            mock_response.headers = {"Content-Type": "image/tiff"}
            mock_get.return_value = mock_response
            
            # Create request
            request = TileRequest(
                url="http://test.com/tile",
                params={"param1": "value1"},
                bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                format=Format.GEOTIFF
            )
            
            # Fetch tile
            response = fetch_tile(request)
            
            # Save tile
            with patch('builtins.open', MagicMock()) as mock_open:
                with patch('os.makedirs', MagicMock()) as mock_makedirs:
                    result = save_tile(response, "/test/path/tile.tiff")
                    
                    assert result == "/test/path/tile.tiff"
                    assert response.status_code == 200
                    assert response.data == b"test image data"
                    
                    print(f"✅ Complete tile pipeline: fetch -> save -> {result}")
    
    def test_tile_error_handling(self):
        """Test tile error handling scenarios."""
        from tilearray.tiles import fetch_tile
        
        # Test various error scenarios
        error_scenarios = [
            (requests.ConnectionError("Connection failed"), "Connection failed"),
            (requests.Timeout("Request timeout"), "Request timeout"),
            (requests.TooManyRedirects("Too many redirects"), "Too many redirects"),
        ]
        
        for error, expected_message in error_scenarios:
            with patch('requests.get') as mock_get:
                mock_get.side_effect = error
                
                request = TileRequest(
                    url="http://test.com/tile",
                    params={"param1": "value1"},
                    bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                    format=Format.GEOTIFF
                )
                
                with pytest.raises(type(error), match=expected_message):
                    fetch_tile(request)
                
                print(f"✅ Error handling for {type(error).__name__}: {expected_message}")
    
    def test_tile_format_handling(self):
        """Test tile format handling."""
        from tilearray.tiles import fetch_tile
        
        # Test different formats
        formats_to_test = [Format.GEOTIFF, Format.NETCDF, Format.HDF5, Format.JSON]
        
        for format_type in formats_to_test:
            with patch('requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.content = b"test data"
                mock_response.headers = {"Content-Type": format_type.value}
                mock_get.return_value = mock_response
                
                request = TileRequest(
                    url="http://test.com/tile",
                    params={"param1": "value1"},
                    bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
                    format=format_type
                )
                
                response = fetch_tile(request)
                
                assert response.status_code == 200
                assert response.content_type == format_type.value
                
                print(f"✅ Format handling for {format_type}: {response.content_type}")
