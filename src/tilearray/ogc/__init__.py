"""
OGC (Open Geospatial Consortium) specific implementations.

This module contains OGC-specific adapters and parsers for WCS, WMS, and WMTS services.
"""

from .wcs import WCSParser, WCSClient, WCSTileAdapter
from .wms import WMSTileAdapter
from .wmts import WMTSAdapter

__all__ = [
    "WCSParser",
    "WCSClient", 
    "WCSTileAdapter",
    "WMSTileAdapter",
    "WMTSAdapter"
]
