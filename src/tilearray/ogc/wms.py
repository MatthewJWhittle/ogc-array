"""
WMS (Web Map Service) tile request functionality.
"""

from typing import Union, List, Optional
from ..types import BoundingBox, CRS, Format, TileRequest


class WMSTileAdapter:
    """Adapter for WMS tile requests."""
    
    @staticmethod
    def create_tile_request(
        base_url: str,
        layers: Union[str, List[str]],
        bbox: BoundingBox,
        width: int = 256,
        height: int = 256,
        output_format: Format = Format.GEOTIFF,
        crs: Optional[CRS] = None,
        **kwargs
    ) -> TileRequest:
        """
        Create a WMS GetMap request.
        
        Args:
            base_url: WMS service base URL
            layers: Layer name(s) to request
            bbox: Bounding box for the tile
            width: Output width in pixels
            height: Output height in pixels
            output_format: Output format
            crs: Coordinate reference system
            **kwargs: Additional WMS parameters
            
        Returns:
            Tile request for WMS service
        """
        if isinstance(layers, list):
            layers = ','.join(layers)
        
        params = {
            'service': 'WMS',
            'version': kwargs.get('version', '1.3.0'),
            'request': 'GetMap',
            'layers': layers,
            'bbox': f'{bbox.min_x},{bbox.min_y},{bbox.max_x},{bbox.max_y}',
            'width': width,
            'height': height,
            'format': output_format.value,
            'crs': (crs or bbox.crs).value
        }
        
        # Add any additional WMS parameters
        params.update(kwargs)
        
        return TileRequest(
            url=base_url,
            params=params,
            output_format=output_format,
            crs=crs or bbox.crs
        )
