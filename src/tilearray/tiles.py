"""
Generic tile fetching functionality for geospatial services.
"""

from typing import Dict, Any, Optional, Union, Tuple, List
from dataclasses import dataclass
import requests
import logging
from pathlib import Path

from .types import BoundingBox, CRS, Format, TileRequest, TileResponse

logger = logging.getLogger(__name__)


def fetch_tile(request: TileRequest) -> TileResponse:
    """
    Generic function to fetch a tile from any geospatial service.
    
    Args:
        request: Tile request parameters
        
    Returns:
        Tile response with data or error information
        
    Raises:
        requests.RequestException: For network-related errors
        ValueError: For invalid request parameters
    """
    if not request.url:
        raise ValueError("URL is required")
    
    if not request.params:
        raise ValueError("Request parameters are required")
    
    # Prepare headers
    headers = request.headers or {}
    if request.output_format:
        headers.setdefault('Accept', request.output_format.value)
    
    # Make the request with retries
    last_exception = None
    for attempt in range(request.retries + 1):
        try:
            logger.debug(f"Fetching tile (attempt {attempt + 1}/{request.retries + 1}): {request.url}")
            
            response = requests.get(
                request.url,
                params=request.params,
                headers=headers,
                timeout=request.timeout,
                stream=True  # For large tiles
            )
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.content
                return TileResponse(
                    data=data,
                    content_type=response.headers.get('content-type', ''),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    url=response.url,
                    success=True
                )
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning(f"Tile request failed: {error_msg}")
                
                if attempt == request.retries:  # Last attempt
                    return TileResponse(
                        data=b'',
                        content_type=response.headers.get('content-type', ''),
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        url=response.url,
                        success=False,
                        error_message=error_msg
                    )
                
        except requests.RequestException as e:
            last_exception = e
            logger.warning(f"Tile request attempt {attempt + 1} failed: {e}")
            
            if attempt == request.retries:  # Last attempt
                return TileResponse(
                    data=b'',
                    content_type='',
                    status_code=0,
                    headers={},
                    url=request.url,
                    success=False,
                    error_message=f"Network error: {str(e)}"
                )
    
    # This should never be reached, but just in case
    return TileResponse(
        data=b'',
        content_type='',
        status_code=0,
        headers={},
        url=request.url,
        success=False,
        error_message=f"All retry attempts failed: {str(last_exception)}"
    )


def save_tile(tile_response: TileResponse, output_path: Union[str, Path]) -> bool:
    """
    Save tile data to file.
    
    Args:
        tile_response: Response from tile request
        output_path: Path to save the tile
        
    Returns:
        True if successful, False otherwise
    """
    if not tile_response.success:
        logger.error(f"Cannot save failed tile: {tile_response.error_message}")
        return False
    
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(tile_response.data)
        
        logger.debug(f"Saved tile to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save tile to {output_path}: {e}")
        return False


# Utility functions for tile grid generation
def create_tile_grid_for_bbox(
    bbox: BoundingBox,
    tile_size: float,
    overlap: float = 0.0
) -> List[BoundingBox]:
    """
    Create a grid of tiles covering a bounding box.
    
    Args:
        bbox: Overall bounding box
        tile_size: Size of each tile in degrees
        overlap: Overlap between tiles in degrees
        
    Returns:
        List of tile bounding boxes
    """
    from .core import create_tile_grid
    return create_tile_grid(bbox, tile_size, overlap)


def estimate_optimal_tile_size(
    bbox: BoundingBox,
    target_pixels: int = 256
) -> float:
    """
    Estimate optimal tile size for a bounding box.
    
    Args:
        bbox: Bounding box
        target_pixels: Target number of pixels per side
        
    Returns:
        Suggested tile size in degrees
    """
    from .core import estimate_tile_size
    return estimate_tile_size(bbox, target_pixels)
