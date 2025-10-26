"""Tests for OGC core models."""

import pytest
from datetime import datetime
from tilearray.types import (
    BoundingBox, SpatialExtent, TemporalExtent, CoverageDescription,
    ServiceCapabilities, TileRequest, WCSResponse, CRS, Format
)
from tilearray.core import (
    validate_bbox, bbox_intersects, bbox_union, bbox_intersection,
    create_tile_grid, estimate_tile_size, format_supports_crs,
    get_supported_crs_for_format, get_supported_formats_for_crs
)


class TestBoundingBox:
    """Test BoundingBox model."""
    
    def test_valid_bbox(self):
        """Test valid bounding box creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 10
        assert bbox.max_y == 10
        assert bbox.crs == CRS.EPSG_4326
    
    def test_invalid_bbox_x_coordinates(self):
        """Test invalid X coordinates."""
        with pytest.raises(ValueError, match="min_x must be less than max_x"):
            BoundingBox(min_x=10, min_y=0, max_x=0, max_y=10)
    
    def test_invalid_bbox_y_coordinates(self):
        """Test invalid Y coordinates."""
        with pytest.raises(ValueError, match="min_y must be less than max_y"):
            BoundingBox(min_x=0, min_y=10, max_x=10, max_y=0)
    
    def test_custom_crs(self):
        """Test custom CRS."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_3857)
        assert bbox.crs == CRS.EPSG_3857


class TestSpatialExtent:
    """Test SpatialExtent model."""
    
    def test_spatial_extent_creation(self):
        """Test spatial extent creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        extent = SpatialExtent(bbox=bbox)
        assert extent.bbox == bbox
        assert extent.bbox.crs == CRS.EPSG_4326
        assert extent.dimensions is None
    
    def test_custom_dimensions(self):
        """Test custom dimensions."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        extent = SpatialExtent(bbox=bbox, dimensions={"x": 10, "y": 10})
        assert extent.dimensions == {"x": 10, "y": 10}


class TestTemporalExtent:
    """Test TemporalExtent model."""
    
    def test_temporal_extent_creation(self):
        """Test temporal extent creation."""
        start = datetime(2020, 1, 1)
        end = datetime(2020, 12, 31)
        extent = TemporalExtent(start_time=start, end_time=end)
        assert extent.start_time == start
        assert extent.end_time == end
    
    def test_invalid_temporal_extent(self):
        """Test invalid temporal extent."""
        start = datetime(2020, 12, 31)
        end = datetime(2020, 1, 1)
        with pytest.raises(ValueError, match="end_time must be after start_time"):
            TemporalExtent(start_time=start, end_time=end)


class TestCoverageDescription:
    """Test CoverageDescription model."""
    
    def test_coverage_description_creation(self):
        """Test coverage description creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        spatial_extent = SpatialExtent(bbox=bbox)
        
        coverage = CoverageDescription(
            identifier="test_coverage",
            title="Test Coverage",
            abstract="A test coverage",
            spatial_extent=spatial_extent
        )
        
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        assert coverage.abstract == "A test coverage"
        assert coverage.spatial_extent == spatial_extent
        assert coverage.spatial_extent.bbox.crs == CRS.EPSG_4326
        assert coverage.supported_formats == []


class TestServiceCapabilities:
    """Test ServiceCapabilities model."""
    
    def test_service_capabilities_creation(self):
        """Test service capabilities creation."""
        capabilities = ServiceCapabilities(
            service_title="Test WCS Service",
            service_url="http://example.com/wcs"
        )
        
        assert capabilities.service_title == "Test WCS Service"
        assert capabilities.service_url == "http://example.com/wcs"
        assert capabilities.version == "2.0.1"
        assert "GetCapabilities" in capabilities.supported_operations


class TestTileRequest:
    """Test TileRequest model."""
    
    def test_tile_request_creation(self):
        """Test tile request creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"},
            output_format=Format.GEOTIFF,
            crs=CRS.EPSG_4326
        )
        
        assert request.url == "http://example.com/wcs"
        assert request.params == {"service": "WCS", "request": "GetCoverage"}
        assert request.output_format == Format.GEOTIFF
        assert request.crs == CRS.EPSG_4326
    
    def test_tile_request_optional_fields(self):
        """Test tile request with optional fields."""
        request = TileRequest(
            url="http://example.com/wcs",
            params={"service": "WCS", "request": "GetCoverage"},
            headers={"Accept": "image/tiff"},
            timeout=60,
            retries=5
        )
        
        assert request.url == "http://example.com/wcs"
        assert request.params == {"service": "WCS", "request": "GetCoverage"}
        assert request.headers == {"Accept": "image/tiff"}
        assert request.timeout == 60
        assert request.retries == 5


class TestWCSResponse:
    """Test WCSResponse model."""
    
    def test_successful_response(self):
        """Test successful response."""
        response = WCSResponse(
            success=True,
            data=b"test data",
            status_code=200
        )
        
        assert response.success is True
        assert response.data == b"test data"
        assert response.status_code == 200
        assert response.error_message is None
    
    def test_error_response(self):
        """Test error response."""
        response = WCSResponse(
            success=False,
            error_message="Test error"
        )
        
        assert response.success is False
        assert response.error_message == "Test error"
        assert response.data is None


class TestEnums:
    """Test enum values."""
    
    def test_crs_enum(self):
        """Test CRS enum values."""
        assert CRS.EPSG_4326 == "EPSG:4326"
        assert CRS.EPSG_3857 == "EPSG:3857"
        assert CRS.EPSG_32633 == "EPSG:32633"
        assert CRS.EPSG_27700 == "EPSG:27700"
    
    def test_format_enum(self):
        """Test Format enum values."""
        assert Format.GEOTIFF == "image/tiff"
        assert Format.NETCDF == "application/netcdf"
        assert Format.HDF5 == "application/x-hdf5"
        assert Format.JSON == "application/json"


class TestBoundingBoxOperations:
    """Test bounding box utility functions."""
    
    def test_validate_bbox_valid(self):
        """Test valid bounding box validation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        assert validate_bbox(bbox) is True
    
    def test_validate_bbox_invalid(self):
        """Test invalid bounding box validation."""
        # Create a valid bbox first, then test with invalid data
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        # Test with manually invalid data
        bbox.min_x = 10  # This makes it invalid
        bbox.max_x = 0
        assert validate_bbox(bbox) is False
    
    def test_bbox_intersects_true(self):
        """Test intersecting bounding boxes."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        bbox2 = BoundingBox(min_x=5, min_y=5, max_x=15, max_y=15)
        assert bbox_intersects(bbox1, bbox2) is True
    
    def test_bbox_intersects_false(self):
        """Test non-intersecting bounding boxes."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=5, max_y=5)
        bbox2 = BoundingBox(min_x=10, min_y=10, max_x=15, max_y=15)
        assert bbox_intersects(bbox1, bbox2) is False
    
    def test_bbox_union(self):
        """Test bounding box union."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=5, max_y=5)
        bbox2 = BoundingBox(min_x=3, min_y=3, max_x=8, max_y=8)
        union = bbox_union(bbox1, bbox2)
        
        assert union.min_x == 0
        assert union.min_y == 0
        assert union.max_x == 8
        assert union.max_y == 8
    
    def test_bbox_union_different_crs(self):
        """Test bounding box union with different CRS raises error."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=5, max_y=5, crs=CRS.EPSG_4326)
        bbox2 = BoundingBox(min_x=3, min_y=3, max_x=8, max_y=8, crs=CRS.EPSG_3857)
        
        with pytest.raises(ValueError, match="Cannot union bounding boxes with different CRS"):
            bbox_union(bbox1, bbox2)
    
    def test_bbox_intersection(self):
        """Test bounding box intersection."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        bbox2 = BoundingBox(min_x=5, min_y=5, max_x=15, max_y=15)
        intersection = bbox_intersection(bbox1, bbox2)
        
        assert intersection is not None
        assert intersection.min_x == 5
        assert intersection.min_y == 5
        assert intersection.max_x == 10
        assert intersection.max_y == 10
    
    def test_bbox_intersection_no_overlap(self):
        """Test bounding box intersection with no overlap."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=5, max_y=5)
        bbox2 = BoundingBox(min_x=10, min_y=10, max_x=15, max_y=15)
        intersection = bbox_intersection(bbox1, bbox2)
        
        assert intersection is None


class TestTileOperations:
    """Test tile utility functions."""
    
    def test_create_tile_grid(self):
        """Test tile grid creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        tiles = create_tile_grid(bbox, tile_size=5.0)
        
        assert len(tiles) == 4  # 2x2 grid
        assert tiles[0].min_x == 0
        assert tiles[0].min_y == 0
        assert tiles[0].max_x == 5
        assert tiles[0].max_y == 5
    
    def test_create_tile_grid_invalid_size(self):
        """Test tile grid creation with invalid size."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        
        with pytest.raises(ValueError, match="tile_size must be positive"):
            create_tile_grid(bbox, tile_size=0)
        
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            create_tile_grid(bbox, tile_size=5.0, overlap=-1.0)
        
        with pytest.raises(ValueError, match="overlap must be less than tile_size"):
            create_tile_grid(bbox, tile_size=5.0, overlap=5.0)
    
    def test_estimate_tile_size(self):
        """Test tile size estimation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1)
        tile_size = estimate_tile_size(bbox, target_pixels=100)
        
        assert tile_size > 0
        assert tile_size <= 1.0
    
    def test_estimate_tile_size_invalid_pixels(self):
        """Test tile size estimation with invalid pixels."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1)
        
        with pytest.raises(ValueError, match="target_pixels must be positive"):
            estimate_tile_size(bbox, target_pixels=0)


class TestFormatCRSOperations:
    """Test format and CRS utility functions."""
    
    def test_format_supports_crs(self):
        """Test format CRS support."""
        assert format_supports_crs(Format.GEOTIFF, CRS.EPSG_4326) is True
        assert format_supports_crs(Format.GEOTIFF, CRS.EPSG_3857) is True
        assert format_supports_crs(Format.NETCDF, CRS.EPSG_4326) is True
        assert format_supports_crs(Format.HDF5, CRS.EPSG_4326) is True
    
    def test_get_supported_crs_for_format(self):
        """Test getting supported CRS for format."""
        crs_list = get_supported_crs_for_format(Format.GEOTIFF)
        assert CRS.EPSG_4326 in crs_list
        assert CRS.EPSG_3857 in crs_list
        assert CRS.EPSG_32633 in crs_list
    
    def test_get_supported_formats_for_crs(self):
        """Test getting supported formats for CRS."""
        formats = get_supported_formats_for_crs(CRS.EPSG_4326)
        assert Format.GEOTIFF in formats
        assert Format.NETCDF in formats
        assert Format.HDF5 in formats
        assert Format.JSON in formats
