"""
WCS (Web Coverage Service) XML parsing and tile request functionality.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urljoin, urlparse
import requests
from datetime import datetime
import logging

from ..types import (
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
            service_keywords = self._get_keywords(root)
            service_provider = self._get_text(root, './/ows:ServiceProvider/ows:ProviderName')
            service_contact = self._get_text(root, './/ows:ServiceProvider/ows:ServiceContact/ows:ContactInfo/ows:ContactPersonPrimary/ows:ContactPerson')
            
            # Parse supported operations
            operations = []
            for op in root.findall('.//ows:Operation', self.namespaces):
                op_name = op.get('name')
                if op_name:
                    operations.append(op_name)
            
            # Parse supported formats
            supported_formats = self._parse_supported_formats(root)
            
            # Parse supported CRS
            supported_crs = self._parse_supported_crs(root)
            
            # Parse coverages
            coverages = self._parse_coverages(root)
            
            return ServiceCapabilities(
                service_title=service_title or "WCS Service",
                service_abstract=service_abstract,
                service_keywords=service_keywords,
                service_provider=service_provider,
                service_contact=service_contact,
                service_url=self.base_url,
                supported_operations=operations,
                supported_formats=supported_formats,
                supported_crs=supported_crs,
                coverages=coverages
            )
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
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
            
            # Find the coverage description
            coverage_elem = root.find('.//wcs:CoverageDescription', self.namespaces)
            if coverage_elem is None:
                # Try to find it as the root element
                if root.tag.endswith('CoverageDescription'):
                    coverage_elem = root
                else:
                    raise ValueError("No coverage description found in XML")
            
            # Parse coverage identifier
            identifier = self._get_text(coverage_elem, './/gml:identifier')
            if not identifier:
                # Try wcs:CoverageId as fallback
                identifier = self._get_text(coverage_elem, './/wcs:CoverageId')
            if not identifier:
                raise ValueError("Coverage identifier not found")
            
            # Parse title and abstract
            title = self._get_text(coverage_elem, './/gml:name')
            abstract = self._get_text(coverage_elem, './/gml:description')
            
            # Parse keywords
            keywords = self._get_keywords(coverage_elem)
            
            # Parse supported CRS
            supported_crs = self._parse_coverage_crs(coverage_elem)
            
            # Parse supported formats
            supported_formats = self._parse_coverage_formats(coverage_elem)
            
            # Parse spatial extent
            spatial_extent = self._parse_spatial_extent(coverage_elem)
            
            # Parse temporal extent
            temporal_extent = self._parse_temporal_extent(coverage_elem)
            
            return CoverageDescription(
                identifier=identifier,
                title=title,
                abstract=abstract,
                keywords=keywords,
                supported_crs=supported_crs,
                supported_formats=supported_formats,
                spatial_extent=spatial_extent,
                temporal_extent=temporal_extent
            )
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML content: {e}")
    
    def _get_text(self, element: ET.Element, xpath: str) -> Optional[str]:
        """Get text content from element using xpath."""
        elem = element.find(xpath, self.namespaces)
        return elem.text.strip() if elem is not None and elem.text else None
    
    def _get_keywords(self, element: ET.Element) -> List[str]:
        """Extract keywords from element."""
        keywords = []
        for kw_elem in element.findall('.//ows:Keywords/ows:Keyword', self.namespaces):
            if kw_elem.text:
                keywords.append(kw_elem.text.strip())
        return keywords
    
    def _parse_supported_formats(self, root: ET.Element) -> List[Format]:
        """Parse supported formats from capabilities."""
        formats = []
        for format_elem in root.findall('.//wcs:SupportedFormat', self.namespaces):
            format_text = format_elem.text
            if format_text:
                try:
                    formats.append(Format(format_text.strip()))
                except ValueError:
                    # Skip unknown formats
                    pass
        return formats
    
    def _parse_supported_crs(self, root: ET.Element) -> List[CRS]:
        """Parse supported CRS from capabilities."""
        crs_list = []
        for crs_elem in root.findall('.//wcs:SupportedCRS', self.namespaces):
            crs_text = crs_elem.text
            if crs_text:
                try:
                    crs_list.append(CRS(crs_text.strip()))
                except ValueError:
                    # Skip unknown CRS
                    pass
        return crs_list
    
    def _parse_coverages(self, root: ET.Element) -> List[CoverageDescription]:
        """Parse coverage descriptions from capabilities."""
        coverages = []
        for coverage_elem in root.findall('.//wcs:Contents/wcs:CoverageSummary', self.namespaces):
            identifier = self._get_text(coverage_elem, './/wcs:Identifier')
            if identifier:
                coverage = CoverageDescription(
                    identifier=identifier,
                    title=self._get_text(coverage_elem, './/wcs:Title'),
                    abstract=self._get_text(coverage_elem, './/wcs:Abstract'),
                    keywords=self._get_keywords(coverage_elem)
                )
                coverages.append(coverage)
        return coverages
    
    def _parse_coverage_crs(self, coverage_elem: ET.Element) -> List[CRS]:
        """Parse supported CRS for a specific coverage."""
        crs_list = []
        for crs_elem in coverage_elem.findall('.//wcs:SupportedCRS', self.namespaces):
            crs_text = crs_elem.text
            if crs_text:
                try:
                    crs_list.append(CRS(crs_text.strip()))
                except ValueError:
                    pass
        return crs_list
    
    def _parse_coverage_formats(self, coverage_elem: ET.Element) -> List[Format]:
        """Parse supported formats for a specific coverage."""
        formats = []
        for format_elem in coverage_elem.findall('.//wcs:SupportedFormat', self.namespaces):
            format_text = format_elem.text
            if format_text:
                try:
                    formats.append(Format(format_text.strip()))
                except ValueError:
                    pass
        return formats
    
    def _parse_spatial_extent(self, coverage_elem: ET.Element) -> Optional[SpatialExtent]:
        """Parse spatial extent from coverage description."""
        bbox_elem = coverage_elem.find('.//gml:Envelope', self.namespaces)
        if bbox_elem is not None:
            # Parse bounding box coordinates
            lower_corner = bbox_elem.find('.//gml:lowerCorner', self.namespaces)
            upper_corner = bbox_elem.find('.//gml:upperCorner', self.namespaces)
            
            if lower_corner is not None and upper_corner is not None:
                try:
                    lower_coords = [float(x) for x in lower_corner.text.split()]
                    upper_coords = [float(x) for x in upper_corner.text.split()]
                    
                    if len(lower_coords) >= 2 and len(upper_coords) >= 2:
                        bbox = BoundingBox(
                            min_x=lower_coords[0],
                            min_y=lower_coords[1],
                            max_x=upper_coords[0],
                            max_y=upper_coords[1],
                            crs=self._parse_native_crs(coverage_elem)
                        )
                        return SpatialExtent(bbox=bbox)
                except (ValueError, IndexError):
                    pass
        return None
    
    def _parse_temporal_extent(self, coverage_elem: ET.Element) -> Optional[TemporalExtent]:
        """Parse temporal extent from coverage description."""
        time_elem = coverage_elem.find('.//gml:TimePeriod', self.namespaces)
        if time_elem is not None:
            begin_elem = time_elem.find('.//gml:beginPosition', self.namespaces)
            end_elem = time_elem.find('.//gml:endPosition', self.namespaces)
            
            start_time = None
            end_time = None
            
            if begin_elem is not None and begin_elem.text:
                try:
                    start_time = datetime.fromisoformat(begin_elem.text.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            if end_elem is not None and end_elem.text:
                try:
                    end_time = datetime.fromisoformat(end_elem.text.replace('Z', '+00:00'))
                except ValueError:
                    pass
            
            if start_time or end_time:
                return TemporalExtent(start_time=start_time, end_time=end_time)
        
        return None
    
    def _parse_native_crs(self, coverage_elem: ET.Element) -> CRS:
        """Parse native CRS for coverage."""
        native_crs_elem = coverage_elem.find('.//wcs:NativeFormat', self.namespaces)
        if native_crs_elem is not None and native_crs_elem.text:
            try:
                return CRS(native_crs_elem.text.strip())
            except ValueError:
                pass
        return CRS.EPSG_4326  # Default
    
    def _parse_native_format(self, coverage_elem: ET.Element) -> Format:
        """Parse native format for coverage."""
        native_format_elem = coverage_elem.find('.//wcs:NativeFormat', self.namespaces)
        if native_format_elem is not None and native_format_elem.text:
            try:
                return Format(native_format_elem.text.strip())
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
        self.session = requests.Session()
        self.parser = WCSParser(self.base_url)
    
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
            'coverageid': coverage_id
        }
        
        response = self.session.get(self.base_url, params=params)
        response.raise_for_status()
        
        return self.parser.parse_describe_coverage(response.text)
    
    def get_coverage(
        self,
        coverage_id: str,
        bbox: BoundingBox,
        width: int = 256,
        height: int = 256,
        output_format: Format = Format.GEOTIFF,
        **kwargs
    ) -> WCSResponse:
        """
        Get coverage data.
        
        Args:
            coverage_id: Coverage identifier
            bbox: Bounding box for the request
            width: Output width in pixels
            height: Output height in pixels
            output_format: Output format
            **kwargs: Additional parameters
            
        Returns:
            WCSResponse object
        """
        params = {
            'service': 'WCS',
            'version': '2.0.1',
            'request': 'GetCoverage',
            'coverageId': coverage_id,
            'subset': f'Long({bbox.min_x},{bbox.max_x}),Lat({bbox.min_y},{bbox.max_y})',
            'format': output_format.value,
            'width': str(width),
            'height': str(height)
        }
        
        # Add any additional parameters
        params.update(kwargs)
        
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            
            return WCSResponse(
                success=True,
                data=response.content,
                status_code=response.status_code
            )
        except requests.RequestException as e:
            return WCSResponse(
                success=False,
                error_message=str(e),
                status_code=getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0
            )


class WCSTileAdapter:
    """Adapter for WCS tile requests."""
    
    @staticmethod
    def create_tile_request(
        base_url: str,
        coverage_id: str,
        bbox: BoundingBox,
        width: int = 256,
        height: int = 256,
        output_format: Format = Format.GEOTIFF,
        crs: Optional[CRS] = None,
        **kwargs
    ) -> TileRequest:
        """
        Create a WCS GetCoverage request.
        
        Args:
            base_url: WCS service base URL
            coverage_id: Coverage identifier
            bbox: Bounding box for the tile
            width: Output width in pixels
            height: Output height in pixels
            output_format: Output format
            crs: Coordinate reference system
            **kwargs: Additional WCS parameters
            
        Returns:
            Tile request for WCS service
        """
        params = {
            'service': 'WCS',
            'version': kwargs.get('version', '2.0.1'),
            'request': 'GetCoverage',
            'coverageId': coverage_id,
            'subset': f'Long({bbox.min_x},{bbox.max_x}),Lat({bbox.min_y},{bbox.max_y})',
            'format': output_format.value,
            'width': str(width),
            'height': str(height)
        }
        
        if crs:
            params['subsettingcrs'] = crs.value
        
        # Add any additional WCS parameters
        params.update(kwargs)
        
        return TileRequest(
            url=base_url,
            params=params,
            output_format=output_format,
            crs=crs
        )