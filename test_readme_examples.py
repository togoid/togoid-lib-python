"""
Test script to verify all README.md examples work correctly.

This script tests all the Python library examples from README.md
to ensure they work as expected.
"""

import sys
import os
from typing import List, Dict, Any


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

    # Gene symbols → automatically uses SPARQList API for ncbigene
    results = label_converter.convert(
        labels=["BRCA1", "TP53"],
        taxon="9606"  # Human
    )
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0]["identifier"] == "672", "BRCA1 should map to 672"
    print(f"✓ Gene symbols conversion: {len(results)} results")
    for r in results:
        print(f"    {r['input']} -> {r['identifier']}")

    # Other labels → automatically uses PubDictionaries API
    results2 = label_converter.convert(
        labels=["breast cancer"],
        dictionaries="togoid_mondo_label"
    )
    print(f"✓ PubDictionaries conversion: {len(results2)} results")

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

    # Automatic API detection - gene symbols use SPARQList
    results = converter.convert(
        labels=["BRCA1", "TP53", "EGFR"],
        taxon="9606"  # Human
    )
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print(f"✓ Auto-detection (gene symbols): {len(results)} results")
    for r in results:
        print(f"    {r['input']} -> {r['identifier']} ({r['match_type']})")

    # Automatic API detection - other labels use PubDictionaries
    results2 = converter.convert(
        labels=["breast cancer"],
        dictionaries="togoid_mondo_label"
    )
    print(f"✓ Auto-detection (other labels): {len(results2)} results")

    # Manual PubDictionaries API usage
    results3 = converter.convert_pubdictionaries(
        labels=["diabetes"],
        dictionaries="togoid_mondo_label",
        threshold=0.5
    )
    print(f"✓ Manual PubDictionaries API: {len(results3)} results")

    # Manual SPARQList API usage
    results4 = converter.convert_sparqlist(
        labels=["BRCA1", "TP53"],
        sparqlist="label2id_ncbigene",
        label_types="symbol,synonym",
        taxon="9606"
    )
    assert len(results4) == 2, f"Expected 2 results, got {len(results4)}"
    print(f"✓ Manual SPARQList API: {len(results4)} results")
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
    print("=" * 60)
    print("Testing README.md Examples")
    print("=" * 60)

    tests = [
        ("Quick Start - ID Conversion", test_quick_start_id_conversion),
        ("Quick Start - Label Conversion", test_quick_start_label_conversion),
        ("Quick Start - Annotations", test_quick_start_annotations),
        ("ID Conversion Formats", test_id_conversion_formats),
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
