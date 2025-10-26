"""
High-level user-friendly API for TileArray.

This module provides simple, intuitive functions for working with geospatial
tile services without requiring knowledge of internal Pydantic models or
service-specific details.
"""

from typing import Union, Tuple, Dict, Any, Optional, List
import xarray as xr

from .types import BoundingBox, CRS, Format
from .array import create_array, create_dataset
from .ogc import WCSTileAdapter, WMSTileAdapter, WMTSAdapter

# Type aliases for better user experience
BBoxTuple = Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
ServiceConfig = Dict[str, Any]


def create_bbox(
    min_x: float, 
    min_y: float, 
    max_x: float, 
    max_y: float, 
    crs: str = "EPSG:4326"
) -> BoundingBox:
    """
    Create a bounding box from simple coordinates.
    
    Args:
        min_x: Minimum X coordinate (west)
        min_y: Minimum Y coordinate (south) 
        max_x: Maximum X coordinate (east)
        max_y: Maximum Y coordinate (north)
        crs: Coordinate reference system (default: WGS84)
        
    Returns:
        BoundingBox object
        
    Raises:
        ValueError: If coordinates are invalid
    """
    try:
        crs_enum = CRS(crs)
    except ValueError as exc:
        raise ValueError(f"Unsupported CRS: {crs}") from exc
    
    return BoundingBox(
        min_x=min_x,
        min_y=min_y, 
        max_x=max_x,
        max_y=max_y,
        crs=crs_enum
    )


def parse_bbox(bbox: Union[BBoxTuple, BoundingBox], crs: str = "EPSG:4326") -> BoundingBox:
    """
    Parse a bounding box from various input formats.
    
    Args:
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox object
        crs: Coordinate reference system (ignored if bbox is already BoundingBox)
        
    Returns:
        BoundingBox object
    """
    if isinstance(bbox, BoundingBox):
        return bbox
    elif isinstance(bbox, (tuple, list)) and len(bbox) == 4:
        return create_bbox(bbox[0], bbox[1], bbox[2], bbox[3], crs)
    else:
        raise ValueError(f"Invalid bbox format: {bbox}. Expected tuple (min_x, min_y, max_x, max_y) or BoundingBox")


def create_wcs_service(
    url: str,
    coverage_id: str,
    resolution: Optional[Tuple[int, int]] = None,
    output_format: str = "image/tiff",
    crs: str = "EPSG:4326",
    **kwargs
) -> ServiceConfig:
    """
    Create a WCS service configuration.
    
    Args:
        url: WCS service URL
        coverage_id: Coverage identifier
        resolution: Optional (width, height) resolution override
        output_format: Output format (default: GeoTIFF)
        crs: Coordinate reference system
        **kwargs: Additional WCS parameters
        
    Returns:
        Service configuration dictionary
    """
    return {
        "type": "WCS",
        "url": url,
        "coverage_id": coverage_id,
        "resolution": resolution,
        "format": output_format,
        "crs": crs,
        "adapter_class": WCSTileAdapter,
        **kwargs
    }


def create_wms_service(
    url: str,
    layers: Union[str, List[str]],
    resolution: Optional[Tuple[int, int]] = None,
    output_format: str = "image/tiff",
    crs: str = "EPSG:4326",
    **kwargs
) -> ServiceConfig:
    """
    Create a WMS service configuration.
    
    Args:
        url: WMS service URL
        layers: Layer name(s) to request
        resolution: Optional (width, height) resolution override
        output_format: Output format (default: GeoTIFF)
        crs: Coordinate reference system
        **kwargs: Additional WMS parameters
        
    Returns:
        Service configuration dictionary
    """
    return {
        "type": "WMS",
        "url": url,
        "layers": layers,
        "resolution": resolution,
        "format": output_format,
        "crs": crs,
        "adapter_class": WMSTileAdapter,
        **kwargs
    }


def create_wmts_service(
    url: str,
    layer: str,
    tile_matrix_set: str,
    resolution: Optional[Tuple[int, int]] = None,
    output_format: str = "image/tiff",
    **kwargs
) -> ServiceConfig:
    """
    Create a WMTS service configuration.
    
    Args:
        url: WMTS service URL
        layer: Layer identifier
        tile_matrix_set: Tile matrix set identifier
        resolution: Optional (width, height) resolution override
        output_format: Output format (default: GeoTIFF)
        **kwargs: Additional WMTS parameters
        
    Returns:
        Service configuration dictionary
    """
    return {
        "type": "WMTS",
        "url": url,
        "layer": layer,
        "tile_matrix_set": tile_matrix_set,
        "resolution": resolution,
        "format": output_format,
        "adapter_class": WMTSAdapter,
        **kwargs
    }


def load_array(
    service: ServiceConfig,
    bbox: Union[BBoxTuple, BoundingBox],
    chunk_size: Tuple[int, int] = (256, 256),
    **kwargs
) -> xr.DataArray:
    """
    Load geospatial data as an xarray DataArray.
    
    Args:
        service: Service configuration (from create_wcs_service, etc.)
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox
        chunk_size: Dask chunk size (width, height)
        **kwargs: Additional parameters for the service
        
    Returns:
        xarray.DataArray with Dask backend
        
    Examples:
        >>> # Load from WCS service
        >>> service = create_wcs_service("http://example.com/wcs", "elevation")
        >>> data = load_array(service, (-1, 50, 1, 52))  # London area
        
        >>> # Load from WMS service  
        >>> service = create_wms_service("http://example.com/wms", "satellite")
        >>> data = load_array(service, (-1, 50, 1, 52), chunk_size=(512, 512))
    """
    # Parse bounding box
    parsed_bbox = parse_bbox(bbox, service.get("crs", "EPSG:4326"))
    
    # Get service parameters
    service_type = service["type"]
    service_url = service["url"]
    
    # Get coverage/layer identifier based on service type
    if service_type == "WCS":
        coverage_id = service["coverage_id"]
    elif service_type == "WMS":
        coverage_id = service["layers"]
    elif service_type == "WMTS":
        coverage_id = service["layer"]
    else:
        raise ValueError(f"Unsupported service type: {service_type}")
    
    # Get resolution override
    resolution = service.get("resolution")
    if resolution:
        chunk_size = resolution
    
    # Get format
    try:
        output_format = Format(service.get("format", "image/tiff"))
    except ValueError as exc:
        raise ValueError(f"Unsupported format: {service.get('format')}") from exc
    
    # Get CRS
    try:
        crs = CRS(service.get("crs", "EPSG:4326"))
    except ValueError as exc:
        raise ValueError(f"Unsupported CRS: {service.get('crs')}") from exc
    
    # Create array using the generic function
    return create_array(
        service_url=service_url,
        coverage_id=coverage_id,
        bbox=parsed_bbox,
        service_type=service_type,
        chunk_size=chunk_size,
        output_format=output_format,
        crs=crs,
        adapter_class=service.get("adapter_class"),
        **kwargs
    )


def load_dataset(
    service: ServiceConfig,
    bbox: Union[BBoxTuple, BoundingBox],
    chunk_size: Tuple[int, int] = (256, 256),
    **kwargs
) -> xr.Dataset:
    """
    Load geospatial data as an xarray Dataset.
    
    Args:
        service: Service configuration (from create_wcs_service, etc.)
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox
        chunk_size: Dask chunk size (width, height)
        **kwargs: Additional parameters for the service
        
    Returns:
        xarray.Dataset with Dask backend
    """
    # Parse bounding box
    parsed_bbox = parse_bbox(bbox, service.get("crs", "EPSG:4326"))
    
    # Get service parameters
    service_type = service["type"]
    service_url = service["url"]
    
    # Get coverage/layer identifier based on service type
    if service_type == "WCS":
        coverage_id = service["coverage_id"]
    elif service_type == "WMS":
        coverage_id = service["layers"]
    elif service_type == "WMTS":
        coverage_id = service["layer"]
    else:
        raise ValueError(f"Unsupported service type: {service_type}")
    
    # Get resolution override
    resolution = service.get("resolution")
    if resolution:
        chunk_size = resolution
    
    # Get format
    try:
        output_format = Format(service.get("format", "image/tiff"))
    except ValueError as exc:
        raise ValueError(f"Unsupported format: {service.get('format')}") from exc
    
    # Get CRS
    try:
        crs = CRS(service.get("crs", "EPSG:4326"))
    except ValueError as exc:
        raise ValueError(f"Unsupported CRS: {service.get('crs')}") from exc
    
    # Create dataset using the generic function
    return create_dataset(
        service_url=service_url,
        coverage_id=coverage_id,
        bbox=parsed_bbox,
        service_type=service_type,
        chunk_size=chunk_size,
        output_format=output_format,
        crs=crs,
        adapter_class=service.get("adapter_class"),
        **kwargs
    )


# Convenience functions for common use cases
def load_wcs_array(
    url: str,
    coverage_id: str,
    bbox: Union[BBoxTuple, BoundingBox],
    chunk_size: Tuple[int, int] = (256, 256),
    **kwargs
) -> xr.DataArray:
    """
    Convenience function to load data from a WCS service.
    
    Args:
        url: WCS service URL
        coverage_id: Coverage identifier
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox
        chunk_size: Dask chunk size (width, height)
        **kwargs: Additional parameters
        
    Returns:
        xarray.DataArray with Dask backend
    """
    service = create_wcs_service(url, coverage_id)
    return load_array(service, bbox, chunk_size, **kwargs)


def load_wms_array(
    url: str,
    layers: Union[str, List[str]],
    bbox: Union[BBoxTuple, BoundingBox],
    chunk_size: Tuple[int, int] = (256, 256),
    **kwargs
) -> xr.DataArray:
    """
    Convenience function to load data from a WMS service.
    
    Args:
        url: WMS service URL
        layers: Layer name(s) to request
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox
        chunk_size: Dask chunk size (width, height)
        **kwargs: Additional parameters
        
    Returns:
        xarray.DataArray with Dask backend
    """
    service = create_wms_service(url, layers)
    return load_array(service, bbox, chunk_size, **kwargs)
