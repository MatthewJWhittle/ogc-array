"""
Core generic functionality for tile-based geospatial data processing.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from .types import CRS, BoundingBox, Format

# Type aliases for better user experience
BBoxTuple = Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
ServiceConfig = Dict[str, Any]

logger = logging.getLogger(__name__)


# Bounding Box Operations
def validate_bbox(bbox: BoundingBox) -> bool:
    """
    Validate bounding box coordinates.

    Args:
        bbox: Bounding box to validate

    Returns:
        True if valid, False otherwise
    """
    if bbox.min_x >= bbox.max_x:
        return False
    if bbox.min_y >= bbox.max_y:
        return False
    return True


def bbox_intersects(bbox1: BoundingBox, bbox2: BoundingBox) -> bool:
    """
    Check if two bounding boxes intersect.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        True if bounding boxes intersect
    """
    return not (bbox1.max_x < bbox2.min_x or
               bbox1.min_x > bbox2.max_x or
               bbox1.max_y < bbox2.min_y or
               bbox1.min_y > bbox2.max_y)


def bbox_union(bbox1: BoundingBox, bbox2: BoundingBox) -> BoundingBox:
    """
    Create union of two bounding boxes.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        Union bounding box

    Raises:
        ValueError: If bounding boxes have different CRS
    """
    if bbox1.crs != bbox2.crs:
        raise ValueError(f"Cannot union bounding boxes with different CRS: {bbox1.crs} vs {bbox2.crs}")

    return BoundingBox(
        min_x=min(bbox1.min_x, bbox2.min_x),
        min_y=min(bbox1.min_y, bbox2.min_y),
        max_x=max(bbox1.max_x, bbox2.max_x),
        max_y=max(bbox1.max_y, bbox2.max_y),
        crs=bbox1.crs
    )


def bbox_intersection(bbox1: BoundingBox, bbox2: BoundingBox) -> Optional[BoundingBox]:
    """
    Create intersection of two bounding boxes.

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        Intersection bounding box, or None if no intersection

    Raises:
        ValueError: If bounding boxes have different CRS
    """
    if bbox1.crs != bbox2.crs:
        raise ValueError(f"Cannot intersect bounding boxes with different CRS: {bbox1.crs} vs {bbox2.crs}")

    if not bbox_intersects(bbox1, bbox2):
        return None

    return BoundingBox(
        min_x=max(bbox1.min_x, bbox2.min_x),
        min_y=max(bbox1.min_y, bbox2.min_y),
        max_x=min(bbox1.max_x, bbox2.max_x),
        max_y=min(bbox1.max_y, bbox2.max_y),
        crs=bbox1.crs
    )


# Tile Operations
def create_tile_grid(bbox: BoundingBox, tile_size: float, overlap: float = 0.0) -> List[BoundingBox]:
    """
    Create a grid of tiles covering the bounding box.

    Args:
        bbox: Overall bounding box
        tile_size: Size of each tile in degrees
        overlap: Overlap between tiles in degrees

    Returns:
        List of tile bounding boxes

    Raises:
        ValueError: If tile_size or overlap are negative
    """
    if tile_size <= 0:
        raise ValueError("tile_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= tile_size:
        raise ValueError("overlap must be less than tile_size")

    tiles = []
    x = bbox.min_x
    y = bbox.min_y

    while y < bbox.max_y:
        while x < bbox.max_x:
            tile_bbox = BoundingBox(
                min_x=x,
                min_y=y,
                max_x=min(x + tile_size, bbox.max_x),
                max_y=min(y + tile_size, bbox.max_y),
                crs=bbox.crs
            )
            tiles.append(tile_bbox)
            x += tile_size - overlap

        x = bbox.min_x
        y += tile_size - overlap

    return tiles


def estimate_tile_size(bbox: BoundingBox, target_pixels: int = 256) -> float:
    """
    Estimate appropriate tile size based on bounding box and target pixels.

    Args:
        bbox: Bounding box
        target_pixels: Target number of pixels per side

    Returns:
        Suggested tile size in degrees

    Raises:
        ValueError: If target_pixels is not positive
    """
    if target_pixels <= 0:
        raise ValueError("target_pixels must be positive")

    width = bbox.max_x - bbox.min_x
    height = bbox.max_y - bbox.min_y

    # Use the larger dimension to determine tile size
    max_dimension = max(width, height)
    tile_size = max_dimension / target_pixels

    # Round to reasonable values
    if tile_size < 0.001:
        return 0.001
    elif tile_size < 0.01:
        return 0.01
    elif tile_size < 0.1:
        return 0.1
    else:
        return round(tile_size, 1)


# Format and CRS Operations
def format_supports_crs(format_type: Format, crs: CRS) -> bool:
    """
    Check if a format supports a specific CRS.

    Args:
        format_type: Output format
        crs: Coordinate reference system

    Returns:
        True if format supports CRS
    """
    # This is a simplified check - in reality, this would depend on the specific service
    format_crs_mapping = {
        Format.GEOTIFF: [CRS.EPSG_4326, CRS.EPSG_3857, CRS.EPSG_32633],
        Format.NETCDF: [CRS.EPSG_4326],
        Format.HDF5: [CRS.EPSG_4326],
        Format.JSON: [CRS.EPSG_4326]
    }

    supported_crs = format_crs_mapping.get(format_type, [])
    return crs in supported_crs if supported_crs else True


def get_supported_crs_for_format(format_type: Format) -> List[CRS]:
    """
    Get list of supported CRS for a given format.

    Args:
        format_type: Output format

    Returns:
        List of supported CRS
    """
    format_crs_mapping = {
        Format.GEOTIFF: [CRS.EPSG_4326, CRS.EPSG_3857, CRS.EPSG_32633],
        Format.NETCDF: [CRS.EPSG_4326],
        Format.HDF5: [CRS.EPSG_4326],
        Format.JSON: [CRS.EPSG_4326]
    }

    return format_crs_mapping.get(format_type, list(CRS))


def get_supported_formats_for_crs(crs: CRS) -> List[Format]:
    """
    Get list of supported formats for a given CRS.

    Args:
        crs: Coordinate reference system

    Returns:
        List of supported formats
    """
    supported_formats = []
    for format_type in Format:
        if format_supports_crs(format_type, crs):
            supported_formats.append(format_type)
    return supported_formats


# User-friendly API functions
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
