"""
Generic array building functionality for geospatial services.

This module provides utilities for creating xarray objects with Dask chunks
from various geospatial tile services.
"""

from typing import Optional, Callable, Tuple, Union, Dict, Any, List
import numpy as np
import xarray as xr
import dask.array as da
from dask.delayed import delayed

from .types import BoundingBox, CRS, Format, TileRequest, TileResponse
from .tiles import fetch_tile
from .core import parse_bbox, BBoxTuple, ServiceConfig


def create_array(
    service_url: str,
    coverage_id: str,
    bbox: BoundingBox,
    service_type: str = "WCS",
    chunk_size: Tuple[int, int] = (256, 256),
    output_format: Format = Format.GEOTIFF,
    crs: Optional[CRS] = None,
    adapter_class: Optional[Callable] = None,
    **kwargs
) -> xr.DataArray:
    """
    Create an xarray DataArray from a geospatial service.

    Args:
        service_url: Base URL of the geospatial service
        coverage_id: Coverage/layer identifier
        bbox: Bounding box for the data
        service_type: Type of service (WCS, WMS, WMTS, etc.)
        chunk_size: Dask chunk size (width, height)
        output_format: Output format
        crs: Coordinate reference system
        adapter_class: Custom adapter class
        **kwargs: Additional parameters

    Returns:
        xarray.DataArray with Dask backend
    """
    from .core import create_tile_grid, estimate_tile_size
    
    # Convert chunk_size tuple to tile_size float
    if isinstance(chunk_size, tuple) and len(chunk_size) == 2:
        # Use the average of width and height as target pixels
        target_pixels = int((chunk_size[0] + chunk_size[1]) / 2)
        tile_size = estimate_tile_size(bbox, target_pixels)
    else:
        # If chunk_size is already a float, use it directly
        tile_size = float(chunk_size)
    
    # Create tile grid
    tile_bboxes = create_tile_grid(bbox, tile_size)
    
    # Extract unique coordinates and calculate grid shape
    x_coords = sorted(list(set([tile.min_x for tile in tile_bboxes] + [bbox.max_x])))
    y_coords = sorted(list(set([tile.min_y for tile in tile_bboxes] + [bbox.max_y])))
    
    # Calculate grid shape
    grid_shape = (len(x_coords) - 1, len(y_coords) - 1)
    
    # Create delayed functions for each tile
    delayed_tiles = []
    for i in range(grid_shape[0]):
        row_tiles = []
        for j in range(grid_shape[1]):
            # Calculate tile bounding box
            tile_min_x = x_coords[i]
            tile_max_x = x_coords[i + 1] if i + 1 < len(x_coords) else bbox.max_x
            tile_min_y = y_coords[j]
            tile_max_y = y_coords[j + 1] if j + 1 < len(y_coords) else bbox.max_y
            
            tile_bbox = BoundingBox(
                min_x=tile_min_x,
                min_y=tile_min_y,
                max_x=tile_max_x,
                max_y=tile_max_y,
                crs=crs or bbox.crs
            )
            
            # Create delayed tile fetch
            delayed_tile = _fetch_tile_delayed(
                service_url, coverage_id, tile_bbox, chunk_size[0], chunk_size[1], 
                output_format, crs, service_type, adapter_class, **kwargs
            )
            row_tiles.append(delayed_tile)
        delayed_tiles.append(row_tiles)
    
    # Convert to Dask array
    dask_arrays = [[da.from_delayed(tile, shape=chunk_size, dtype=np.float32) 
                    for tile in row] for row in delayed_tiles]
    
    # Stack arrays
    if len(dask_arrays) == 1 and len(dask_arrays[0]) == 1:
        # Single tile
        data_array = dask_arrays[0][0]
    else:
        # Multiple tiles - concatenate
        if len(dask_arrays) > 1:
            data_array = da.concatenate([da.stack(row, axis=1) for row in dask_arrays], axis=0)
        else:
            data_array = da.stack(dask_arrays[0], axis=1)
    
    # Create coordinate arrays based on data dimensions
    data_shape = data_array.shape
    
    if len(data_shape) == 1:
        # 1D data - single dimension
        coords = {
            'x': np.linspace(bbox.min_x, bbox.max_x, data_shape[0])
        }
        dims = ['x']
    elif len(data_shape) == 2:
        # 2D data - spatial dimensions
        coords = {
            'y': np.linspace(bbox.min_y, bbox.max_y, data_shape[0]),
            'x': np.linspace(bbox.min_x, bbox.max_x, data_shape[1])
        }
        dims = ['y', 'x']
    elif len(data_shape) == 3:
        # 3D data - spatial + additional dimension (e.g., bands, time, etc.)
        coords = {
            'y': np.linspace(bbox.min_y, bbox.max_y, data_shape[0]),
            'x': np.linspace(bbox.min_x, bbox.max_x, data_shape[1]),
            'band': np.arange(data_shape[2])  # Additional dimension
        }
        dims = ['y', 'x', 'band']
    else:
        # 4D+ data - handle generically
        coords = {}
        dims = []
        
        # First two dimensions are spatial
        coords['y'] = np.linspace(bbox.min_y, bbox.max_y, data_shape[0])
        coords['x'] = np.linspace(bbox.min_x, bbox.max_x, data_shape[1])
        dims.extend(['y', 'x'])
        
        # Additional dimensions
        for i in range(2, len(data_shape)):
            dim_name = f'dim_{i}'
            coords[dim_name] = np.arange(data_shape[i])
            dims.append(dim_name)
    
    # Create xarray DataArray
    return xr.DataArray(
        data_array,
        coords=coords,
        dims=dims,
        attrs={
            'crs': (crs or bbox.crs).value,
            'service_url': service_url,
            'coverage_id': coverage_id,
            'service_type': service_type
        }
    )


def create_dataset(
    service_url: str,
    coverage_id: str,
    bbox: BoundingBox,
    service_type: str = "WCS",
    chunk_size: Tuple[int, int] = (256, 256),
    output_format: Format = Format.GEOTIFF,
    crs: Optional[CRS] = None,
    adapter_class: Optional[Callable] = None,
    **kwargs
) -> xr.Dataset:
    """
    Create an xarray Dataset from a geospatial service.

    Args:
        service_url: Base URL of the geospatial service
        coverage_id: Coverage/layer identifier
        bbox: Bounding box for the data
        service_type: Type of service (WCS, WMS, WMTS, etc.)
        chunk_size: Dask chunk size (width, height)
        output_format: Output format
        crs: Coordinate reference system
        adapter_class: Custom adapter class
        **kwargs: Additional parameters

    Returns:
        xarray.Dataset with Dask backend
    """
    data_array = create_array(
        service_url=service_url,
        coverage_id=coverage_id,
        bbox=bbox,
        service_type=service_type,
        chunk_size=chunk_size,
        output_format=output_format,
        crs=crs,
        adapter_class=adapter_class,
        **kwargs
    )
    
    return xr.Dataset({coverage_id: data_array})


def _fetch_tile_delayed(
    service_url: str,
    coverage_id: str,
    tile_bbox: BoundingBox,
    width: int,
    height: int,
    output_format: Format,
    crs: Optional[CRS],
    service_type: str,
    adapter_class: Optional[Callable],
    **kwargs
):
    """
    Create a delayed function for fetching a single tile.

    Args:
        service_url: Base URL of the geospatial service
        coverage_id: Coverage/layer identifier
        tile_bbox: Bounding box for this tile
        width: Tile width in pixels
        height: Tile height in pixels
        output_format: Output format
        crs: Coordinate reference system
        service_type: Type of service
        adapter_class: Custom adapter class
        **kwargs: Additional parameters

    Returns:
        Delayed function that returns tile data
    """
    @delayed
    def fetch_and_parse_tile():
        """Fetch and parse a single tile."""
        try:
            # Create tile request using adapter
            if adapter_class:
                adapter = adapter_class(service_url)
                request = adapter.create_tile_request(
                    coverage_id=coverage_id,
                    bbox=tile_bbox,
                    width=width,
                    height=height,
                    output_format=output_format,
                    crs=crs
                )
            else:
                # Fallback to generic tile request
                request = TileRequest(
                    url=service_url,
                    params={
                        'service': service_type,
                        'coverageId': coverage_id,
                        'bbox': f"{tile_bbox.min_x},{tile_bbox.min_y},{tile_bbox.max_x},{tile_bbox.max_y}",
                        'width': str(width),
                        'height': str(height),
                        'format': output_format.value
                    }
                )

            # Fetch tile
            response = fetch_tile(request)
            
            if response.success:
                return _parse_tile_data(response.data, output_format)
            else:
                # Return NaN array for failed tiles
                return np.full((height, width), np.nan, dtype=np.float32)
                
        except Exception as e:
            print(f"Error fetching tile {tile_bbox}: {e}")
            return np.full((height, width), np.nan, dtype=np.float32)

    return fetch_and_parse_tile()


def _parse_tile_data(data: bytes, output_format: Format) -> np.ndarray:
    """
    Parse tile data based on format.

    Args:
        data: Raw tile data
        output_format: Output format

    Returns:
        Parsed numpy array
    """
    if output_format == Format.GEOTIFF:
        return _parse_geotiff(data)
    elif output_format == Format.PNG:
        return _parse_png(data)
    elif output_format == Format.JPEG:
        return _parse_jpeg(data)
    else:
        # Fallback: try to parse as numpy array
        try:
            return np.frombuffer(data, dtype=np.float32)
        except:
            return np.array([])


def _parse_geotiff(data: bytes) -> np.ndarray:
    """Parse GeoTIFF data."""
    try:
        from PIL import Image
        import io
        
        # Try to open as image first
        img = Image.open(io.BytesIO(data))
        return np.array(img)
    except ImportError:
        # PIL not available, try basic parsing
        return np.frombuffer(data, dtype=np.float32)
    except Exception:
        return np.frombuffer(data, dtype=np.float32)


def _parse_png(data: bytes) -> np.ndarray:
    """Parse PNG data."""
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(data))
        return np.array(img)
    except ImportError:
        # PIL not available, return empty array
        return np.array([])
    except Exception:
        return np.array([])


def _parse_jpeg(data: bytes) -> np.ndarray:
    """Parse JPEG data."""
    try:
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(data))
        return np.array(img)
    except ImportError:
        # PIL not available, return empty array
        return np.array([])
    except Exception:
        return np.array([])

# User-friendly service creation functions
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
    from .ogc import WCSTileAdapter
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
    from .ogc import WMSTileAdapter
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
    from .ogc import WMTSAdapter
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


# User-friendly array loading functions
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
