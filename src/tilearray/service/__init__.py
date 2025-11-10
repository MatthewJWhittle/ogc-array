"""Service abstractions and implementations for OGC-style tile services."""

from .base import BaseService, TileGeometry, detect_service_type, get_service, register_service
from .config import ServiceConfig, WCSConfig
from .wcs import WCSParser, WCSService

__all__ = [
    "BaseService",
    "TileGeometry",
    "detect_service_type",
    "get_service",
    "register_service",
    "ServiceConfig",
    "WCSConfig",
    "WCSParser",
    "WCSService",
]
