"""
Generic type definitions and models for tile-based geospatial data processing.
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
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Optional dimension details")


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
    title: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    supported_crs: List[CRS] = Field(default_factory=list)
    supported_formats: List[Format] = Field(default_factory=list)
    spatial_extent: Optional[SpatialExtent] = None
    temporal_extent: Optional[TemporalExtent] = None


class ServiceCapabilities(BaseModel):
    """WCS Service Capabilities."""
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
    """Generic tile request parameters."""
    url: str
    params: Dict[str, Any]
    headers: Optional[Dict[str, str]] = None
    timeout: int = 30
    retries: int = 3
    output_format: Optional[Format] = None
    crs: Optional[CRS] = None


class TileResponse(BaseModel):
    """Response from tile request."""
    data: bytes
    content_type: str
    status_code: int
    headers: Dict[str, str]
    url: str
    success: bool
    error_message: Optional[str] = None


class WCSResponse(BaseModel):
    """Represents a WCS response, either successful data or an error."""
    success: bool = Field(..., description="True if the request was successful, False otherwise")
    data: Optional[Any] = Field(None, description="The response data (e.g., image bytes, NetCDF data)")
    error_message: Optional[str] = Field(None, description="Error message if the request failed")
    status_code: Optional[int] = Field(None, description="HTTP status code of the response")
