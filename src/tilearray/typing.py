"""Type aliases and protocols for TileArray."""

from typing import TypeAlias, Protocol, Tuple, Dict, Any, Union, List, Optional, Callable
import xarray as xr

# Type aliases for better user experience
BBoxTuple: TypeAlias = Tuple[float, float, float, float]  # (min_x, min_y, max_x, max_y)
ServiceConfig: TypeAlias = Dict[str, Any]
TileSize: TypeAlias = Tuple[int, int]  # (width, height)
CoordinateTuple: TypeAlias = Tuple[float, float]  # (x, y)

# Protocols for service interfaces
class TileService(Protocol):
    """Protocol for tile service adapters."""
    
    def create_tile_request(
        self,
        coverage_id: str,
        bbox: "BoundingBox",
        width: int,
        height: int,
        output_format: "Format",
        crs: Optional["CRS"] = None,
        **kwargs
    ) -> "TileRequest":
        """Create a tile request for this service."""
        ...


class ServiceClient(Protocol):
    """Protocol for service clients."""
    
    def get_capabilities(self) -> "ServiceCapabilities":
        """Get service capabilities."""
        ...
    
    def describe_coverage(self, coverage_id: str) -> "CoverageDescription":
        """Describe a coverage."""
        ...


# Import types that are used in protocols
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .types import BoundingBox, Format, CRS, TileRequest, ServiceCapabilities, CoverageDescription
