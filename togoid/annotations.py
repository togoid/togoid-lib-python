"""
TogoID Annotations - ID to annotations converter

This module provides functionality to convert IDs to labels and annotations
using TogoID config API and GRASP GraphQL endpoint.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from itertools import product
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import requests


# Default endpoints
DEFAULT_API_ENDPOINT = os.environ.get(
    "TOGOID_API_ENDPOINT", "https://api.togoid.dbcls.jp"
)
DEFAULT_GRASP_ENDPOINT = os.environ.get(
    "TOGOID_GRASP_ENDPOINT", "https://dx.dbcls.jp/grasp-dev-togoid"
)


class AnnotationsConverter:
    """GraphQL を用いて ID をラベル・アノテーション付きデータへ変換するクラス。"""

    def __init__(
        self,
        api_endpoint: str = DEFAULT_API_ENDPOINT,
        grasp_endpoint: str = DEFAULT_GRASP_ENDPOINT,
        verbose: bool = False,
        timeout: float = 30.0,
    ):
        self.api_endpoint = api_endpoint.rstrip("/")
        self.grasp_endpoint = grasp_endpoint.rstrip("/")
        self.verbose = verbose
        self.timeout = timeout
        self.session = requests.Session()
        self._dataset_config: Optional[Dict[str, Any]] = None

    # --------------------------------------------------------------------- #
    # ヘルパー
    # --------------------------------------------------------------------- #

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[INFO] {message}", file=sys.stderr)

    def _get_dataset_config(self) -> Dict[str, Any]:
        if self._dataset_config is None:
            url = f"{self.api_endpoint}/config/dataset"
            self._log(f"Fetching dataset configuration from {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            self._dataset_config = response.json()
        return self._dataset_config

    def get_dataset(self, dataset_name: str) -> Dict[str, Any]:
        config = self._get_dataset_config()
        if dataset_name not in config:
            available = ", ".join(sorted(config.keys()))
            raise ValueError(
                f"Unknown dataset '{dataset_name}'. Available datasets: {available}"
            )
        return config[dataset_name]

    def list_fields(self, dataset_name: str) -> List[Tuple[str, Dict[str, Any]]]:
        dataset = self.get_dataset(dataset_name)
        annotations = dataset.get("annotations") or []
        fields: List[Tuple[str, Dict[str, Any]]] = []

        # Web UI では GraphQL の `label` フィールドが利用できる場合に表示されるため、
        # ここでも設定済みの項目とあわせて一覧に含める。
        fields.append(
            (
                "label",
                {
                    "label": "Label",
                    "is_list": False,
                    "items": None,
                    "description": "GRASP GraphQL が公開している標準的なラベルフィールド。",
                },
            )
        )

        for annotation in annotations:
            fields.append(
                (
                    annotation["variable"],
                    {
                        "label": annotation.get("label", annotation["variable"]),
                        "is_list": annotation.get("is_list", False),
                        "items": annotation.get("items"),
                        "numerical": annotation.get("numerical", False),
                    },
                )
            )
        return fields

    def build_query(
        self,
        dataset_name: str,
        fields: Iterable[str],
        filters: Dict[str, List[str]],
    ) -> Tuple[str, Dict[str, Any]]:
        unique_fields = []
        seen = set()
        for field in fields:
            if field == "id":
                continue
            if field not in seen:
                unique_fields.append(field)
                seen.add(field)

        variable_defs = ["$id: [String!]"]
        argument_defs = ["id: $id"]

        for field_name in filters:
            variable_defs.append(f"${field_name}: [String!]")
            argument_defs.append(f"{field_name}: ${field_name}")

        selection_set = ["id"] + unique_fields

        query_lines = [
            f"query ({', '.join(variable_defs)}) {{",
            f"  {dataset_name}({', '.join(argument_defs)}) {{",
        ]
        for field in selection_set:
            query_lines.append(f"    {field}")
        query_lines.append("  }")
        query_lines.append("}")

        query = "\n".join(query_lines)
        variables: Dict[str, Any] = {"id": []}  # GraphQL 変数の型を維持するためのダミー値

        return query, variables

    def execute_query(
        self,
        dataset_name: str,
        ids: List[str],
        fields: Iterable[str],
        filters: Optional[Dict[str, List[str]]] = None,
        format: str = "dict",
    ) -> Any:
        if filters is None:
            filters = {}

        deduped_ids = list(dict.fromkeys(ids))
        if not deduped_ids:
            raise ValueError("At least one identifier is required.")

        query, variables = self.build_query(dataset_name, fields, filters)
        variables["id"] = deduped_ids
        for key, value in filters.items():
            variables[key] = list(dict.fromkeys(value))

        payload = {"query": query, "variables": variables}
        self._log(f"Submitting GraphQL query to {self.grasp_endpoint}")

        response = self.session.post(
            self.grasp_endpoint, json=payload, timeout=self.timeout
        )
        response.raise_for_status()
        body = response.json()

        if "errors" in body:
            raise RuntimeError(f"GraphQL error: {body['errors']}")

        data = body.get("data", {})
        records = data.get(dataset_name)
        if records is None:
            raise RuntimeError(
                f"Unexpected GraphQL response: dataset '{dataset_name}' missing."
            )

        result: Dict[str, Dict[str, Any]] = {}
        for entry in records:
            identifier = entry.get("id")
            if identifier is None:
                continue
            # ID フィールドは呼び出し側で扱うため、ここでは格納しない。
            result[identifier] = {
                key: value for key, value in entry.items() if key != "id"
            }

        if format == "dataframe":
            try:
                import pandas as pd
            except ImportError:
                raise ImportError(
                    "pandas is required for dataframe format. "
                    "Install with: pip install pandas"
                )
            if not result:
                return pd.DataFrame()
            rows = [{"id": id_val, **fields_data} for id_val, fields_data in result.items()]
            return pd.DataFrame(rows)

        return result

    # --------------------------------------------------------------------- #
    # 出力フォーマット処理
    # --------------------------------------------------------------------- #

    @staticmethod
    def _normalize_value(
        value: Any, *, compact: bool, separator: str = "\n"
    ) -> Tuple[List[str], bool]:
        """
        GraphQL から得られた値を文字列リストへ正規化する。

        Returns:
            `values` と `is_list` のタプル。`values` は必ず 1 要素以上となり、
            元の値が欠損している場合でも表の形を保つため空文字を返す。
        """
        if value is None:
            return ([""], False)

        if isinstance(value, list):
            if not value:
                return ([""], True)
            if compact:
                return ([separator.join(str(v) for v in value)], True)
            return ([str(v) for v in value], True)

        return ([str(value)], False)

    def build_rows(
        self,
        dataset_label: str,
        fields: List[str],
        field_meta: Dict[str, Dict[str, Any]],
        records: Dict[str, Dict[str, Any]],
        filters: Dict[str, List[str]],
        compact: bool,
    ) -> Tuple[List[str], List[List[str]]]:
        header = [dataset_label]
        for field in fields:
            meta = field_meta.get(field, {})
            header.append(meta.get("label", field))

        rows: List[List[str]] = []
        for identifier, values in records.items():
            per_field_values: List[List[str]] = []
            skip_identifier = False
            for field in fields:
                raw_value = values.get(field)
                allowed = filters.get(field)

                if isinstance(raw_value, list) and allowed:
                    raw_value = [item for item in raw_value if item in allowed]
                elif allowed and raw_value is not None:
                    if raw_value not in allowed:
                        raw_value = None

                normalised, _ = self._normalize_value(
                    raw_value, compact=compact, separator="\n"
                )

                if allowed and all(not cell for cell in normalised):
                    skip_identifier = True
                    break

                per_field_values.append(normalised)

            if skip_identifier:
                continue

            value_product = product(*per_field_values) if per_field_values else [()]
            for combination in value_product:
                row = [identifier] + list(combination)
                rows.append(row)

        return header, rows


def parse_filters(filter_args: Optional[List[str]]) -> Dict[str, List[str]]:
    filters: Dict[str, List[str]] = {}
    if not filter_args:
        return filters

    for raw in filter_args:
        if "=" not in raw:
            raise ValueError(
                f"Invalid filter '{raw}'. Expected format 'field=value1,value2'."
            )
        field, value = raw.split("=", 1)
        field = field.strip()
        values = [v.strip() for v in value.split(",") if v.strip()]
        if not field or not values:
            raise ValueError(
                f"Invalid filter '{raw}'. Fields and values must be non-empty."
            )
        filters.setdefault(field, []).extend(values)

    return filters


def load_ids(ids: List[str], ids_file: Optional[str]) -> List[str]:
    collected: List[str] = list(ids)
    if ids_file:
        with open(ids_file, "r", encoding="utf-8") as handle:
            for line in handle:
                token = line.strip()
                if token:
                    collected.append(token)
    return collected


def ensure_fields(
    requested_fields: Optional[List[str]],
    field_catalog: Dict[str, Dict[str, Any]],
    include_label: bool,
) -> List[str]:
    seen: Set[str] = set()
    if requested_fields:
        fields = []
        for field in requested_fields:
            if field not in field_catalog:
                available = ", ".join(sorted(field_catalog.keys()))
                raise ValueError(
                    f"Unknown field '{field}'. Available fields: {available}"
                )
            if field not in seen:
                fields.append(field)
                seen.add(field)
    else:
        fields = []

    if include_label and "label" not in seen:
        fields.insert(0, "label")
        seen.add("label")

    return fields


def output_table(
    header: List[str],
    rows: List[List[str]],
    *,
    delimiter: str,
    output_path: Optional[str],
    include_header: bool,
) -> None:
    handle = (
        open(output_path, "w", newline="", encoding="utf-8")
        if output_path
        else sys.stdout
    )
    try:
        writer = csv.writer(handle, delimiter=delimiter)
        if include_header:
            writer.writerow(header)
        for row in rows:
            writer.writerow(row)
    finally:
        if handle is not sys.stdout:
            handle.close()


def output_json(
    fields: List[str],
    records: Dict[str, Dict[str, Any]],
    *,
    output_path: Optional[str],
) -> None:
    payload = []
    for identifier, values in records.items():
        entry = {"id": identifier}
        entry.update({field: values.get(field) for field in fields})
        payload.append(entry)

    handle = open(output_path, "w", encoding="utf-8") if output_path else sys.stdout
    try:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        if handle is sys.stdout:
            print()  # 対話的な利用時に改行を付与する。
    finally:
        if handle is not sys.stdout:
            handle.close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve database identifiers to labels using TogoID GraphQL."
    )
    parser.add_argument("--dataset", required=True, help="Dataset key (e.g. ncbigene).")
    parser.add_argument(
        "--ids",
        nargs="*",
        default=[],
        help="Identifiers to resolve. Repeat or separate by space.",
    )
    parser.add_argument(
        "--ids-file",
        help="Path to a file containing identifiers (one per line).",
    )
    parser.add_argument(
        "--field",
        dest="fields",
        action="append",
        help="Annotation field to include. Repeat for multiple fields.",
    )
    parser.add_argument(
        "--include-label",
        action="store_true",
        help="Include the GraphQL 'label' field when available.",
    )
    parser.add_argument(
        "--filter",
        dest="filters",
        action="append",
        help="Filter results by annotation values. Format: field=value1,value2.",
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="List available annotation fields for the dataset and exit.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format. 'table' uses tab-delimited text.",
    )
    parser.add_argument(
        "--delimiter",
        default="\t",
        help="Delimiter for table or CSV output. Defaults to tab for table mode.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Keep list-valued annotations within a single cell.",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Suppress header row in table/CSV output.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write results to a file instead of stdout.",
    )
    parser.add_argument(
        "--api-endpoint",
        default=DEFAULT_API_ENDPOINT,
        help=f"TogoID API endpoint (default: {DEFAULT_API_ENDPOINT}).",
    )
    parser.add_argument(
        "--graphql-endpoint",
        default=DEFAULT_GRASP_ENDPOINT,
        help=f"GRASP GraphQL endpoint (default: {DEFAULT_GRASP_ENDPOINT}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress messages to stderr.",
    )

    args = parser.parse_args(argv)

    converter = IDToAnnotationsConverter(
        api_endpoint=args.api_endpoint,
        grasp_endpoint=args.graphql_endpoint,
        verbose=args.verbose,
        timeout=args.timeout,
    )

    try:
        field_entries = converter.list_fields(args.dataset)
        field_catalog = {name: meta for name, meta in field_entries}
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.list_fields:
        print(f"Available annotation fields for dataset '{args.dataset}':")
        for name, meta in field_entries:
            label = meta.get("label", name)
            type_hint = "list" if meta.get("is_list") else "scalar"
            descriptor = f"{label} ({name}, {type_hint})"
            if meta.get("items"):
                descriptor += f" - allowed values: {', '.join(meta['items'])}"
            print(f"  - {descriptor}")
        return 0

    filters = parse_filters(args.filters)
    try:
        fields = ensure_fields(args.fields, field_catalog, args.include_label)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    missing_filters = set(filters) - set(fields)
    if missing_filters:
        missing = ", ".join(sorted(missing_filters))
        print(
            f"Error: Filters reference fields that are not included in the result: {missing}",
            file=sys.stderr,
        )
        return 1

    ids = load_ids(args.ids, args.ids_file)
    if not ids:
        print("Error: No identifiers provided. Use --ids or --ids-file.", file=sys.stderr)
        return 1

    try:
        dataset = converter.get_dataset(args.dataset)
        records = converter.execute_query(args.dataset, ids, fields, filters)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        output_json(fields, records, output_path=args.output)
        return 0

    delimiter = args.delimiter
    if args.format == "csv" and delimiter == "\t":
        delimiter = ","

    header, rows = converter.build_rows(
        dataset_label=dataset.get("label", args.dataset),
        fields=fields,
        field_meta=field_catalog,
        records=records,
        filters=filters,
        compact=args.compact,
    )

    if not rows:
        print("No results found for the supplied identifiers.", file=sys.stderr)
        return 0

    output_table(
        header,
        rows,
        delimiter=delimiter,
        output_path=args.output,
        include_header=not args.no_header,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
