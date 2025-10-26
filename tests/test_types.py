"""
Tests for tilearray.types module.

Tests Pydantic models, enums, and type definitions.
"""

import pytest
from pydantic import ValidationError

import tilearray as ta
from tilearray.types import BoundingBox, CRS, Format, SpatialExtent, CoverageDescription, ServiceCapabilities, TileRequest, TileResponse, WCSResponse


class TestTypes:
    """Test type definitions and models."""
    
    def test_crs_enum(self):
        """Test CRS enum values."""
        assert CRS.EPSG_4326 == "EPSG:4326"
        assert CRS.EPSG_3857 == "EPSG:3857"
        assert CRS.EPSG_32633 == "EPSG:32633"
        assert CRS.EPSG_27700 == "EPSG:27700"
        
        print("✅ CRS enum values are correct")
    
    def test_format_enum(self):
        """Test Format enum values."""
        assert Format.GEOTIFF == "image/tiff"
        assert Format.NETCDF == "application/netcdf"
        assert Format.HDF5 == "application/x-hdf5"
        assert Format.JSON == "application/json"
        
        print("✅ Format enum values are correct")
    
    def test_bounding_box_creation(self):
        """Test BoundingBox creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        
        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 10
        assert bbox.max_y == 10
        assert bbox.crs == CRS.EPSG_4326
        
        print(f"✅ Created BoundingBox: {bbox}")
    
    def test_bounding_box_default_crs(self):
        """Test BoundingBox default CRS."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10)
        
        assert bbox.crs == CRS.EPSG_4326  # Default CRS
        
        print(f"✅ BoundingBox default CRS: {bbox.crs}")
    
    def test_bounding_box_validation(self):
        """Test BoundingBox validation."""
        # Valid bbox
        valid_bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        assert valid_bbox.min_x < valid_bbox.max_x
        assert valid_bbox.min_y < valid_bbox.max_y
        
        # Invalid bbox should raise ValidationError
        with pytest.raises(ValidationError, match="min_x must be less than max_x"):
            BoundingBox(min_x=10, min_y=0, max_x=0, max_y=10, crs=CRS.EPSG_4326)
        
        with pytest.raises(ValidationError, match="min_y must be less than max_y"):
            BoundingBox(min_x=0, min_y=10, max_x=10, max_y=0, crs=CRS.EPSG_4326)
        
        print("✅ BoundingBox validation works correctly")
    
    def test_spatial_extent_creation(self):
        """Test SpatialExtent creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        extent = SpatialExtent(bbox=bbox)
        
        assert extent.bbox == bbox
        assert extent.dimensions is None
        
        print(f"✅ Created SpatialExtent: {extent}")
    
    def test_spatial_extent_with_dimensions(self):
        """Test SpatialExtent with dimensions."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        dimensions = {"x": 10, "y": 10}
        extent = SpatialExtent(bbox=bbox, dimensions=dimensions)
        
        assert extent.bbox == bbox
        assert extent.dimensions == dimensions
        
        print(f"✅ Created SpatialExtent with dimensions: {extent}")
    
    def test_coverage_description_creation(self):
        """Test CoverageDescription creation."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        spatial_extent = SpatialExtent(bbox=bbox)
        
        coverage = CoverageDescription(
            identifier="test_coverage",
            title="Test Coverage",
            spatial_extent=spatial_extent,
            native_format=Format.GEOTIFF
        )
        
        assert coverage.identifier == "test_coverage"
        assert coverage.title == "Test Coverage"
        assert coverage.spatial_extent == spatial_extent
        assert coverage.native_format == Format.GEOTIFF
        
        print(f"✅ Created CoverageDescription: {coverage}")
    
    def test_service_capabilities_creation(self):
        """Test ServiceCapabilities creation."""
        capabilities = ServiceCapabilities(
            version="2.0.1",
            title="Test Service",
            coverages=[]
        )
        
        assert capabilities.version == "2.0.1"
        assert capabilities.title == "Test Service"
        assert capabilities.coverages == []
        
        print(f"✅ Created ServiceCapabilities: {capabilities}")
    
    def test_tile_request_creation(self):
        """Test TileRequest creation."""
        request = TileRequest(
            url="http://test.com",
            params={"param1": "value1"},
            bbox=BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326),
            format=Format.GEOTIFF
        )
        
        assert request.url == "http://test.com"
        assert request.params == {"param1": "value1"}
        assert request.format == Format.GEOTIFF
        
        print(f"✅ Created TileRequest: {request}")
    
    def test_tile_response_creation(self):
        """Test TileResponse creation."""
        response = TileResponse(
            data=b"test data",
            content_type="image/tiff",
            status_code=200
        )
        
        assert response.data == b"test data"
        assert response.content_type == "image/tiff"
        assert response.status_code == 200
        
        print(f"✅ Created TileResponse: {response}")
    
    def test_wcs_response_creation(self):
        """Test WCSResponse creation."""
        response = WCSResponse(
            data=b"test xml data",
            status_code=200
        )
        
        assert response.data == b"test xml data"
        assert response.status_code == 200
        
        print(f"✅ Created WCSResponse: {response}")
    
    def test_enum_string_conversion(self):
        """Test enum string conversion."""
        # Test CRS string conversion
        crs_str = str(CRS.EPSG_4326)
        assert crs_str == "EPSG:4326"
        
        # Test Format string conversion
        format_str = str(Format.GEOTIFF)
        assert format_str == "image/tiff"
        
        print("✅ Enum string conversion works correctly")
    
    def test_enum_comparison(self):
        """Test enum comparison."""
        # Test CRS comparison
        assert CRS.EPSG_4326 == "EPSG:4326"
        assert CRS.EPSG_4326 != "EPSG:3857"
        
        # Test Format comparison
        assert Format.GEOTIFF == "image/tiff"
        assert Format.GEOTIFF != "application/netcdf"
        
        print("✅ Enum comparison works correctly")
    
    def test_model_serialization(self):
        """Test model serialization."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        
        # Test dict conversion
        bbox_dict = bbox.model_dump()
        assert isinstance(bbox_dict, dict)
        assert bbox_dict["min_x"] == 0
        assert bbox_dict["crs"] == "EPSG:4326"
        
        # Test JSON conversion
        bbox_json = bbox.model_dump_json()
        assert isinstance(bbox_json, str)
        assert "EPSG:4326" in bbox_json
        
        print("✅ Model serialization works correctly")
    
    def test_model_deserialization(self):
        """Test model deserialization."""
        # Test dict to model
        bbox_dict = {
            "min_x": 0,
            "min_y": 0,
            "max_x": 10,
            "max_y": 10,
            "crs": "EPSG:4326"
        }
        
        bbox = BoundingBox.model_validate(bbox_dict)
        assert bbox.min_x == 0
        assert bbox.crs == CRS.EPSG_4326
        
        # Test JSON to model
        bbox_json = '{"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10, "crs": "EPSG:4326"}'
        bbox_from_json = BoundingBox.model_validate_json(bbox_json)
        assert bbox_from_json.min_x == 0
        assert bbox_from_json.crs == CRS.EPSG_4326
        
        print("✅ Model deserialization works correctly")
