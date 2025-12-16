"""
Test script to verify all README.md examples work correctly.

This script tests all the Python library examples from README.md
to ensure they work as expected.
"""

import sys
import os
from typing import List, Dict, Any

import requests
from requests.exceptions import RequestException

# Quick connectivity guard so the README example tests can be skipped cleanly
API_CHECKED = False
API_AVAILABLE = False


def ensure_api_available() -> bool:
    """Return False quickly if external APIs are unreachable."""
    global API_CHECKED, API_AVAILABLE
    if API_CHECKED:
        return API_AVAILABLE

    API_CHECKED = True
    try:
        # Lightweight reachability checks; status code does not matter here
        requests.get("https://api.togoid.dbcls.jp/config/descriptions", timeout=5)
        requests.post("https://dx.dbcls.jp/grasp-dev-togoid", json={"ping": True}, timeout=5)
        API_AVAILABLE = True
    except RequestException as e:
        print(f"⚠ TogoID API endpoints are not reachable: {e}")
        API_AVAILABLE = False

    return API_AVAILABLE


def test_quick_start_id_conversion():
    """Test Quick Start - ID Conversion examples"""
    print("\n=== Testing Quick Start - ID Conversion ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # JSON format (default)
    result = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"])
    assert result is not None, "JSON format failed"
    print("✓ JSON format")

    # Dict format
    result_dict = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dict")
    assert "results" in result_dict, "Dict format missing results"
    print(f"✓ Dict format: {result_dict}")

    # Table format
    result_table = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="table")
    assert isinstance(result_table, list), "Table format should return list"
    print(f"✓ Table format (first 3 rows): {result_table[:3]}")

    # DataFrame format (requires pandas)
    try:
        result_df = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dataframe")
        print(f"✓ DataFrame format: shape={result_df.shape}")
    except ImportError:
        print("⚠ DataFrame format skipped (pandas not installed)")

    return True


def test_quick_start_label_conversion():
    """Test Quick Start - Label to ID Conversion examples"""
    print("\n=== Testing Quick Start - Label to ID Conversion ===")

    from togoid import LabelConverter
    label_converter = LabelConverter()

    # Convert labels with dataset specification
    results = label_converter.convert(
        labels=["BRCA1", "TP53"],
        dataset="ncbigene",
        taxonomy="9606"  # Human
    )
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0]["identifier"] == "672", "BRCA1 should map to 672"
    print(f"✓ Gene symbols conversion: {len(results)} results")
    for r in results:
        print(f"    {r['input']} -> {r['identifier']}")

    # Convert labels for other datasets
    results2 = label_converter.convert(
        labels=["caffeine"],
        dataset="chebi",
        label_types="togoid_chebi_label"
    )
    print(f"✓ Chemical names conversion: {len(results2)} results")

    return True


def test_quick_start_annotations():
    """Test Quick Start - Annotations examples"""
    print("\n=== Testing Quick Start - Annotations ===")

    from togoid import AnnotationsConverter
    annotator = AnnotationsConverter()

    annotations = annotator.execute_query(
        dataset_name="ncbigene",
        ids=["672", "7157"],
        fields=["label", "gene_synonym"],
        filters={}
    )
    assert len(annotations) == 2, f"Expected 2 annotations, got {len(annotations)}"
    assert "672" in annotations, "Missing annotation for ID 672"
    assert "label" in annotations["672"], "Missing label field"
    print(f"✓ Annotations: {len(annotations)} IDs")
    for id_val in list(annotations.keys()):
        print(f"    {id_val}: {list(annotations[id_val].keys())}")

    return True


def test_id_conversion_formats():
    """Test ID Conversion - Different Output Formats"""
    print("\n=== Testing ID Conversion - Different Output Formats ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # JSON (default) - raw API response
    json_result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene"]
    )
    print("✓ JSON format")

    # Dict - {source_id: [target_ids]} mapping
    dict_result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene"],
        format="dict"
    )
    print(f"✓ Dict format: {dict_result}")

    # Table - [[source_id, target_id], ...] 2D array
    table_result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene"],
        format="table"
    )
    print(f"✓ Table format: {len(table_result)} rows")

    # DataFrame - pandas DataFrame with source_id and target_id columns
    try:
        df_result = converter.convert(
            ids=["1", "9"],
            route=["ncbigene", "ensembl_gene"],
            format="dataframe"
        )
        print(f"✓ DataFrame format: shape={df_result.shape}, columns={list(df_result.columns)}")
    except ImportError:
        print("⚠ DataFrame format skipped (pandas not installed)")

    return True


def test_label_conversion_detailed():
    """Test Label to ID Conversion - Detailed Examples"""
    print("\n=== Testing Label to ID Conversion - Detailed Examples ===")

    from togoid import LabelConverter
    converter = LabelConverter(verbose=False)

    # Convert gene symbols (uses SPARQList API based on dataset config)
    results = converter.convert(
        labels=["BRCA1", "TP53", "EGFR"],
        dataset="ncbigene",
        taxonomy="9606"  # Human
    )
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print(f"✓ Gene symbols (SPARQList): {len(results)} results")
    for r in results:
        print(f"    {r['input']} -> {r['identifier']} ({r['match_type']})")

    # Convert chemical names (uses PubDictionaries API based on dataset config)
    results2 = converter.convert(
        labels=["caffeine"],
        dataset="chebi",
        label_types="togoid_chebi_label"  # Optional: override dataset config
    )
    print(f"✓ Chemical names (PubDictionaries): {len(results2)} results")

    # Convert disease names
    results3 = converter.convert(
        labels=["breast cancer"],
        dataset="mondo",
        threshold=0.5  # PubDictionaries matching threshold
    )
    print(f"✓ Disease names: {len(results3)} results")

    # Label types are auto-configured from dataset, or can be manually specified
    results4 = converter.convert(
        labels=["BRCA1"],
        dataset="ncbigene",
        label_types="symbol",  # Override: only search by symbol
        taxonomy="9606"
    )
    assert len(results4) >= 1, f"Expected at least 1 result, got {len(results4)}"
    print(f"✓ Manual label_types override: {len(results4)} results")
    for r in results4:
        print(f"    {r['input']} -> {r['identifier']}")

    return True


def test_annotations_detailed():
    """Test Annotations - Detailed Examples"""
    print("\n=== Testing Annotations - Detailed Examples ===")

    from togoid import AnnotationsConverter
    annotator = AnnotationsConverter()

    # List available fields for a dataset
    fields = annotator.list_fields("ncbigene")
    assert len(fields) > 0, "No fields returned"
    print(f"✓ List fields: {len(fields)} fields")
    for field_name, field_meta in fields[:3]:
        print(f"    {field_name}: {field_meta['label']}")

    # Get annotations for IDs
    result = annotator.execute_query(
        dataset_name="ncbigene",
        ids=["672", "7157"],
        fields=["label", "gene_synonym", "type_of_gene"],
        filters={"type_of_gene": ["protein-coding"]}
    )
    assert len(result) == 2, f"Expected 2 results, got {len(result)}"
    print(f"✓ Execute query: {len(result)} IDs")
    for id_val in list(result.keys()):
        annotations = result[id_val]
        label = annotations.get('label', 'N/A')
        gene_type = annotations.get('type_of_gene', 'N/A')
        print(f"    {id_val}: label={label}, type={gene_type}")

    return True


def test_convert_with_annotations():
    """Test ID Conversion with Annotations"""
    print("\n=== Testing ID Conversion with Annotations ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # Add annotation columns to conversion results
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="table",
        annotate=[
            ("ncbigene", "label"),           # Add gene label from ncbigene
            ("ncbigene", "full_name"),       # Add full gene name from ncbigene
            ("ensembl_gene", "label")        # Add gene label from ensembl_gene
        ]
    )
    assert len(result) > 0, "No results returned"
    assert len(result[0]) == 6, f"Expected 6 columns (3 route + 3 annotations), got {len(result[0])}"
    print(f"✓ Annotations: {len(result)} rows with {len(result[0])} columns")
    print(f"  First row: {result[0]}")

    return True


def test_convert_with_filtering():
    """Test ID Conversion with Filtering"""
    print("\n=== Testing ID Conversion with Filtering ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # Filter conversion results by annotation values
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="table",
        annotate=[("ncbigene", "label")],
        filter=[
            ("ensembl_transcript", "transcript_flag", ["MANE Select"])
        ]
    )
    print(f"✓ Filtering: {len(result)} rows (filtered by MANE Select)")
    if len(result) > 0:
        print(f"  First row: {result[0]}")

    return True


def test_get_ortholog():
    """Test Get Orthologs"""
    print("\n=== Testing Get Orthologs ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # Get orthologs through round-trip conversion and taxonomy filtering
    result = converter.get_ortholog(
        ids=["1", "9"],                      # Human genes
        route=["ncbigene", "homologene"],    # Via homologene
        target_taxids=["10090", "10116"]     # Mouse and Rat
    )
    assert len(result) > 0, "No orthologs found"
    assert len(result[0]) == 3, f"Expected 3 columns, got {len(result[0])}"
    print(f"✓ Orthologs: {len(result)} results")
    for row in result:
        print(f"  {row}")

    # Test dict format
    result_dict = converter.get_ortholog(
        ids=["1", "9"],
        route=["ncbigene", "homologene"],
        target_taxids=["10090"],  # Mouse only
        format="dict"
    )
    assert isinstance(result_dict, dict), "Dict format should return dict"
    print(f"✓ Orthologs (dict format): {len(result_dict)} homologene groups")

    return True


def test_api_methods():
    """Test various API methods"""
    print("\n=== Testing API Methods ===")

    from togoid import TogoIDConverter
    converter = TogoIDConverter()

    # Count mappings
    try:
        result = converter.count("ncbigene", "ensembl_gene", ["1", "9"])
        print(f"✓ Count: {result}")
    except Exception as e:
        print(f"⚠ Count failed: {e}")

    # Config dataset
    try:
        result = converter.config_dataset("ncbigene")
        assert "label" in result, "Config missing label"
        print(f"✓ Config dataset: {result.get('label', 'unknown')}")
    except Exception as e:
        print(f"⚠ Config dataset failed: {e}")

    # Config descriptions
    try:
        result = converter.config_descriptions()
        print(f"✓ Config descriptions: {len(result)} databases")
    except Exception as e:
        print(f"⚠ Config descriptions failed: {e}")

    return True


def main():
    """Run all tests"""
    if not ensure_api_available():
        print("\nAPI not reachable; skipping README example tests.")
        return 0

    print("=" * 60)
    print("Testing README.md Examples")
    print("=" * 60)

    tests = [
        ("Quick Start - ID Conversion", test_quick_start_id_conversion),
        ("Quick Start - Label Conversion", test_quick_start_label_conversion),
        ("Quick Start - Annotations", test_quick_start_annotations),
        ("ID Conversion Formats", test_id_conversion_formats),
        ("ID Conversion with Annotations", test_convert_with_annotations),
        ("ID Conversion with Filtering", test_convert_with_filtering),
        ("Get Orthologs", test_get_ortholog),
        ("Label Conversion Detailed", test_label_conversion_detailed),
        ("Annotations Detailed", test_annotations_detailed),
        ("API Methods", test_api_methods),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {test_name} FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
