"""
OGC Array - A Python library for OGC array operations.

This library provides utilities for working with OGC (Open Geospatial Consortium)
array data structures and operations.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import core functionality

# Import OGC types and utilities
from .ogc.types import (
    CRS, Format, BoundingBox, SpatialExtent, TemporalExtent,
    CoverageDescription, ServiceCapabilities, TileRequest, WCSResponse
)
from .ogc.core import (
    validate_bbox, bbox_intersects, bbox_union, bbox_intersection,
    create_tile_grid, estimate_tile_size, format_supports_crs,
    get_supported_crs_for_format, get_supported_formats_for_crs
)
from .ogc.wcs import WCSParser, WCSClient

__all__ = [
    # Core functionality
    "ArrayProcessor",
    
    # OGC Types
    "CRS", "Format", "BoundingBox", "SpatialExtent", "TemporalExtent",
    "CoverageDescription", "ServiceCapabilities", "TileRequest", "WCSResponse",
    
    # OGC Utility Functions
    "validate_bbox", "bbox_intersects", "bbox_union", "bbox_intersection",
    "create_tile_grid", "estimate_tile_size", "format_supports_crs",
    "get_supported_crs_for_format", "get_supported_formats_for_crs",
    
    # WCS Functionality
    "WCSParser", "WCSClient",
    
    # Package info
    "__version__"
]
