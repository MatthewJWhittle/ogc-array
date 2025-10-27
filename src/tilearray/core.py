"""
Core generic functionality for tile-based geospatial data processing.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from pyproj.transformer import Transformer
import numpy as np

from .types import CRS, BoundingBox, Format, BBoxTuple

logger = logging.getLogger(__name__)


# Bounding Box Operations


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


def parse_bbox(bbox: Union[BBoxTuple, BoundingBox], crs: CRS) -> BoundingBox:
    """
    Parse a bounding box from various input formats.
    
    Args:
        bbox: Bounding box as tuple (min_x, min_y, max_x, max_y) or BoundingBox object
        crs: Coordinate reference system
        
    Returns:
        BoundingBox object
    """
    if isinstance(bbox, BoundingBox):
        return bbox

    if isinstance(bbox, tuple) and len(bbox) == 4:
        return create_bbox(bbox[0], bbox[1], bbox[2], bbox[3], crs)

    raise ValueError(f"Invalid bbox format: {bbox}. Expected tuple (min_x, min_y, max_x, max_y) or BoundingBox")

def transform_bbox(bbox: BoundingBox, src_crs: CRS, dst_crs: CRS) -> BoundingBox:
    """
    Transform a bounding box from one CRS to another.
    
    Args:
        bbox: Bounding box
        src_crs: Source coordinate reference system
        dst_crs: Destination coordinate reference system
    """
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    xmin, ymin = transformer.transform(bbox.min_x, bbox.min_y)
    xmax, ymax = transformer.transform(bbox.max_x, bbox.max_y)
    return BoundingBox(
        min_x=xmin,
        min_y=ymin,
        max_x=xmax,
        max_y=ymax,
        crs=dst_crs
    )