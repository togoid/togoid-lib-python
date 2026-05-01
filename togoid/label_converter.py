"""
TogoID Label Converter - Label to ID conversion

This module converts biological labels (gene names, protein names, disease names, etc.)
to database identifiers using PubDictionaries API and TogoID SPARQList API.

The tool automatically selects the appropriate API based on dataset configuration:
- If dataset has label_resolver.sparqlist: Uses SPARQList API
- Otherwise: Uses PubDictionaries API
"""
import csv
import json
import os
import sys
from typing import Dict, List, Optional, Any

import requests

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class LabelConverter:
    """Convert labels to IDs using external APIs"""

    PUBDICT_BASE_URL = "https://pubdictionaries.org"
    SPARQLIST_BASE_URL = "https://dx.dbcls.jp/togoid/sparqlist/api"
    DEFAULT_TOGOID_API_BASE_URL = "https://api.togoid.dbcls.jp"

    def __init__(self, verbose: bool = False, api_base_url: Optional[str] = None):
        self.verbose = verbose
        self.session = requests.Session()
        self._dataset_cache: Optional[Dict[str, Any]] = None
        base_url = api_base_url or os.getenv("TOGOID_API_ENDPOINT") or self.DEFAULT_TOGOID_API_BASE_URL
        self.api_base_url = base_url.rstrip('/')

    def _log(self, message: str):
        """Print log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[INFO] {message}", file=sys.stderr)

    def _get_dataset_config(self) -> Dict[str, Any]:
        """
        Fetch dataset configuration from TogoID API

        Returns:
            Dictionary of dataset configurations

        Raises:
            Exception if API request fails
        """
        if self._dataset_cache is not None:
            return self._dataset_cache

        self._log("Fetching dataset config from TogoID API")
        url = f"{self.api_base_url}/config/dataset"
        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        self._dataset_cache = response.json()
        return self._dataset_cache

    def _should_use_sparqlist_for_dataset(self, dataset: str) -> bool:
        """
        Determine if SPARQList API should be used for the given dataset

        Args:
            dataset: Dataset name

        Returns:
            True if dataset has label_resolver.sparqlist configured, False otherwise
        """
        try:
            datasets = self._get_dataset_config()

            if dataset not in datasets:
                self._log(f"Dataset '{dataset}' not found in TogoID API config")
                return False

            dataset_config = datasets[dataset]
            label_resolver = dataset_config.get("label_resolver", {})

            if "sparqlist" in label_resolver:
                sparqlist_endpoint = label_resolver["sparqlist"]
                self._log(f"Dataset '{dataset}' has SPARQList endpoint: {sparqlist_endpoint}")
                return True
            else:
                self._log(f"Dataset '{dataset}' does not have SPARQList endpoint, using PubDictionaries")
                return False
        except Exception as e:
            self._log(f"Error checking dataset config: {e}. Defaulting to PubDictionaries API")
            return False

    def convert_pubdictionaries(
        self,
        labels: List[str],
        dictionaries: str,
        tags: Optional[str] = None,
        threshold: float = 0.5,
        preferred_dictionary: Optional[str] = None,
        dictionary_to_label: Optional[Dict[str, str]] = None,
        preferred_label_column: str = "name",
    ) -> List[Dict[str, Any]]:
        """
        Convert labels to IDs using PubDictionaries API

        The output mirrors the TogoID Web UI: each row contains
        ``input``, ``match_type`` (the human-readable dictionary label such as
        "Name" / "Exact synonym"), the canonical label under the column whose
        name comes from the preferred dictionary's ``label`` (e.g. "Name"),
        ``score`` and ``identifier``.

        Args:
            labels: List of labels to search
            dictionaries: Comma-separated dictionary names
            tags: Taxonomy tags (e.g., "9606" for human)
            threshold: Matching score threshold (0-1)
            preferred_dictionary: Preferred dictionary for canonical label resolution
            dictionary_to_label: Mapping of dictionary id -> human-readable label
            preferred_label_column: Column name for the canonical label
        """
        self._log(f"Converting {len(labels)} labels using PubDictionaries API")
        self._log(f"Dictionaries: {dictionaries}")

        if dictionary_to_label is None:
            dictionary_to_label = {}

        params = {
            "labels": "|".join(labels),
            "dictionaries": dictionaries,
            "verbose": "true",
            "use_ngram_similarity": "true",
        }
        if tags:
            params["tags"] = tags
        if threshold is not None:
            params["threshold"] = str(threshold)

        self._log(f"Request URL: {self.PUBDICT_BASE_URL}/find_ids.json")
        response = self.session.get(
            f"{self.PUBDICT_BASE_URL}/find_ids.json", params=params
        )
        response.raise_for_status()
        find_ids_data = response.json()

        # Collect identifiers from non-preferred dictionaries to resolve canonical labels
        synonym_identifiers: List[str] = []
        if preferred_dictionary:
            for label in labels:
                for item in find_ids_data.get(label, []) or []:
                    dict_id = item.get("dictionary", "")
                    identifier = item.get("identifier", "")
                    if dict_id and dict_id != preferred_dictionary and identifier:
                        synonym_identifiers.append(identifier)
            # Dedupe while preserving order
            synonym_identifiers = list(dict.fromkeys(synonym_identifiers))

        canonical_lookup: Dict[str, str] = {}
        if synonym_identifiers and preferred_dictionary:
            self._log(
                f"Resolving {len(synonym_identifiers)} synonyms via {preferred_dictionary}"
            )
            try:
                terms_response = self.session.get(
                    f"{self.PUBDICT_BASE_URL}/find_terms.json",
                    params={
                        "identifiers": "|".join(synonym_identifiers),
                        "dictionaries": preferred_dictionary,
                    },
                )
                terms_response.raise_for_status()
                terms_data = terms_response.json() or {}
                for id_key, entry in terms_data.items():
                    if isinstance(entry, dict) and "label" in entry:
                        canonical_lookup[str(id_key)] = entry.get("label", "")
                    elif isinstance(entry, list) and entry:
                        first = entry[0]
                        if isinstance(first, dict):
                            canonical_lookup[str(id_key)] = first.get("label", "")
            except Exception as exc:  # noqa: BLE001
                self._log(f"find_terms lookup failed: {exc}")

        results: List[Dict[str, Any]] = []

        for label in labels:
            table_base_data = find_ids_data.get(label, [])

            if not table_base_data:
                self._log(f"No results found for label: {label}")
                row = {
                    "input": label,
                    "match_type": "Unmatched",
                    preferred_label_column: None,
                    "score": None,
                    "identifier": "",
                }
                results.append(row)
                continue

            for item in table_base_data:
                dict_id = item.get("dictionary", "")
                identifier = item.get("identifier", "")
                score = item.get("score")

                match_label = dictionary_to_label.get(dict_id) or dict_id or "PubDictionaries"

                if preferred_dictionary and dict_id == preferred_dictionary:
                    canonical_label = item.get("label", "")
                elif preferred_dictionary:
                    canonical_label = canonical_lookup.get(identifier, item.get("label", ""))
                else:
                    canonical_label = item.get("label", "")

                row = {
                    "input": label,
                    "match_type": match_label,
                    preferred_label_column: canonical_label,
                    "score": score,
                    "identifier": identifier,
                }
                results.append(row)

        self._log(f"Total results: {len(results)}")
        return results

    def convert_sparqlist(
        self,
        labels: List[str],
        sparqlist: str,
        label_types: List[str],
        taxonomy: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Convert labels to IDs using TogoID SPARQList API

        Args:
            labels: List of labels to search
            sparqlist: SPARQList endpoint name
            label_types: List of label types (e.g., ["symbol", "synonym"])
            taxonomy: Taxonomy ID (e.g., "9606" for human)

        Returns:
            List of result dictionaries
        """
        self._log(f"Converting {len(labels)} labels using SPARQList API")
        self._log(f"SPARQList endpoint: {sparqlist}")
        self._log(f"Label types: {label_types}")

        params = {
            "labels": ",".join(labels),
            "label_types": ",".join(label_types),
        }
        if taxonomy:
            params["taxon"] = taxonomy

        url = f"{self.SPARQLIST_BASE_URL}/{sparqlist}"
        self._log(f"Request URL: {url}")

        response = self.session.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        results = []

        for label in labels:
            label_data = data.get(label, [])

            if not label_data:
                self._log(f"No results found for label: {label}")
                results.append(
                    {
                        "input": label,
                        "match_type": "Unmatched",
                        "symbol": "",
                        "identifier": "",
                    }
                )
                continue

            for item in label_data:
                results.append(
                    {
                        "input": label,
                        "match_type": item.get("label_type", ""),
                        "symbol": item.get("preferred", ""),
                        "identifier": item.get("identifier", ""),
                    }
                )

        self._log(f"Total results: {len(results)}")
        return results

    def convert(
        self,
        labels: List[str],
        dataset: str,
        label_types: Optional[List[str]] = None,
        tags: Optional[str] = None,
        threshold: float = 0.5,
        preferred_dictionary: Optional[str] = None,
        taxonomy: Optional[str] = None,
        format: str = 'json',
    ) -> Any:
        """
        Convert labels to IDs - automatically selects API based on dataset configuration

        Args:
            labels: List of labels to search
            dataset: Dataset name to determine API endpoint
            label_types: List of label types (if None, uses dataset config)
                        - For SPARQList: list of label types (e.g., ["symbol", "synonym"])
                        - For PubDictionaries: list of dictionary names (e.g., ["togoid_chebi_label"])
            tags: Taxonomy tags for PubDict (e.g., "9606" for human)
            threshold: Matching score threshold for PubDict (0-1)
            preferred_dictionary: Preferred dictionary for PubDict synonym resolution
            taxonomy: Taxonomy ID for SPARQList (e.g., "9606" for human)
            format: Output format - 'json' (default) or 'dataframe'

        Returns:
            List of result dictionaries (json format) or pandas DataFrame (dataframe format)
        """
        if self._should_use_sparqlist_for_dataset(dataset):
            # Get SPARQList endpoint from dataset config
            datasets = self._get_dataset_config()
            dataset_config = datasets[dataset]
            label_resolver = dataset_config["label_resolver"]
            sparqlist_endpoint = label_resolver["sparqlist"]

            # Check if taxonomy is required
            taxonomy_required = label_resolver.get("taxonomy", False)
            if taxonomy_required and taxonomy is None:
                raise ValueError(
                    f"Taxonomy is required for dataset: {dataset}. "
                    f"Please specify the 'taxonomy' parameter (e.g., taxonomy='9606' for human)"
                )

            # Use label_types from argument or extract from dataset config
            if label_types is None:
                # Extract label_type values from dataset config
                label_type_configs = label_resolver.get("label_types", [])
                if label_type_configs:
                    label_types = [lt["label_type"] for lt in label_type_configs]
                else:
                    # Fallback default
                    label_types = ["symbol", "synonym"]
                self._log(f"Using label_types from dataset config: {label_types}")

            self._log(f"Using SPARQList API for dataset '{dataset}'")
            results = self.convert_sparqlist(
                labels=labels,
                sparqlist=sparqlist_endpoint,
                label_types=label_types,
                taxonomy=taxonomy,
            )
        else:
            # Use PubDictionaries API
            datasets = self._get_dataset_config()
            dataset_config = datasets.get(dataset, {})
            label_resolver = dataset_config.get("label_resolver", {})
            dictionary_configs = label_resolver.get("dictionaries", [])

            # Build dictionary -> label map and locate preferred dictionary
            dictionary_to_label: Dict[str, str] = {}
            config_preferred_dictionary: Optional[str] = None
            preferred_label_column = "name"
            for d in dictionary_configs:
                dname = d.get("dictionary")
                if not dname:
                    continue
                dictionary_to_label[dname] = d.get("label", dname)
                if d.get("preferred"):
                    config_preferred_dictionary = dname
                    preferred_label_column = d.get("label", dname)

            # Caller-supplied preferred_dictionary overrides config
            effective_preferred = preferred_dictionary or config_preferred_dictionary

            if label_types is None:
                # Extract dictionary names from dataset config
                if dictionary_configs:
                    resolved_dictionaries = [d["dictionary"] for d in dictionary_configs]
                else:
                    raise ValueError(
                        f"The label_types argument is required for dataset '{dataset}' "
                        "which does not have dictionary configuration"
                    )
                self._log(f"Using dictionaries from dataset config: {resolved_dictionaries}")
            else:
                # Map label_type short names to dictionary names
                label_type_to_dict = {
                    d.get("label_type", ""): d["dictionary"]
                    for d in dictionary_configs
                    if "dictionary" in d
                }
                resolved_dictionaries = [
                    label_type_to_dict.get(lt, lt) for lt in label_types
                ]
                self._log(
                    f"Resolved label_types {label_types} to dictionaries: {resolved_dictionaries}"
                )

            self._log(f"Using PubDictionaries API for dataset '{dataset}'")
            results = self.convert_pubdictionaries(
                labels=labels,
                dictionaries=",".join(resolved_dictionaries),
                tags=tags,
                threshold=threshold,
                preferred_dictionary=effective_preferred,
                dictionary_to_label=dictionary_to_label,
                preferred_label_column=preferred_label_column,
            )

        # Convert to dataframe if requested
        if format == 'dataframe':
            if not PANDAS_AVAILABLE:
                raise ImportError(
                    "pandas is required for dataframe format. "
                    "Install with: pip install pandas"
                )
            if not results:
                return pd.DataFrame()
            return pd.DataFrame(results)
        else:
            return results


def parse_labels(label_input: str) -> List[str]:
    """
    Parse label input string and return list of labels

    Args:
        label_input: Comma or newline-separated labels

    Returns:
        List of cleaned labels
    """
    # Split by comma or newline
    labels = []
    for part in label_input.replace("\n", ",").split(","):
        part = part.strip()
        if part:
            labels.append(part)
    return labels


def output_results(
    results: List[Dict[str, Any]], output_format: str, output_file: Optional[str] = None
):
    """
    Output results in the specified format

    Args:
        results: List of result dictionaries
        output_format: Output format (json, csv, tsv)
        output_file: Output file path (None for stdout)
    """
    if output_format == "json":
        output_data = json.dumps(results, indent=2, ensure_ascii=False)
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_data)
        else:
            print(output_data)

    elif output_format in ["csv", "tsv"]:
        delimiter = "," if output_format == "csv" else "\t"

        if not results:
            return

        # Determine fieldnames
        fieldnames = list(results[0].keys())

        if output_file:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(results)
        else:
            writer = csv.DictWriter(
                sys.stdout, fieldnames=fieldnames, delimiter=delimiter
            )
            writer.writeheader()
            writer.writerows(results)

