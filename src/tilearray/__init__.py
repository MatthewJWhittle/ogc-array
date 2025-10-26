"""
TileArray - A Python library for loading geospatial data from remote tile servers.

This library provides utilities for loading geospatial data from OGC services
(WCS, WMS, WMTS) and other tile servers as xarray objects with Dask chunking
for efficient processing of large datasets.

The main API is designed to be simple and intuitive:

    >>> import tilearray as ta
    >>> 
    >>> # Create a service configuration
    >>> service = ta.create_wcs_service("http://example.com/wcs", "elevation")
    >>> 
    >>> # Load data with a simple bbox tuple
    >>> data = ta.load_array(service, (-1, 50, 1, 52))  # London area
    >>> 
    >>> # Or use convenience functions
    >>> data = ta.load_wcs_array("http://example.com/wcs", "elevation", (-1, 50, 1, 52))
    >>> 
    >>> # Save using xarray's built-in methods
    >>> data.to_netcdf("elevation.nc")
    >>> data.to_zarr("elevation.zarr")
"""

from ._version import __version__

__author__ = "Your Name"
__email__ = "your.email@example.com"

# High-level user-friendly API
from .core import (
    create_bbox, parse_bbox, BBoxTuple, ServiceConfig,
    validate_bbox, bbox_intersects, bbox_union, bbox_intersection,
    create_tile_grid, estimate_tile_size, format_supports_crs,
    get_supported_crs_for_format, get_supported_formats_for_crs
)

from .array import (
    create_wcs_service, create_wms_service, create_wmts_service,
    load_array, load_dataset, load_wcs_array, load_wms_array,
    create_array, create_dataset
)

# OGC Implementations
from .ogc import (
    WCSParser, WCSClient, WCSTileAdapter, WMSTileAdapter, WMTSAdapter
)

# Types and Models
from .types import (
    CRS, Format, BoundingBox, SpatialExtent, TemporalExtent,
    CoverageDescription, ServiceCapabilities, TileRequest, TileResponse, WCSResponse
)

# Generic Tile Functionality
from .tiles import (
    fetch_tile, save_tile, create_tile_grid_for_bbox, estimate_optimal_tile_size
)

# Public API - prioritize the user-friendly functions
__all__ = [
    # High-level API (recommended for most users)
    "create_bbox", "parse_bbox",
    "create_wcs_service", "create_wms_service", "create_wmts_service", 
    "load_array", "load_dataset",
    "load_wcs_array", "load_wms_array",
    "BBoxTuple", "ServiceConfig",
    
    # Lower-level API (for advanced users)
    "validate_bbox", "bbox_intersects", "bbox_union", "bbox_intersection",
    "create_tile_grid", "estimate_tile_size", "format_supports_crs",
    "get_supported_crs_for_format", "get_supported_formats_for_crs",
    
    # Types and Models
    "CRS", "Format", "BoundingBox", "SpatialExtent", "TemporalExtent",
    "CoverageDescription", "ServiceCapabilities", "TileRequest", "TileResponse", "WCSResponse",
    
    # Generic Tile Functionality
    "fetch_tile", "save_tile", "create_tile_grid_for_bbox", "estimate_optimal_tile_size",
    
    # Generic Array Functionality
    "create_array", "create_dataset",
    
    # OGC Implementations
    "WCSParser", "WCSClient", "WCSTileAdapter", "WMSTileAdapter", "WMTSAdapter",
    
    # Package info
    "__version__", "__author__", "__email__"
]