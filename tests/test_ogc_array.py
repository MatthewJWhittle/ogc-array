"""Tests for OGC array functionality."""

import pytest
import numpy as np
import xarray as xr
import dask.array as da
from unittest.mock import Mock, patch, MagicMock

from tilearray.array import (
    create_array, create_dataset
)
from tilearray.types import BoundingBox, CRS, Format, TileRequest, TileResponse


class TestCreateArray:
    """Test convenience functions."""
    
    @patch('tilearray.core.create_tile_grid')
    @patch('tilearray.array._fetch_tile_delayed')
    def test_create_array(self, mock_fetch_tile_delayed, mock_create_tile_grid):
        """Test create_array function."""
        # Mock tile grid - single tile to avoid stacking issues
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        mock_x_coords = np.array([0, 1])
        mock_y_coords = np.array([0, 1])
        mock_grid_shape = (1, 1)
        mock_create_tile_grid.return_value = (mock_x_coords, mock_y_coords, mock_grid_shape)
        
        # Mock delayed tile
        mock_delayed_tile = Mock()
        mock_delayed_tile.return_value = np.zeros((256, 256))
        mock_fetch_tile_delayed.return_value = mock_delayed_tile
        
        result = create_array(
            service_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            service_type="WCS"
        )
        
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('y', 'x')
        assert 'crs' in result.attrs
        assert result.attrs['service_url'] == "http://example.com/wcs"
        assert result.attrs['coverage_id'] == "test_coverage"

    @patch('tilearray.array.create_array')
    def test_create_dataset(self, mock_create_array):
        """Test create_dataset function."""
        mock_array = xr.DataArray(
            np.zeros((256, 256)),
            dims=['y', 'x'],
            coords={'x': np.linspace(0, 1, 256), 'y': np.linspace(1, 0, 256)}
        )
        mock_create_array.return_value = mock_array
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        
        result = create_dataset(
            service_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox
        )
        
        assert isinstance(result, xr.Dataset)
        assert "test_coverage" in result.data_vars


class TestArrayIntegration:
    """Integration tests for array functionality."""
    
    @patch('tilearray.core.create_tile_grid')
    @patch('tilearray.array._fetch_tile_delayed')
    def test_end_to_end_array_creation(self, mock_fetch_tile_delayed, mock_create_tile_grid):
        """Test end-to-end array creation."""
        # Mock tile grid
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        mock_x_coords = np.array([0, 1])
        mock_y_coords = np.array([0, 1])
        mock_grid_shape = (1, 1)
        mock_create_tile_grid.return_value = (mock_x_coords, mock_y_coords, mock_grid_shape)
        
        # Mock successful tile response
        mock_delayed_tile = Mock()
        mock_delayed_tile.return_value = np.zeros((256, 256))
        mock_fetch_tile_delayed.return_value = mock_delayed_tile
        
        result = create_array(
            service_url="http://example.com/wcs",
            coverage_id="test_coverage",
            bbox=bbox,
            service_type="WCS"
        )
        
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('y', 'x')
        assert result.attrs['service_type'] == "WCS"

    @patch('tilearray.core.create_tile_grid')
    @patch('tilearray.array._fetch_tile_delayed')
    def test_array_with_different_service_types(self, mock_fetch_tile_delayed, mock_create_tile_grid):
        """Test array creation with different service types."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        mock_x_coords = np.array([0, 1])
        mock_y_coords = np.array([0, 1])
        mock_grid_shape = (1, 1)
        mock_create_tile_grid.return_value = (mock_x_coords, mock_y_coords, mock_grid_shape)
        
        mock_delayed_tile = Mock()
        mock_delayed_tile.return_value = np.zeros((256, 256))
        mock_fetch_tile_delayed.return_value = mock_delayed_tile
        
        # Test WMS
        result_wms = create_array(
            service_url="http://example.com/wms",
            coverage_id="test_layer",
            bbox=bbox,
            service_type="WMS"
        )
        assert result_wms.attrs['service_type'] == "WMS"
        
        # Test WMTS
        result_wmts = create_array(
            service_url="http://example.com/wmts",
            coverage_id="test_layer",
            bbox=bbox,
            service_type="WMTS"
        )
        assert result_wmts.attrs['service_type'] == "WMTS"

    @patch('tilearray.core.create_tile_grid')
    @patch('tilearray.array._fetch_tile_delayed')
    def test_array_with_custom_adapter(self, mock_fetch_tile_delayed, mock_create_tile_grid):
        """Test array creation with custom adapter."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        mock_x_coords = np.array([0, 1])
        mock_y_coords = np.array([0, 1])
        mock_grid_shape = (1, 1)
        mock_create_tile_grid.return_value = (mock_x_coords, mock_y_coords, mock_grid_shape)
        
        mock_delayed_tile = Mock()
        mock_delayed_tile.return_value = np.zeros((256, 256))
        mock_fetch_tile_delayed.return_value = mock_delayed_tile
        
        # Mock custom adapter
        mock_adapter = Mock()
        mock_adapter.create_tile_request.return_value = TileRequest(
            url="http://example.com",
            params={"test": "param"}
        )
        
        result = create_array(
            service_url="http://example.com/custom",
            coverage_id="test_coverage",
            bbox=bbox,
            adapter_class=lambda x: mock_adapter
        )
        
        assert isinstance(result, xr.DataArray)
        assert result.attrs['service_url'] == "http://example.com/custom"