"""
WCS (Web Coverage Service) XML parsing and tile request functionality.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import requests
from datetime import datetime
import logging

from .types import (
    ServiceCapabilities, CoverageDescription, SpatialExtent, TemporalExtent,
    BoundingBox, CRS, Format, TileRequest, WCSResponse
)

logger = logging.getLogger(__name__)


class WCSParser:
    """Parser for WCS XML responses."""
    
    def __init__(self, base_url: str):
        """
        Initialize WCS parser.
        
        Args:
            base_url: Base URL of the WCS service
        """
        self.base_url = base_url.rstrip('/')
        self.namespaces = {
            'wcs': 'http://www.opengis.net/wcs/2.0',
            'ows': 'http://www.opengis.net/ows/1.1',
            'gml': 'http://www.opengis.net/gml/3.2',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
    
    def parse_get_capabilities(self, xml_content: str) -> ServiceCapabilities:
        """
        Parse WCS GetCapabilities XML response.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            ServiceCapabilities object
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Parse service identification
            service_title = self._get_text(root, './/ows:ServiceIdentification/ows:Title')
            service_abstract = self._get_text(root, './/ows:ServiceIdentification/ows:Abstract')
            service_keywords = self._parse_keywords(root)
            service_provider = self._get_text(root, './/ows:ServiceProvider/ows:ProviderName')
            service_contact = self._get_text(root, './/ows:ServiceProvider/ows:ServiceContact/ows:ContactInfo/ows:ContactPersonPrimary/ows:ContactPerson')
            
            # Parse service URL
            service_url = self._get_text(root, './/ows:OperationsMetadata/ows:Operation[@name="GetCapabilities"]/ows:DCP/ows:HTTP/ows:Get/ows:OnlineResource', 'href')
            
            # Parse supported operations
            operations = self._parse_operations(root)
            
            # Parse supported formats and CRS
            supported_formats = self._parse_supported_formats(root)
            supported_crs = self._parse_supported_crs(root)
            
            # Parse coverages
            coverages = self._parse_coverages(root)
            
            return ServiceCapabilities(
                service_title=service_title or "WCS Service",
                service_abstract=service_abstract,
                service_keywords=service_keywords,
                service_provider=service_provider,
                service_contact=service_contact,
                service_url=service_url or self.base_url,
                supported_operations=operations,
                supported_formats=supported_formats,
                supported_crs=supported_crs,
                coverages=coverages
            )
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML content: {e}")
        except Exception as e:
            logger.error(f"Error parsing GetCapabilities: {e}")
            raise ValueError(f"Error parsing WCS capabilities: {e}")
    
    def parse_describe_coverage(self, xml_content: str) -> CoverageDescription:
        """
        Parse WCS DescribeCoverage XML response.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            CoverageDescription object
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Parse coverage identifier
            identifier = self._get_text(root, './/wcs:CoverageId')
            title = self._get_text(root, './/gml:name')
            abstract = self._get_text(root, './/gml:description')
            
            # Parse spatial extent
            spatial_extent = self._parse_spatial_extent(root)
            
            # Parse temporal extent
            temporal_extent = self._parse_temporal_extent(root)
            
            # Parse supported formats and CRS
            supported_formats = self._parse_coverage_formats(root)
            supported_crs = self._parse_coverage_crs(root)
            native_crs = self._parse_native_crs(root)
            native_format = self._parse_native_format(root)
            
            return CoverageDescription(
                identifier=identifier,
                title=title or identifier,
                abstract=abstract,
                spatial_extent=spatial_extent,
                temporal_extent=temporal_extent,
                supported_formats=supported_formats,
                supported_crs=supported_crs,
                native_crs=native_crs,
                native_format=native_format
            )
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML content: {e}")
        except Exception as e:
            logger.error(f"Error parsing DescribeCoverage: {e}")
            raise ValueError(f"Error parsing coverage description: {e}")
    
    def _get_text(self, element: ET.Element, xpath: str, attr: Optional[str] = None) -> Optional[str]:
        """Get text content or attribute value from XML element."""
        try:
            found = element.find(xpath, self.namespaces)
            if found is not None:
                if attr:
                    return found.get(attr)
                return found.text
        except Exception:
            pass
        return None
    
    def _parse_keywords(self, root: ET.Element) -> List[str]:
        """Parse keywords from XML."""
        keywords = []
        keyword_elements = root.findall('.//ows:Keywords/ows:Keyword', self.namespaces)
        for elem in keyword_elements:
            if elem.text:
                keywords.append(elem.text.strip())
        return keywords
    
    def _parse_operations(self, root: ET.Element) -> List[str]:
        """Parse supported operations."""
        operations = []
        op_elements = root.findall('.//ows:OperationsMetadata/ows:Operation', self.namespaces)
        for elem in op_elements:
            name = elem.get('name')
            if name:
                operations.append(name)
        return operations
    
    def _parse_supported_formats(self, root: ET.Element) -> List[Format]:
        """Parse supported formats."""
        formats = []
        format_elements = root.findall('.//wcs:SupportedFormat', self.namespaces)
        for elem in format_elements:
            if elem.text:
                try:
                    formats.append(Format(elem.text.strip()))
                except ValueError:
                    # Skip unsupported formats
                    pass
        return formats
    
    def _parse_supported_crs(self, root: ET.Element) -> List[CRS]:
        """Parse supported CRS."""
        crs_list = []
        crs_elements = root.findall('.//wcs:SupportedCRS', self.namespaces)
        for elem in crs_elements:
            if elem.text:
                try:
                    crs_list.append(CRS(elem.text.strip()))
                except ValueError:
                    # Skip unsupported CRS
                    pass
        return crs_list
    
    def _parse_coverages(self, root: ET.Element) -> List[CoverageDescription]:
        """Parse coverage descriptions."""
        coverages = []
        coverage_elements = root.findall('.//wcs:CoverageSummary', self.namespaces)
        
        for elem in coverage_elements:
            try:
                identifier = self._get_text(elem, './/wcs:Identifier')
                title = self._get_text(elem, './/wcs:Title')
                abstract = self._get_text(elem, './/wcs:Abstract')
                
                # Parse bounding box
                bbox_elem = elem.find('.//ows:WGS84BoundingBox', self.namespaces)
                if bbox_elem is not None:
                    min_x = float(self._get_text(bbox_elem, './/ows:LowerCorner').split()[0])
                    min_y = float(self._get_text(bbox_elem, './/ows:LowerCorner').split()[1])
                    max_x = float(self._get_text(bbox_elem, './/ows:UpperCorner').split()[0])
                    max_y = float(self._get_text(bbox_elem, './/ows:UpperCorner').split()[1])
                    
                    bbox = BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
                    spatial_extent = SpatialExtent(bbox=bbox)
                    
                    coverage = CoverageDescription(
                        identifier=identifier,
                        title=title or identifier,
                        abstract=abstract,
                        spatial_extent=spatial_extent
                    )
                    coverages.append(coverage)
                    
            except Exception as e:
                logger.warning(f"Error parsing coverage {identifier}: {e}")
                continue
        
        return coverages
    
    def _parse_spatial_extent(self, root: ET.Element) -> SpatialExtent:
        """Parse spatial extent from coverage description."""
        # Look for bounding box in various formats
        bbox_elem = root.find('.//gml:Envelope', self.namespaces)
        if bbox_elem is not None:
            lower_corner = self._get_text(bbox_elem, './/gml:lowerCorner')
            upper_corner = self._get_text(bbox_elem, './/gml:upperCorner')
            
            if lower_corner and upper_corner:
                min_coords = [float(x) for x in lower_corner.split()]
                max_coords = [float(x) for x in upper_corner.split()]
                
                bbox = BoundingBox(
                    min_x=min_coords[0],
                    min_y=min_coords[1],
                    max_x=max_coords[0],
                    max_y=max_coords[1]
                )
                return SpatialExtent(bbox=bbox)
        
        # Default extent if not found
        return SpatialExtent(bbox=BoundingBox(min_x=-180, min_y=-90, max_x=180, max_y=90))
    
    def _parse_temporal_extent(self, root: ET.Element) -> Optional[TemporalExtent]:
        """Parse temporal extent from coverage description."""
        # Look for temporal extent elements
        time_elem = root.find('.//gml:TimePeriod', self.namespaces)
        if time_elem is not None:
            begin = self._get_text(time_elem, './/gml:beginPosition')
            end = self._get_text(time_elem, './/gml:endPosition')
            
            if begin or end:
                start_time = datetime.fromisoformat(begin.replace('Z', '+00:00')) if begin else None
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00')) if end else None
                return TemporalExtent(start_time=start_time, end_time=end_time)
        
        return None
    
    def _parse_coverage_formats(self, root: ET.Element) -> List[Format]:
        """Parse supported formats for a specific coverage."""
        formats = []
        format_elements = root.findall('.//wcs:SupportedFormat', self.namespaces)
        for elem in format_elements:
            if elem.text:
                try:
                    formats.append(Format(elem.text.strip()))
                except ValueError:
                    pass
        return formats
    
    def _parse_coverage_crs(self, root: ET.Element) -> List[CRS]:
        """Parse supported CRS for a specific coverage."""
        crs_list = []
        crs_elements = root.findall('.//wcs:SupportedCRS', self.namespaces)
        for elem in crs_elements:
            if elem.text:
                try:
                    crs_list.append(CRS(elem.text.strip()))
                except ValueError:
                    pass
        return crs_list
    
    def _parse_native_crs(self, root: ET.Element) -> CRS:
        """Parse native CRS for coverage."""
        native_crs = self._get_text(root, './/wcs:NativeCRS')
        if native_crs:
            try:
                return CRS(native_crs.strip())
            except ValueError:
                pass
        return CRS.EPSG_4326  # Default
    
    def _parse_native_format(self, root: ET.Element) -> Format:
        """Parse native format for coverage."""
        native_format = self._get_text(root, './/wcs:NativeFormat')
        if native_format:
            try:
                return Format(native_format.strip())
            except ValueError:
                pass
        return Format.GEOTIFF  # Default


class WCSClient:
    """Client for WCS operations."""
    
    def __init__(self, base_url: str):
        """
        Initialize WCS client.
        
        Args:
            base_url: Base URL of the WCS service
        """
        self.base_url = base_url.rstrip('/')
        self.parser = WCSParser(base_url)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ogc-array/0.1.0'})
    
    def get_capabilities(self) -> ServiceCapabilities:
        """
        Get WCS service capabilities.
        
        Returns:
            ServiceCapabilities object
        """
        params = {
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'GetCapabilities'
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        return self.parser.parse_get_capabilities(response.text)
    
    def describe_coverage(self, coverage_id: str) -> CoverageDescription:
        """
        Describe a specific coverage.
        
        Args:
            coverage_id: Coverage identifier
            
        Returns:
            CoverageDescription object
        """
        params = {
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'DescribeCoverage',
            'coverageId': coverage_id
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        return self.parser.parse_describe_coverage(response.text)
    
    def get_coverage(self, tile_request: TileRequest) -> WCSResponse:
        """
        Get coverage data for a tile request.
        
        Args:
            tile_request: Tile request parameters
            
        Returns:
            WCSResponse object
        """
        try:
            params = tile_request.to_wcs_params()
            response = self.session.get(self.base_url, params=params, stream=True)
            response.raise_for_status()
            
            return WCSResponse(
                success=True,
                data=response.content,
                content_type=response.headers.get('Content-Type'),
                content_length=int(response.headers.get('Content-Length', 0)),
                metadata={
                    'url': response.url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            )
            
        except requests.RequestException as e:
            logger.error(f"WCS request failed: {e}")
            return WCSResponse(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return WCSResponse(
                success=False,
                error_message=f"Unexpected error: {e}"
            )
