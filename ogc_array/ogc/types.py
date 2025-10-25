"""
OGC type definitions and models.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from enum import Enum


class CRS(str, Enum):
    """Common Coordinate Reference Systems."""
    EPSG_4326 = "EPSG:4326"
    EPSG_3857 = "EPSG:3857"
    EPSG_32633 = "EPSG:32633"
    EPSG_27700 = "EPSG:27700"


class Format(str, Enum):
    """Supported output formats."""
    GEOTIFF = "image/tiff"
    NETCDF = "application/netcdf"
    HDF5 = "application/x-hdf5"
    JSON = "application/json"


class BoundingBox(BaseModel):
    """Bounding box representation."""
    min_x: float = Field(..., description="Minimum X coordinate")
    min_y: float = Field(..., description="Minimum Y coordinate")
    max_x: float = Field(..., description="Maximum X coordinate")
    max_y: float = Field(..., description="Maximum Y coordinate")
    crs: CRS = Field(default=CRS.EPSG_4326, description="Coordinate Reference System")

    @model_validator(mode='after')
    def validate_coordinates(self):
        """Validate that min coordinates are less than max coordinates."""
        if self.min_x >= self.max_x:
            raise ValueError('min_x must be less than max_x')
        if self.min_y >= self.max_y:
            raise ValueError('min_y must be less than max_y')
        return self


class SpatialExtent(BaseModel):
    """Spatial extent information."""
    bbox: BoundingBox
    crs: CRS = Field(default=CRS.EPSG_4326)
    dimensions: int = Field(default=2, ge=2, le=3, description="Number of spatial dimensions")


class TemporalExtent(BaseModel):
    """Temporal extent information."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @model_validator(mode='after')
    def validate_temporal_order(self):
        """Validate that end_time is after start_time."""
        if self.end_time and self.start_time and self.end_time < self.start_time:
            raise ValueError('end_time must be after start_time')
        return self


class CoverageDescription(BaseModel):
    """Coverage description from WCS GetCapabilities."""
    identifier: str = Field(..., description="Coverage identifier")
    title: str = Field(..., description="Coverage title")
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    spatial_extent: SpatialExtent
    temporal_extent: Optional[TemporalExtent] = None
    supported_formats: List[Format] = Field(default_factory=list)
    supported_crs: List[CRS] = Field(default_factory=list)
    native_crs: CRS = Field(default=CRS.EPSG_4326)
    native_format: Format = Field(default=Format.GEOTIFF)


class ServiceCapabilities(BaseModel):
    """WCS service capabilities."""
    service_title: str
    service_abstract: Optional[str] = None
    service_keywords: List[str] = Field(default_factory=list)
    service_provider: Optional[str] = None
    service_contact: Optional[str] = None
    service_url: str
    version: str = Field(default="2.0.1")
    supported_versions: List[str] = Field(default_factory=lambda: ["2.0.1", "2.0.0"])
    supported_operations: List[str] = Field(default_factory=lambda: ["GetCapabilities", "DescribeCoverage", "GetCoverage"])
    supported_formats: List[Format] = Field(default_factory=list)
    supported_crs: List[CRS] = Field(default_factory=list)
    coverages: List[CoverageDescription] = Field(default_factory=list)


class TileRequest(BaseModel):
    """Tile request parameters."""
    coverage_id: str = Field(..., description="Coverage identifier")
    bbox: BoundingBox = Field(..., description="Bounding box for the tile")
    width: int = Field(..., gt=0, description="Output width in pixels")
    height: int = Field(..., gt=0, description="Output height in pixels")
    format: Format = Field(default=Format.GEOTIFF, description="Output format")
    crs: CRS = Field(default=CRS.EPSG_4326, description="Output CRS")
    subset: Optional[Dict[str, Any]] = Field(default=None, description="Additional subset parameters")
    interpolation: str = Field(default="nearest", description="Interpolation method")
    
    def to_wcs_params(self) -> Dict[str, Any]:
        """Convert to WCS GetCoverage parameters."""
        return {
            "service": "WCS",
            "version": "2.0.1",
            "request": "GetCoverage",
            "coverageId": self.coverage_id,
            "subset": f"Long({self.bbox.min_x},{self.bbox.max_x})",
            "subset": f"Lat({self.bbox.min_y},{self.bbox.max_y})",
            "size": f"{self.width},{self.height}",
            "format": self.format.value,
            "crs": self.crs.value,
            "interpolation": self.interpolation
        }


class WCSResponse(BaseModel):
    """WCS response wrapper."""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
