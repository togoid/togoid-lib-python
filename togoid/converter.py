"""
TogoID Converter - ID conversion functionality

This module provides ID conversion between biological databases using TogoID API.
"""

import json
import sys
from typing import Optional, List, Dict, Any, Tuple

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

    def _add_annotations(
        self,
        response: Any,
        route: List[str],
        annotate: Optional[List[Tuple[str, str]]] = None,
        filter: Optional[List[Tuple[str, str, List[str]]]] = None
    ) -> Dict[str, Any]:
        """
        Add annotations to conversion results and apply filters

        Args:
            response: API response from convert endpoint
            route: Conversion route
            annotate: List of (dataset_name, field_name) tuples to add as columns
            filter: List of (dataset_name, field_name, allowed_values) tuples to filter results

        Returns:
            Modified response with annotations added and filters applied
        """
        # Import AnnotationsConverter here to avoid circular dependency
        from .annotations import AnnotationsConverter

        # Extract the results array from the response
        if isinstance(response, dict) and 'results' in response:
            table_data = response['results']
        else:
            # Fallback to table conversion
            table_data = self._convert_to_table(response)

        if not table_data:
            return response

        # Initialize annotations converter
        ann_converter = AnnotationsConverter(api_endpoint=self.api_base_url)

        # Build a mapping of dataset -> {id -> {field -> value}}
        annotations_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Collect all fields to fetch (both annotate and filter)
        fields_to_fetch: Dict[str, set] = {}  # dataset -> set of fields

        if annotate:
            for dataset_name, field_name in annotate:
                if dataset_name not in fields_to_fetch:
                    fields_to_fetch[dataset_name] = set()
                fields_to_fetch[dataset_name].add(field_name)

        if filter:
            for dataset_name, field_name, _ in filter:
                if dataset_name not in fields_to_fetch:
                    fields_to_fetch[dataset_name] = set()
                fields_to_fetch[dataset_name].add(field_name)

        # Fetch all required annotations
        for dataset_name, field_names in fields_to_fetch.items():
            if dataset_name not in route:
                raise ValueError(
                    f"Dataset '{dataset_name}' not found in route {route}"
                )

            # Collect all IDs for this dataset
            dataset_index = route.index(dataset_name)
            ids_to_annotate = set()

            for row in table_data:
                if isinstance(row, list) and len(row) > dataset_index:
                    ids_to_annotate.add(str(row[dataset_index]))

            if not ids_to_annotate:
                continue

            # Execute annotation query
            try:
                records = ann_converter.execute_query(
                    dataset_name=dataset_name,
                    ids=list(ids_to_annotate),
                    fields=list(field_names),
                    filters={}
                )

                # Cache the results
                if dataset_name not in annotations_cache:
                    annotations_cache[dataset_name] = {}

                for id_value, fields_data in records.items():
                    if id_value not in annotations_cache[dataset_name]:
                        annotations_cache[dataset_name][id_value] = {}
                    for field_name in field_names:
                        annotations_cache[dataset_name][id_value][field_name] = fields_data.get(field_name, "")

            except Exception as e:
                # Log error but continue
                print(f"Warning: Failed to get annotations for {dataset_name}: {e}", file=sys.stderr)

        # Apply filters first, then add annotation columns
        annotated_table = []
        for row in table_data:
            if isinstance(row, list):
                # Check if row passes all filters
                passes_filter = True
                if filter:
                    for dataset_name, field_name, allowed_values in filter:
                        dataset_index = route.index(dataset_name)
                        if len(row) > dataset_index:
                            id_value = str(row[dataset_index])
                            annotation_value = annotations_cache.get(dataset_name, {}).get(id_value, {}).get(field_name, "")

                            # Check if value matches any allowed value
                            if isinstance(annotation_value, list):
                                # If annotation is a list, check if any element matches
                                if not any(str(v) in allowed_values for v in annotation_value):
                                    passes_filter = False
                                    break
                            else:
                                # Single value
                                if str(annotation_value) not in allowed_values:
                                    passes_filter = False
                                    break

                if not passes_filter:
                    continue

                # Add annotation columns
                new_row = list(row)
                if annotate:
                    for dataset_name, field_name in annotate:
                        dataset_index = route.index(dataset_name)
                        if len(row) > dataset_index:
                            id_value = str(row[dataset_index])
                            annotation_value = annotations_cache.get(dataset_name, {}).get(id_value, {}).get(field_name, "")
                            # Handle list values
                            if isinstance(annotation_value, list):
                                annotation_value = ", ".join(str(v) for v in annotation_value)
                            new_row.append(str(annotation_value))
                        else:
                            new_row.append("")
                annotated_table.append(new_row)
            else:
                annotated_table.append(row)

        # Update response with annotated results
        if isinstance(response, dict) and 'results' in response:
            response['results'] = annotated_table
            return response
        else:
            return annotated_table

    def convert(
        self,
        route: List[str],
        ids: List[str],
        format: str = 'json',
        annotate: Optional[List[Tuple[str, str]]] = None,
        filter: Optional[List[Tuple[str, str, List[str]]]] = None,
        **kwargs
    ) -> Any:
        """
        Convert IDs between databases

        Args:
            route: List of database names forming the conversion route
            ids: List of IDs to convert
            format: Output format - 'json' (default), 'dict', 'table', or 'dataframe'
            annotate: Optional list of (dataset_name, field_name) tuples to add annotations
            filter: Optional list of (dataset_name, field_name, allowed_values) tuples to filter results
            **kwargs: Additional parameters (report, limit, offset, etc.)

        Returns:
            Conversion results in the specified format:
            - 'json': Raw API response (default)
            - 'dict': Dictionary mapping source IDs to target IDs
            - 'table': 2D array (list of lists) with [source_id, target_id] pairs (with annotations if specified)
            - 'dataframe': pandas DataFrame with 'source_id' and 'target_id' columns (with annotations if specified)
        """
        params = {
            'route': ','.join(route),
            'ids': ','.join(ids),
        }
        params.update(kwargs)

        # If annotations or filters requested, ensure we get full report format
        if (annotate or filter) and 'report' not in params:
            params['report'] = 'full'

        # Get API response
        response = self._make_request('/convert', 'GET', params=params)

        # If annotations or filters requested, add them to the response
        if (annotate or filter) and format in ('table', 'dataframe'):
            response = self._add_annotations(response, route, annotate, filter)

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
            2D array with [source_id, target_id, ...] rows
        """
        result = []

        # Handle TogoID API response format with 'results' key
        if isinstance(response, dict) and 'results' in response:
            results_data = response['results']
            if isinstance(results_data, list):
                for item in results_data:
                    if isinstance(item, list):
                        # Already a list, convert all elements to strings
                        result.append([str(elem) for elem in item])
                    else:
                        # Single value
                        result.append([str(item)])
            return result

        # Handle simple list format
        if isinstance(response, list):
            # Handle list format (e.g., [[source, target], ...] or [[source, target, annotation], ...])
            for item in response:
                if isinstance(item, list):
                    # Convert all elements to strings
                    result.append([str(elem) for elem in item])
                elif isinstance(item, dict):
                    # Handle dict items within list
                    for key, value in item.items():
                        if isinstance(value, list):
                            for v in value:
                                result.append([str(key), str(v)])
                        else:
                            result.append([str(key), str(value)])
        elif isinstance(response, dict):
            # Handle dictionary format (not TogoID API format)
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
