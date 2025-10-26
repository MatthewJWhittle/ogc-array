"""
WMTS (Web Map Tile Service) tile request functionality.
"""

from typing import Optional
from ..types import BoundingBox, CRS, Format, TileRequest


class WMTSAdapter:
    """Adapter for WMTS tile requests."""
    
    @staticmethod
    def create_tile_request(
        base_url: str,
        layer: str,
        tile_matrix_set: str,
        tile_matrix: str,
        tile_row: int,
        tile_col: int,
        output_format: Format = Format.GEOTIFF,
        **kwargs
    ) -> TileRequest:
        """
        Create a WMTS GetTile request.
        
        Args:
            base_url: WMTS service base URL
            layer: Layer identifier
            tile_matrix_set: Tile matrix set identifier
            tile_matrix: Tile matrix identifier
            tile_row: Tile row index
            tile_col: Tile column index
            output_format: Output format
            **kwargs: Additional WMTS parameters
            
        Returns:
            Tile request for WMTS service
        """
        params = {
            'service': 'WMTS',
            'version': kwargs.get('version', '1.0.0'),
            'request': 'GetTile',
            'layer': layer,
            'tilematrixset': tile_matrix_set,
            'tilematrix': tile_matrix,
            'tilerow': tile_row,
            'tilecol': tile_col,
            'format': output_format.value
        }
        
        # Add any additional WMTS parameters
        params.update(kwargs)
        
        return TileRequest(
            url=base_url,
            params=params,
            output_format=output_format
        )
