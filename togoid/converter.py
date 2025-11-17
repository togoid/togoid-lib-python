"""
TogoID Converter - ID conversion functionality

This module provides ID conversion between biological databases using TogoID API.
"""

import json
import sys
from typing import Optional, List, Dict, Any

import requests

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class TogoIDConverter:
    """TogoID Converter - API wrapper for ID conversion"""

    DEFAULT_API_URL = 'https://api.togoid.dbcls.jp'

    def __init__(self, api_base_url: Optional[str] = None):
        """
        Initialize TogoID Converter

        Args:
            api_base_url: Base URL for API endpoint. If None, uses default TogoID API.
        """
        self.api_base_url = (api_base_url or self.DEFAULT_API_URL).rstrip('/')

    def _make_request(self, endpoint: str, method: str = 'GET', params: Optional[Dict] = None,
                      json_data: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to API

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET or POST)
            params: Query parameters
            json_data: JSON data for POST requests

        Returns:
            Response data (parsed JSON or text)
        """
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        try:
            if method == 'GET':
                resp = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                resp = requests.post(url, json=json_data, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()

            # Try to parse as JSON, otherwise return text
            content_type = resp.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return resp.json()
            else:
                return resp.text

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"API Error: {e}") from e

    def convert(self, route: List[str], ids: List[str], format: str = 'json', **kwargs) -> Any:
        """
        Convert IDs between databases

        Args:
            route: List of database names forming the conversion route
            ids: List of IDs to convert
            format: Output format - 'json' (default), 'dict', 'table', or 'dataframe'
            **kwargs: Additional parameters (report, limit, offset, etc.)

        Returns:
            Conversion results in the specified format:
            - 'json': Raw API response (default)
            - 'dict': Dictionary mapping source IDs to target IDs
            - 'table': 2D array (list of lists) with [source_id, target_id] pairs
            - 'dataframe': pandas DataFrame with 'source_id' and 'target_id' columns
        """
        params = {
            'route': ','.join(route),
            'ids': ','.join(ids),
        }
        params.update(kwargs)

        # Get API response
        response = self._make_request('/convert', 'GET', params=params)

        # Transform based on format
        if format == 'dict':
            return self._convert_to_dict(response)
        elif format == 'table':
            return self._convert_to_table(response)
        elif format == 'dataframe':
            return self._convert_to_dataframe(response)
        else:  # format == 'json' or any other value
            return response

    def _convert_to_dict(self, response: Any) -> Dict[str, List[str]]:
        """
        Convert API response to dictionary format

        Args:
            response: API response (can be list or dict)

        Returns:
            Dictionary mapping source IDs to list of target IDs
        """
        result = {}

        if isinstance(response, list):
            # Handle list format (e.g., [[source, target], ...])
            for item in response:
                if isinstance(item, list) and len(item) >= 2:
                    source_id = str(item[0])
                    target_id = str(item[1])
                    if source_id not in result:
                        result[source_id] = []
                    result[source_id].append(target_id)
        elif isinstance(response, dict):
            # Handle dictionary format
            for source_id, targets in response.items():
                if isinstance(targets, list):
                    result[str(source_id)] = [str(t) for t in targets]
                else:
                    result[str(source_id)] = [str(targets)]

        return result

    def _convert_to_table(self, response: Any) -> List[List[str]]:
        """
        Convert API response to 2D array format

        Args:
            response: API response (can be list or dict)

        Returns:
            2D array with [source_id, target_id] pairs
        """
        result = []

        if isinstance(response, list):
            # Handle list format (e.g., [[source, target], ...])
            for item in response:
                if isinstance(item, list) and len(item) >= 2:
                    result.append([str(item[0]), str(item[1])])
                elif isinstance(item, dict):
                    # Handle dict items within list
                    for key, value in item.items():
                        if isinstance(value, list):
                            for v in value:
                                result.append([str(key), str(v)])
                        else:
                            result.append([str(key), str(value)])
        elif isinstance(response, dict):
            # Handle dictionary format
            for source_id, targets in response.items():
                if isinstance(targets, list):
                    for target_id in targets:
                        result.append([str(source_id), str(target_id)])
                else:
                    result.append([str(source_id), str(targets)])

        return result

    def _convert_to_dataframe(self, response: Any):
        """
        Convert API response to pandas DataFrame format

        Args:
            response: API response (can be list or dict)

        Returns:
            pandas DataFrame with 'source_id' and 'target_id' columns

        Raises:
            ImportError: If pandas is not installed
        """
        if not PANDAS_AVAILABLE:
            raise ImportError(
                "pandas is required for dataframe format. "
                "Install with: pip install pandas"
            )

        # Convert to table format first
        table_data = self._convert_to_table(response)

        # Create DataFrame
        df = pd.DataFrame(table_data, columns=['source_id', 'target_id'])
        return df

    def count(self, src: str, dst: str, ids: List[str], link: Optional[str] = None) -> Dict:
        """
        Count mappings between databases

        Args:
            src: Source database name
            dst: Destination database name
            ids: List of IDs to count
            link: Optional link name

        Returns:
            Count results with source and target counts
        """
        params = {'ids': ','.join(ids)}
        if link:
            params['link'] = link
        return self._make_request(f'/count/{src}-{dst}', 'GET', params=params)

    def search_databases(self, name: str) -> List[str]:
        """
        Search databases by name (partial match)

        Args:
            name: Partial database name to search for

        Returns:
            List of matching database names
        """
        return self._make_request(f'/search/databases/{name}')

    def search_id(self, id_string: str) -> List[str]:
        """
        Search databases by ID pattern

        Args:
            id_string: ID string to search for

        Returns:
            List of databases that match the ID pattern
        """
        return self._make_request(f'/search/id/{id_string}')

    def lookup_id(self, id_string: str) -> List[str]:
        """
        Lookup which tables contain a specific ID

        Args:
            id_string: ID to lookup

        Returns:
            List of table names containing the ID
        """
        return self._make_request(f'/lookup/id/{id_string}')

    def route(self, src: str, dst: str, max_hops: int = 3) -> List[List[str]]:
        """
        Find all routes between two databases

        Args:
            src: Source database name
            dst: Destination database name
            max_hops: Maximum number of hops (default: 3, max: 5)

        Returns:
            List of routes (each route is a list of database names)
        """
        params = {'max_hops': max_hops}
        return self._make_request(f'/route/{src}/{dst}', 'GET', params=params)

    def config_dataset(self, name: Optional[str] = None) -> Any:
        """
        Get dataset configuration

        Args:
            name: Optional dataset name. If None, returns all datasets.

        Returns:
            Configuration data
        """
        if name:
            return self._make_request(f'/config/dataset/{name}')
        else:
            return self._make_request('/config/dataset')

    def config_relation(self, src: Optional[str] = None, dst: Optional[str] = None) -> Any:
        """
        Get relation configuration

        Args:
            src: Source database name
            dst: Destination database name

        Returns:
            Configuration data
        """
        if src and dst:
            return self._make_request(f'/config/relation/{src}-{dst}')
        else:
            return self._make_request('/config/relation')

    def config_descriptions(self) -> Dict:
        """
        Get database descriptions

        Returns:
            Dictionary of database descriptions
        """
        return self._make_request('/config/descriptions')

    def config_statistics(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary of table statistics
        """
        return self._make_request('/config/statistics')

    def config_taxonomy(self) -> Any:
        """
        Get taxonomy list

        Returns:
            Taxonomy configuration
        """
        return self._make_request('/config/taxonomy')
