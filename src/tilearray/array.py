"""
Generic array building functionality for geospatial services.

This module provides utilities for creating xarray objects with Dask chunks
from various geospatial tile services.
"""

from typing import Optional, Callable, Tuple, Union, Dict, Any
import numpy as np
import xarray as xr
import dask.array as da
from dask.delayed import delayed

from .types import BoundingBox, CRS, Format, TileRequest, TileResponse
from .tiles import fetch_tile


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
    from .core import create_tile_grid
    
    # Create tile grid
    x_coords, y_coords, grid_shape = create_tile_grid(bbox, chunk_size)
    
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
    
    # Create coordinate arrays
    x_coords_final = np.linspace(bbox.min_x, bbox.max_x, data_array.shape[1])
    y_coords_final = np.linspace(bbox.min_y, bbox.max_y, data_array.shape[0])
    
    # Create xarray DataArray
    return xr.DataArray(
        data_array,
        coords={
            'y': y_coords_final,
            'x': x_coords_final
        },
        dims=['y', 'x'],
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