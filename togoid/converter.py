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
                      json_data: Optional[Dict] = None,
                      form_data: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to API

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET or POST)
            params: Query parameters (GET only; ignored for POST when form_data/json_data given)
            json_data: JSON body for POST requests
            form_data: application/x-www-form-urlencoded body for POST requests

        Returns:
            Response data (parsed JSON or text)
        """
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"

        try:
            if method == 'GET':
                resp = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                if form_data is not None:
                    resp = requests.post(url, data=form_data, timeout=30)
                elif json_data is not None:
                    resp = requests.post(url, json=json_data, timeout=30)
                else:
                    resp = requests.post(url, data=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            resp.raise_for_status()

            # Try to parse as JSON, otherwise return text
            content_type = resp.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return resp.json()
            else:
                return resp.text

        except requests.exceptions.HTTPError as e:
            # Include status code in error for better handling
            status_code = e.response.status_code if hasattr(e, 'response') else 'Unknown'
            raise RuntimeError(f"API Error ({status_code}): {e}") from e
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

                # Add annotation columns right after their corresponding dataset column
                if annotate:
                    # Build a mapping of dataset_index -> list of annotation values to insert after that index
                    annotations_to_insert = {}
                    for dataset_name, field_name in annotate:
                        dataset_index = route.index(dataset_name)
                        if dataset_index not in annotations_to_insert:
                            annotations_to_insert[dataset_index] = []

                        if len(row) > dataset_index:
                            id_value = str(row[dataset_index])
                            annotation_value = annotations_cache.get(dataset_name, {}).get(id_value, {}).get(field_name, "")
                            # Handle list values
                            if isinstance(annotation_value, list):
                                annotation_value = ", ".join(str(v) for v in annotation_value)
                            annotations_to_insert[dataset_index].append(str(annotation_value))
                        else:
                            annotations_to_insert[dataset_index].append("")

                    # Build new row by inserting annotations after their dataset columns
                    new_row = []
                    for i, cell in enumerate(row):
                        new_row.append(cell)
                        # Insert annotations for this column if any
                        if i in annotations_to_insert:
                            new_row.extend(annotations_to_insert[i])
                    annotated_table.append(new_row)
                else:
                    annotated_table.append(list(row))
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
            - 'dict': Dictionary with 'ids', 'route', and 'results' (mapping source IDs to target IDs)
            - 'table': 2D array (list of lists) with [source_id, target_id, ...] pairs (with annotations if specified)
            - 'dataframe': pandas DataFrame with dataset name columns (with annotations if specified)
        """
        params = {
            'route': ','.join(route),
            'ids': ','.join(ids),
        }
        params.update(kwargs)

        # Set report parameter based on format and whether annotations/filters are requested
        if 'report' not in params:
            if annotate or filter or len(route) >= 3:
                params['report'] = 'full'
            elif format in ('dict', 'table', 'dataframe'):
                params['report'] = 'pair'

        # Get API response with route suggestion on error.
        # POST + form encoding lets us send large ID lists without hitting URL-length limits.
        try:
            response = self._make_request('/convert', 'POST', form_data=params)
        except RuntimeError as e:
            # Check if it's a connection error (400 Bad Request or similar)
            error_str = str(e)
            if ('400' in error_str or 'Bad Request' in error_str) and len(route) == 2:
                # Try to find alternative routes for 2-dataset conversions
                src, dst = route
                suggested_routes = self._find_alternative_routes(src, dst)

                if suggested_routes:
                    route_strs = [' -> '.join(r) for r in suggested_routes]
                    raise RuntimeError(
                        f"No direct connection between '{src}' and '{dst}'. "
                        f"Try one of these routes instead:\n" +
                        '\n'.join(f"  - {rs}" for rs in route_strs)
                    ) from e
                else:
                    raise RuntimeError(
                        f"No connection found between '{src}' and '{dst}'. "
                        f"These datasets may not be connected in the TogoID database."
                    ) from e
            # Re-raise other errors
            raise

        # If annotations or filters requested, add them to the response
        if (annotate or filter) and format in ('table', 'dataframe'):
            response = self._add_annotations(response, route, annotate, filter)

        # Transform based on format
        if format == 'dict':
            if len(route) >= 3:
                raise ValueError(
                    "format='dict' is not supported when route length >= 3. "
                    "Use 'table' or 'dataframe' instead."
                )
            return self._convert_to_dict(response, route)
        elif format == 'table':
            return self._convert_to_table(response)
        elif format == 'dataframe':
            return self._convert_to_dataframe(response, route, annotate)
        else:  # format == 'json' or any other value
            return response

    def _convert_to_dict(self, response: Any, route: List[str]) -> Dict[str, Any]:
        """
        Convert API response to dictionary format

        Args:
            response: API response (can be list or dict)
            route: Conversion route

        Returns:
            Dictionary with 'ids', 'route', and 'results' (mapping source IDs to list of target IDs)
        """
        result_mapping = {}

        # Handle TogoID API response format with 'results' key
        if isinstance(response, dict) and 'results' in response:
            results_data = response['results']
            ids = response.get('ids', [])

            if isinstance(results_data, list):
                for item in results_data:
                    if isinstance(item, list) and len(item) >= 2:
                        source_id = str(item[0])
                        target_id = str(item[1])
                        if source_id not in result_mapping:
                            result_mapping[source_id] = []
                        result_mapping[source_id].append(target_id)

            return {
                'ids': ids,
                'route': route,
                'results': result_mapping
            }

        # Handle simple list format
        if isinstance(response, list):
            # Handle list format (e.g., [[source, target], ...])
            for item in response:
                if isinstance(item, list) and len(item) >= 2:
                    source_id = str(item[0])
                    target_id = str(item[1])
                    if source_id not in result_mapping:
                        result_mapping[source_id] = []
                    result_mapping[source_id].append(target_id)
        elif isinstance(response, dict):
            # Handle dictionary format (not TogoID API format)
            for source_id, targets in response.items():
                if isinstance(targets, list):
                    result_mapping[str(source_id)] = [str(t) for t in targets]
                else:
                    result_mapping[str(source_id)] = [str(targets)]

        return {
            'ids': [],
            'route': route,
            'results': result_mapping
        }

    def _convert_to_table(self, response: Any) -> List[List[str]]:
        """
        Convert API response to 2D array format

        Args:
            response: API response (can be list or dict)

        Returns:
            2D array with [source_id, target_id, ...] rows
        """
        # Preserve None as Python None (missing mapping) instead of stringifying
        # it to "None". DataFrame conversion then promotes None -> pd.NA.
        def _cell(v):
            return None if v is None else str(v)

        result = []

        # Handle TogoID API response format with 'results' key
        if isinstance(response, dict) and 'results' in response:
            results_data = response['results']
            if isinstance(results_data, list):
                for item in results_data:
                    if isinstance(item, list):
                        result.append([_cell(elem) for elem in item])
                    else:
                        result.append([_cell(item)])
            return result

        # Handle simple list format
        if isinstance(response, list):
            # Handle list format (e.g., [[source, target], ...] or [[source, target, annotation], ...])
            for item in response:
                if isinstance(item, list):
                    result.append([_cell(elem) for elem in item])
                elif isinstance(item, dict):
                    # Handle dict items within list
                    for key, value in item.items():
                        if isinstance(value, list):
                            for v in value:
                                result.append([_cell(key), _cell(v)])
                        else:
                            result.append([_cell(key), _cell(value)])
        elif isinstance(response, dict):
            # Handle dictionary format (not TogoID API format)
            for source_id, targets in response.items():
                if isinstance(targets, list):
                    for target_id in targets:
                        result.append([_cell(source_id), _cell(target_id)])
                else:
                    result.append([_cell(source_id), _cell(targets)])

        return result

    def _convert_to_dataframe(
        self,
        response: Any,
        route: List[str],
        annotate: Optional[List[Tuple[str, str]]] = None
    ):
        """
        Convert API response to pandas DataFrame format

        Args:
            response: API response (can be list or dict)
            route: Conversion route (list of dataset names)
            annotate: Optional list of (dataset_name, field_name) tuples for annotations

        Returns:
            pandas DataFrame with dataset name columns and annotation columns

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

        # Create DataFrame with appropriate column names based on data
        if not table_data:
            # Empty result - use route names as columns
            df = pd.DataFrame(columns=route)
        else:
            num_cols = len(table_data[0]) if table_data else 0

            if annotate:
                # With annotations: build column names matching the data order
                # Annotations are inserted right after their corresponding dataset column
                col_names = []

                # Build a mapping of dataset_index -> list of annotation names
                annotations_map = {}
                for dataset_name, field_name in annotate:
                    dataset_index = route.index(dataset_name)
                    if dataset_index not in annotations_map:
                        annotations_map[dataset_index] = []
                    annotations_map[dataset_index].append(f"{dataset_name}.{field_name}")

                # Build column names by inserting annotations after their dataset columns
                for i, dataset_name in enumerate(route):
                    col_names.append(dataset_name)
                    # Add annotation columns for this dataset if any
                    if i in annotations_map:
                        col_names.extend(annotations_map[i])

                df = pd.DataFrame(table_data, columns=col_names, dtype=object)
            else:
                # Without annotations: use route names
                if num_cols == len(route):
                    df = pd.DataFrame(table_data, columns=route, dtype=object)
                elif num_cols < len(route):
                    # Fewer columns than route (e.g., only target IDs with report='target')
                    # Use the last N dataset names from the route
                    df = pd.DataFrame(table_data, columns=route[-num_cols:], dtype=object)
                else:
                    # More columns than route (shouldn't happen, but handle it)
                    col_names = route + [f'col_{i}' for i in range(len(route), num_cols)]
                    df = pd.DataFrame(table_data, columns=col_names, dtype=object)

        # Promote any missing cell (None / NaN) to pd.NA for a consistent
        # missing-value sentinel in DataFrame output.
        if not df.empty:
            df = df.where(df.notna(), pd.NA)
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
        return self._make_request(f'/count/{src}-{dst}', 'POST', form_data=params)

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

    def config_list_targets(self, source: str) -> List[str]:
        """
        Get list of datasets reachable from the specified source dataset in one hop

        Args:
            source: Source dataset name (e.g., "ncbigene")

        Returns:
            List of target dataset names reachable from the source

        Example:
            >>> converter = TogoIDConverter()
            >>> targets = converter.config_list_targets(source="ncbigene")
            >>> print(targets)
            ['ensembl_gene', 'ensembl_protein', 'ensembl_transcript', ...]
        """
        # Get all relation configurations
        relations = self.config_relation()

        targets = []

        # Parse each relation key
        for relation_key in relations.keys():
            # Split key by "-"
            parts = relation_key.split('-')

            # Check if it's a valid format (2 parts)
            if len(parts) == 2:
                src, dst = parts

                # If source matches (forward link), add target to list
                if src == source:
                    targets.append(dst)
                # If destination matches (reverse link), add source to list
                if dst == source:
                    targets.append(src)

        # Remove duplicates and sort
        return sorted(set(targets))

    def _find_alternative_routes(
        self,
        src: str,
        dst: str,
        max_hops: int = 3,
        max_results: int = 5
    ) -> List[List[str]]:
        """
        Find alternative routes between two datasets

        Args:
            src: Source dataset name
            dst: Destination dataset name
            max_hops: Maximum number of hops to search (default: 3)
            max_results: Maximum number of routes to return (default: 5)

        Returns:
            List of routes (each route is a list of dataset names)
        """
        routes = []

        # Try route API first
        try:
            api_routes = self.route(src, dst, max_hops=max_hops)
            if api_routes:
                return api_routes[:max_results]
        except RuntimeError:
            # Route API failed (404 or other error), fall back to manual search
            pass

        # Manual search using config_list_targets

        # Check direct connection (1 hop)
        try:
            targets_from_src = self.config_list_targets(src)
            if dst in targets_from_src:
                routes.append([src, dst])
                return routes
        except RuntimeError:
            # config_list_targets failed
            return routes

        # Check 2-hop connections
        if max_hops >= 2:
            for intermediate in targets_from_src:
                try:
                    targets_from_intermediate = self.config_list_targets(intermediate)
                    if dst in targets_from_intermediate:
                        routes.append([src, intermediate, dst])
                        if len(routes) >= max_results:
                            return routes
                except RuntimeError:
                    continue

            if routes:
                return routes

        # Check 3-hop connections
        if max_hops >= 3:
            for intermediate1 in targets_from_src:
                try:
                    targets_from_intermediate1 = self.config_list_targets(intermediate1)
                    for intermediate2 in targets_from_intermediate1:
                        if intermediate2 == src:  # Avoid loops
                            continue
                        try:
                            targets_from_intermediate2 = self.config_list_targets(intermediate2)
                            if dst in targets_from_intermediate2:
                                routes.append([src, intermediate1, intermediate2, dst])
                                if len(routes) >= max_results:
                                    return routes
                        except RuntimeError:
                            continue
                except RuntimeError:
                    continue

        return routes

    def get_ortholog(
        self,
        ids: List[str],
        route: List[str],
        target_taxids: List[str],
        format: str = 'table'
    ) -> Any:
        """
        Get orthologs by round-trip conversion through specified route and taxonomy filtering

        This method performs a special conversion pattern:
        1. Forward conversion: Follow the route (e.g., ncbigene -> homologene)
        2. Reverse conversion: Go back through route in reverse (e.g., homologene -> ncbigene)
        3. Taxonomy conversion: Convert to taxonomy IDs
        4. Filter: Keep only results matching target_taxids

        Args:
            ids: List of source IDs
            route: Conversion route (e.g., ["ncbigene", "homologene"])
            target_taxids: List of taxonomy IDs to filter by (e.g., ["10090", "10116"])
            format: Output format - 'table' (default), 'dict', 'dataframe', or 'json'

        Returns:
            Filtered ortholog results in specified format. Table format returns
            rows in the order: [source_id, intermediate_id, target_id, taxonomy_id].
            Dict format maps each source_id to a list of
            (intermediate_id, target_id, taxonomy_id) tuples.
            DataFrame format returns a pandas DataFrame with columns based on the route.

        Example:
            >>> converter = TogoIDConverter()
            >>> result = converter.get_ortholog(
            ...     ids=["1", "9"],
            ...     route=["ncbigene", "homologene"],
            ...     target_taxids=["10090", "10116"]
            ... )
            # Returns mouse and rat orthologs
        """
        # Step 1: Forward conversion (e.g., ncbigene -> homologene)
        forward_result = self.convert(
            ids=ids,
            route=route,
            format='json',
            report='pair'
        )

        # Extract intermediate IDs and keep mapping back to original IDs
        forward_pairs = forward_result.get('results', [])
        if not forward_pairs:
            # No results from forward conversion
            if format == 'dict':
                return {}
            elif format == 'table':
                return []
            else:
                return {'results': []}

        intermediate_ids: List[str] = []
        intermediate_to_sources: Dict[str, List[str]] = {}
        intermediate_seen = set()

        for pair in forward_pairs:
            if isinstance(pair, list) and len(pair) >= 2:
                source_id = str(pair[0])
                intermediate_id = str(pair[1])
                if intermediate_id not in intermediate_seen:
                    intermediate_ids.append(intermediate_id)
                    intermediate_seen.add(intermediate_id)

                if intermediate_id not in intermediate_to_sources:
                    intermediate_to_sources[intermediate_id] = []
                intermediate_to_sources[intermediate_id].append(source_id)

        # Step 2: Reverse conversion (e.g., homologene -> ncbigene)
        reverse_route = list(reversed(route))
        reverse_result = self.convert(
            ids=intermediate_ids,
            route=reverse_route,
            format='json',
            report='pair'
        )

        reverse_pairs = reverse_result.get('results', [])
        if not reverse_pairs:
            # No results from reverse conversion
            if format == 'dict':
                return {}
            elif format == 'table':
                return []
            else:
                return {'results': []}

        # Extract target IDs from reverse conversion
        target_ids = set()
        # Build mapping: intermediate_id -> [target_ids]
        intermediate_to_targets: Dict[str, List[str]] = {}
        for pair in reverse_pairs:
            if isinstance(pair, list) and len(pair) >= 2:
                intermediate_id = str(pair[0])
                target_id = str(pair[1])
                target_ids.add(target_id)
                if intermediate_id not in intermediate_to_targets:
                    intermediate_to_targets[intermediate_id] = []
                intermediate_to_targets[intermediate_id].append(target_id)

        # Step 3: Convert target IDs to taxonomy
        taxonomy_route = [route[0], 'taxonomy']  # Use source database -> taxonomy
        taxonomy_result = self.convert(
            ids=list(target_ids),
            route=taxonomy_route,
            format='json',
            report='pair'
        )

        taxonomy_pairs = taxonomy_result.get('results', [])

        # Build mapping: target_id -> taxonomy_id
        target_to_taxonomy: Dict[str, str] = {}
        for pair in taxonomy_pairs:
            if isinstance(pair, list) and len(pair) >= 2:
                target_id = str(pair[0])
                taxonomy_id = str(pair[1])
                target_to_taxonomy[target_id] = taxonomy_id

        # Step 4: Filter by target_taxids
        filtered_results = []
        for intermediate_id, target_id_list in intermediate_to_targets.items():
            for target_id in target_id_list:
                taxonomy_id = target_to_taxonomy.get(target_id)
                if taxonomy_id in target_taxids:
                    source_ids = intermediate_to_sources.get(intermediate_id, [])
                    if not source_ids:
                        # Should not happen, but keep explicit placeholder
                        filtered_results.append(["", intermediate_id, target_id, taxonomy_id])
                        continue
                    for source_id in source_ids:
                        filtered_results.append([source_id, intermediate_id, target_id, taxonomy_id])

        # Format output
        if format == 'dict':
            # Group by intermediate_id
            result_dict: Dict[str, List[Tuple[str, str, str]]] = {}
            for row in filtered_results:
                source_id, intermediate_id, target_id, taxonomy_id = row
                if source_id not in result_dict:
                    result_dict[source_id] = []
                result_dict[source_id].append((intermediate_id, target_id, taxonomy_id))
            return result_dict
        elif format == 'table':
            return filtered_results
        elif format == 'dataframe':
            if not PANDAS_AVAILABLE:
                raise ImportError(
                    "pandas is required for dataframe format. "
                    "Install with: pip install pandas"
                )
            # Column names: source dataset, intermediate dataset, target dataset, taxonomy
            col_names = [route[0], route[-1], route[0], 'taxonomy']
            if not filtered_results:
                return pd.DataFrame(columns=col_names)
            return pd.DataFrame(filtered_results, columns=col_names)
        else:  # json
            return {
                'ids': ids,
                'route': route,
                'target_taxids': target_taxids,
                'results': filtered_results
            }
