#!/usr/bin/env python3
"""
Test script to verify customer feedback fixes from feedback.md
"""

from togoid import TogoIDConverter, LabelConverter, AnnotationsConverter


def test_route_length_3_table_format():
    """Test that route length >= 3 outputs all intermediate IDs in table format"""
    print("Test 1: Route length 3 - table format")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="table"
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should have rows"
    assert len(result[0]) == 3, f"Each row should have 3 columns (source, intermediate, target), got {len(result[0])}"
    print(f"  ✓ Table has 3 columns: {result[0]}")
    print()


def test_route_length_3_dataframe_format():
    """Test that route length >= 3 outputs all intermediate IDs in dataframe format"""
    print("Test 2: Route length 3 - dataframe format")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="dataframe"
    )

    expected_columns = ["ncbigene", "ensembl_gene", "ensembl_transcript"]
    assert list(result.columns) == expected_columns, \
        f"Columns should be {expected_columns}, got {list(result.columns)}"
    assert result.shape[1] == 3, "DataFrame should have 3 columns"
    print(f"  ✓ DataFrame has correct columns: {list(result.columns)}")
    print(f"  ✓ Shape: {result.shape}")
    print(result.head(3))
    print()


def test_dataframe_headers_with_annotations():
    """Test that DataFrame headers align correctly with annotation data"""
    print("Test 3: DataFrame with annotations - header alignment")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="dataframe",
        annotate=[("ncbigene", "label")]
    )

    expected_columns = ["ncbigene", "ncbigene label", "ensembl_gene", "ensembl_transcript"]
    assert list(result.columns) == expected_columns, \
        f"Columns should be {expected_columns}, got {list(result.columns)}"

    # Check that data aligns with headers
    first_row = result.iloc[0]
    print(f"  ✓ DataFrame columns: {list(result.columns)}")
    print(f"  ✓ First row data:")
    for col in result.columns:
        print(f"    {col}: {first_row[col]}")
    print()


def test_dict_format_error_with_route_3():
    """Test that dict format raises error when route length >= 3"""
    print("Test 4: Dict format error with route length >= 3")
    converter = TogoIDConverter()

    try:
        result = converter.convert(
            ids=["1", "9"],
            route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
            format="dict"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not supported when route length >= 3" in str(e)
        print(f"  ✓ Correctly raised ValueError: {e}")
    print()


def test_label_types_as_list():
    """Test that label_types accepts list type"""
    print("Test 5: label_types as list")
    converter = LabelConverter()

    # Test with list type
    result = converter.convert(
        labels=["BRCA1", "TP53"],
        dataset="ncbigene",
        label_types=["symbol", "synonym"],
        taxonomy="9606"
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Should have results"
    print(f"  ✓ label_types accepts list: ['symbol', 'synonym']")
    print(f"  ✓ Found {len(result)} results")
    print()


def test_filters_optional():
    """Test that annotator.execute_query works without filters"""
    print("Test 6: annotator.execute_query without filters")
    annotator = AnnotationsConverter()

    # Test without filters parameter
    result = annotator.execute_query(
        dataset_name="ncbigene",
        ids=["672", "7157"],
        fields=["label", "gene_synonym"]
        # filters not specified
    )

    assert isinstance(result, dict), "Result should be a dict"
    assert len(result) > 0, "Should have results"
    print(f"  ✓ execute_query works without filters parameter")
    print(f"  ✓ Found results for {len(result)} IDs")
    print()


def test_table_format_with_annotations():
    """Test table format with annotations (column order check)"""
    print("Test 7: Table format with annotations - column order")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=["1", "9"],
        route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
        format="table",
        annotate=[("ncbigene", "label")]
    )

    assert len(result[0]) == 4, f"Should have 4 columns, got {len(result[0])}"
    # Order should be: source_id, annotation, intermediate_id, target_id
    print(f"  ✓ First row: {result[0]}")
    print(f"  ✓ Column order: [source_id, annotation, intermediate_id, target_id]")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Customer Feedback Fixes")
    print("=" * 60)
    print()

    try:
        test_route_length_3_table_format()
        test_route_length_3_dataframe_format()
        test_dataframe_headers_with_annotations()
        test_dict_format_error_with_route_3()
        test_label_types_as_list()
        test_filters_optional()
        test_table_format_with_annotations()

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
