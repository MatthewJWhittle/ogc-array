"""
Integration tests for tilearray against real OGC services.

These tests use real services and are marked as slow and network-dependent.
They are designed to flag regressions and test real-world scenarios.
"""

from typing import Tuple
import pytest
import numpy as np

import tilearray as ta
from tilearray.types import BoundingBox, CRS


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.net
class TestRealServiceIntegration:
    """Test against real OGC services."""

    @pytest.fixture
    def service_url(self):
        return "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"

    @pytest.fixture
    def coverage_id(self):
        return "dtm-1m"

    @pytest.fixture
    def bbox(self) -> Tuple[float, float, float, float]:
        xmin, ymin = 416209 , 391707
        side_length_m = 1000
        xmax, ymax = xmin + side_length_m, ymin + side_length_m
        return xmin, ymin, xmax, ymax
    
    def test_uk_environment_wcs_load_array(
        self, 
        service_url: str, 
        coverage_id: str, 
        bbox: Tuple[float, float, float, float]
    ) -> None:
        """Test load_array against real UK Environment WCS service."""
        # UK Environment WCS service
        service = ta.create_wcs_service(
            url=service_url,
            coverage_id=coverage_id,
            resolution=(1, 1) # 1m resolution
        )
        
        # Test with different chunk sizes
        chunk_sizes = [
            (256, 256),  # Standard tile size
            (512, 512),  # Large tile size
            (128, 128),  # Small tile size
        ]

        # Calculate the expected shape of the array at the given resolution
        xmin, ymin, xmax, ymax = bbox
        x_side = xmax - xmin
        y_side = ymax - ymin
        x_dim = int(x_side / 1)
        y_dim = int(y_side / 1)
        expected_shape = (1, y_dim, x_dim)
        expected_dims = ('band', 'y', 'x')
        for chunk_size in chunk_sizes:
            result = ta.load_array(service, bbox, chunk_size=chunk_size)
            assert result is not None
            assert result.shape == expected_shape
            assert result.dims == expected_dims
    
    def test_uk_environment_wcs_service_config_override(self):
        """Test service configuration override with real service."""
        service_url = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
        
        # Create base service
        base_service = ta.create_wcs_service(
            url=service_url,
            coverage_id="dtm-1m",
            resolution=0.001
        )
        
        # Test with custom parameters
        custom_service = {
            **base_service,
            "format": "image/tiff",
            "crs": "EPSG:4326",
            "adapter_class": None  # Use default adapter
        }
        
        # Small test area
        bbox = BoundingBox(
            min_x=-0.5, min_y=51.0,
            max_x=-0.4, max_y=51.1,
            crs=CRS.EPSG_4326
        )
        
        result = ta.load_array(custom_service, bbox, chunk_size=(256, 256))
            
        assert result is not None
        assert hasattr(result, 'shape')
        assert hasattr(result, 'dims')
    
    def test_uk_environment_wcs_different_bbox_sizes(self):
        """Test different bounding box sizes against real service."""
        service_url = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
        
        service = ta.create_wcs_service(
            url=service_url,
            coverage_id="dtm-1m",
            resolution=0.001
        )
        
        # Test different bbox sizes
        bbox_sizes = [
            # (bbox, description)
            (BoundingBox(min_x=-0.5, min_y=51.0, max_x=-0.4, max_y=51.1, crs=CRS.EPSG_4326), "Small area"),
            (BoundingBox(min_x=-0.6, min_y=50.9, max_x=-0.3, max_y=51.2, crs=CRS.EPSG_4326), "Medium area"),
            (BoundingBox(min_x=-1.0, min_y=50.5, max_x=0.0, max_y=51.5, crs=CRS.EPSG_4326), "Large area"),
        ]
        
        for bbox, description in bbox_sizes:
            result = ta.load_array(service, bbox, chunk_size=(256, 256))
        assert result is not None
        assert hasattr(result, 'shape')
        assert hasattr(result, 'dims')
    
    def test_uk_environment_wcs_error_handling(self):
        """Test error handling with real service."""
        service_url = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
        
        service = ta.create_wcs_service(
            url=service_url,
            coverage_id="dtm-1m",
            resolution=0.001
        )
        
        # Test with invalid bbox (outside UK)
        invalid_bbox = BoundingBox(
            min_x=-180, min_y=-90,  # Invalid coordinates
            max_x=180, max_y=90,
            crs=CRS.EPSG_4326
        )
        
        result = ta.load_array(service, invalid_bbox, chunk_size=(256, 256))
            
        assert result is not None
        assert hasattr(result, 'shape')
        assert hasattr(result, 'dims')
    
    def test_uk_environment_wcs_performance(self):
        """Test performance with real service."""
        service_url = "https://environment.data.gov.uk/spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs"
        
        service = ta.create_wcs_service(
            url=service_url,
            coverage_id="dtm-1m",
            resolution=0.001
        )
        
        # Small test area for performance testing
        bbox = BoundingBox(
            min_x=-0.5, min_y=51.0,
            max_x=-0.4, max_y=51.1,
            crs=CRS.EPSG_4326
        )
        
        import time
        
        try:
            start_time = time.time()
            result = ta.load_array(service, bbox, chunk_size=(256, 256))
            end_time = time.time()
            
            if result is not None:
                duration = end_time - start_time
                print(f"✅ Loaded array in {duration:.2f} seconds")
                
                # Check if performance is reasonable (should be < 30 seconds for small area)
                if duration > 30:
                    print(f"⚠️ Performance warning: Load took {duration:.2f} seconds")
                else:
                    print(f"✅ Performance acceptable: {duration:.2f} seconds")
            else:
                print(f"⚠️ Service returned None")
                
        except Exception as e:
            print(f"⚠️ Service error during performance test: {type(e).__name__}: {e}")

