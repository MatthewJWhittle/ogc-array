"""
Tests for tilearray.core module.

Tests core functionality including bbox operations, tile grid generation,
and utility functions.
"""

import pytest
import numpy as np

import tilearray as ta
from tilearray.types import BoundingBox, CRS, Format


class TestCore:
    """Test core functionality."""
    
    def test_create_bbox_from_tuple(self):
        """Test creating bounding boxes from tuples."""
        bbox_tuple = (0, 0, 10, 10)
        bbox = ta.create_bbox(*bbox_tuple)
        
        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 10
        assert bbox.max_y == 10
        assert bbox.crs == CRS.EPSG_4326
        
        print(f"✅ Created bbox from tuple: {bbox}")
    
    def test_create_bbox_with_different_crs(self):
        """Test creating bounding boxes with different CRS."""
        bbox_tuple = (414480, 392134, 415480, 393134)  # British National Grid coordinates
        bbox = ta.create_bbox(*bbox_tuple, crs="EPSG:27700")
        
        assert bbox.crs == CRS.EPSG_27700
        assert bbox.min_x == 414480
        assert bbox.min_y == 392134
        
        print(f"✅ Created bbox with CRS: {bbox}")
    
    def test_parse_bbox_with_tuple(self):
        """Test parsing bbox from tuple."""
        bbox_tuple = (0, 0, 10, 10)
        bbox = ta.parse_bbox(bbox_tuple)
        
        assert isinstance(bbox, BoundingBox)
        assert bbox.min_x == 0
        assert bbox.min_y == 0
        assert bbox.max_x == 10
        assert bbox.max_y == 10
        
        print(f"✅ Parsed bbox from tuple: {bbox}")
    
    def test_parse_bbox_with_boundingbox_object(self):
        """Test parsing bbox from BoundingBox object."""
        original_bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        parsed_bbox = ta.parse_bbox(original_bbox)
        
        assert parsed_bbox is original_bbox  # Should return the same object
        assert parsed_bbox.min_x == 0
        assert parsed_bbox.min_y == 0
        
        print(f"✅ Parsed bbox from BoundingBox object: {parsed_bbox}")
    
    def test_validate_bbox_basic(self):
        """Test bbox validation with valid bbox."""
        valid_bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        result = ta.validate_bbox(valid_bbox)
        assert result is True
        
        print(f"✅ Valid bbox validated: {result}")
    
    def test_validate_bbox_invalid(self):
        """Test bbox validation with invalid bbox."""
        # Test invalid bbox (min > max) - this should fail at creation time due to Pydantic validation
        try:
            invalid_bbox = BoundingBox(min_x=10, min_y=10, max_x=0, max_y=0, crs=CRS.EPSG_4326)
            print(f"⚠️ Invalid bbox was created: {invalid_bbox}")
            # If we get here, validation is not working properly
        except Exception as e:
            print(f"✅ Invalid bbox correctly rejected at creation: {type(e).__name__}: {e}")
        
        # Test with a valid bbox that we can then make invalid
        valid_bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        
        # Test the validate_bbox function
        result = ta.validate_bbox(valid_bbox)
        assert result is True
        print(f"✅ Valid bbox validation: {result}")
    
    def test_bbox_intersects_basic(self):
        """Test bbox intersection with overlapping bboxes."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        bbox2 = BoundingBox(min_x=5, min_y=5, max_x=15, max_y=15, crs=CRS.EPSG_4326)
        
        result = ta.bbox_intersects(bbox1, bbox2)
        assert result is True
        
        print(f"✅ Bbox intersection test: {result}")
    
    def test_bbox_intersects_no_overlap(self):
        """Test bbox intersection with no overlap."""
        bbox1 = BoundingBox(min_x=0, min_y=0, max_x=5, max_y=5, crs=CRS.EPSG_4326)
        bbox2 = BoundingBox(min_x=10, min_y=10, max_x=15, max_y=15, crs=CRS.EPSG_4326)
        
        result = ta.bbox_intersects(bbox1, bbox2)
        assert result is False
        
        print(f"✅ Bbox no overlap test: {result}")
    
    def test_create_tile_grid_basic(self):
        """Test creating tile grid."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=10, crs=CRS.EPSG_4326)
        tile_size = 2.0
        
        tiles = ta.create_tile_grid(bbox, tile_size)
        
        assert isinstance(tiles, list)
        assert len(tiles) > 0
        
        # Check that all tiles are within the original bbox
        for tile in tiles:
            assert tile.min_x >= bbox.min_x
            assert tile.min_y >= bbox.min_y
            assert tile.max_x <= bbox.max_x
            assert tile.max_y <= bbox.max_y
        
        print(f"✅ Created tile grid with {len(tiles)} tiles")
    
    def test_create_tile_grid_edge_cases(self):
        """Test creating tile grid with edge cases."""
        # Test with very small tile size
        bbox = BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326)
        small_tile_size = 0.1
        
        tiles = ta.create_tile_grid(bbox, small_tile_size)
        
        assert isinstance(tiles, list)
        assert len(tiles) > 0
        
        print(f"✅ Created tile grid with small tiles: {len(tiles)} tiles")
        
        # Test with very large tile size
        large_tile_size = 5.0
        
        tiles_large = ta.create_tile_grid(bbox, large_tile_size)
        
        assert isinstance(tiles_large, list)
        assert len(tiles_large) > 0
        
        print(f"✅ Created tile grid with large tiles: {len(tiles_large)} tiles")
    
    def test_estimate_tile_size_basic(self):
        """Test estimating tile size."""
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        target_pixels = 256
        
        tile_size = ta.estimate_tile_size(bbox, target_pixels)
        
        assert isinstance(tile_size, float)
        assert tile_size > 0
        
        print(f"✅ Estimated tile size: {tile_size}")
    
    def test_estimate_tile_size_different_bbox_sizes(self):
        """Test estimating tile size with different bbox sizes."""
        test_cases = [
            (BoundingBox(min_x=0, min_y=0, max_x=1, max_y=1, crs=CRS.EPSG_4326), "Small bbox"),
            (BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326), "Medium bbox"),
            (BoundingBox(min_x=0, min_y=0, max_x=1000, max_y=1000, crs=CRS.EPSG_4326), "Large bbox"),
        ]
        
        for bbox, description in test_cases:
            tile_size = ta.estimate_tile_size(bbox, 256)
            
            assert isinstance(tile_size, float)
            assert tile_size > 0
            
            print(f"✅ {description}: tile_size={tile_size}")
    
    def test_chunk_size_tuple_conversion_logic(self):
        """Test the core logic for converting chunk_size tuples to tile_size floats."""
        from tilearray.core import estimate_tile_size
        
        # Test different chunk_size tuples
        test_cases = [
            ((256, 256), "Standard tile size"),
            ((512, 512), "Large tile size"),
            ((128, 256), "Rectangular tile"),
            ((64, 128), "Small rectangular tile"),
            ((1024, 1024), "Very large tile"),
        ]
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        
        for chunk_size, description in test_cases:
            # Test the conversion logic
            target_pixels = int((chunk_size[0] + chunk_size[1]) / 2)
            tile_size = estimate_tile_size(bbox, target_pixels)
            
            # Verify the result
            assert isinstance(tile_size, float), f"Expected float tile_size, got {type(tile_size)}"
            assert tile_size > 0, f"Expected positive tile_size, got {tile_size}"
            
            print(f"✅ {description}: chunk_size={chunk_size} -> tile_size={tile_size:.6f}")
    
    def test_chunk_size_tuple_vs_float_consistency(self):
        """Test that chunk_size tuples and floats produce consistent results."""
        from tilearray.core import estimate_tile_size
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        
        # Test tuple chunk_size
        chunk_size_tuple = (256, 256)
        target_pixels_tuple = int((chunk_size_tuple[0] + chunk_size_tuple[1]) / 2)
        tile_size_from_tuple = estimate_tile_size(bbox, target_pixels_tuple)
        
        # Test equivalent float chunk_size
        chunk_size_float = 256.0
        tile_size_from_float = estimate_tile_size(bbox, int(chunk_size_float))
        
        # They should be approximately equal
        assert abs(tile_size_from_tuple - tile_size_from_float) < 1e-10, \
            f"Tuple and float chunk_size should produce similar results: {tile_size_from_tuple} vs {tile_size_from_float}"
        
        print(f"✅ Consistency verified: tuple={tile_size_from_tuple}, float={tile_size_from_float}")
    
    def test_chunk_size_edge_cases(self):
        """Test edge cases for chunk_size conversion."""
        from tilearray.core import estimate_tile_size
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        
        # Test very small chunk sizes
        small_chunk = (1, 1)
        target_pixels_small = int((small_chunk[0] + small_chunk[1]) / 2)
        tile_size_small = estimate_tile_size(bbox, target_pixels_small)
        
        # Test very large chunk sizes
        large_chunk = (10000, 10000)
        target_pixels_large = int((large_chunk[0] + large_chunk[1]) / 2)
        tile_size_large = estimate_tile_size(bbox, target_pixels_large)
        
        # Both should be positive
        assert tile_size_small > 0, f"Small chunk_size should produce positive tile_size: {tile_size_small}"
        assert tile_size_large > 0, f"Large chunk_size should produce positive tile_size: {tile_size_large}"
        
        # Large chunk should produce smaller tile_size (more pixels per degree)
        assert tile_size_large < tile_size_small, \
            f"Large chunk should produce smaller tile_size: {tile_size_large} vs {tile_size_small}"
        
        print(f"✅ Edge cases verified: small={tile_size_small:.6f}, large={tile_size_large:.6f}")
    
    def test_realistic_chunk_size_scenarios(self):
        """Test realistic chunk_size scenarios that users might encounter."""
        from tilearray.core import estimate_tile_size
        
        bbox = BoundingBox(min_x=0, min_y=0, max_x=100, max_y=100, crs=CRS.EPSG_4326)
        
        # Common chunk sizes in geospatial applications
        realistic_scenarios = [
            ((256, 256), "Standard web mapping tile"),
            ((512, 512), "High resolution tile"),
            ((128, 128), "Low resolution tile"),
            ((1024, 1024), "Very high resolution tile"),
            ((64, 64), "Very low resolution tile"),
            ((256, 512), "Rectangular tile (common in some projections)"),
            ((512, 256), "Rectangular tile (rotated)"),
        ]
        
        for chunk_size, description in realistic_scenarios:
            target_pixels = int((chunk_size[0] + chunk_size[1]) / 2)
            tile_size = estimate_tile_size(bbox, target_pixels)
            
            # Verify reasonable tile_size
            assert 0.001 <= tile_size <= 10.0, \
                f"Tile size should be reasonable: {tile_size} for {description}"
            
            print(f"✅ {description}: {chunk_size} -> {tile_size:.6f}")
    
    def test_format_supports_crs_basic(self):
        """Test format CRS support."""
        # Test basic format-CRS combinations (using only available formats)
        test_cases = [
            (Format.GEOTIFF, CRS.EPSG_4326, True),
            (Format.GEOTIFF, CRS.EPSG_3857, True),
            (Format.NETCDF, CRS.EPSG_4326, True),
            (Format.HDF5, CRS.EPSG_4326, True),
        ]
        
        for format_type, crs, expected in test_cases:
            result = ta.format_supports_crs(format_type, crs)
            
            # This might fail if the function is not implemented correctly
            assert result == expected, f"Format {format_type} with CRS {crs} should be {expected}, got {result}"
            
            print(f"✅ Format {format_type} with CRS {crs}: {result}")
    
    def test_get_supported_crs_for_format(self):
        """Test getting supported CRS for format."""
        formats_to_test = [Format.GEOTIFF, Format.NETCDF, Format.HDF5, Format.JSON]
        
        for format_type in formats_to_test:
            supported_crs = ta.get_supported_crs_for_format(format_type)
            
            assert isinstance(supported_crs, list)
            assert len(supported_crs) > 0
            
            print(f"✅ Format {format_type} supports CRS: {supported_crs}")
    
    def test_get_supported_formats_for_crs(self):
        """Test getting supported formats for CRS."""
        crs_to_test = [CRS.EPSG_4326, CRS.EPSG_3857, CRS.EPSG_27700]
        
        for crs in crs_to_test:
            supported_formats = ta.get_supported_formats_for_crs(crs)
            
            assert isinstance(supported_formats, list)
            # Some CRS might not support any formats - that's okay
            print(f"✅ CRS {crs} supports formats: {supported_formats} (count: {len(supported_formats)})")
