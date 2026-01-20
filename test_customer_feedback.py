#!/usr/bin/env python3
"""
Test script to verify customer feedback fixes

Tests:
1. Dict format - returns dict with ids, route, and results
2. Table format - returns source_id and target_id pairs
3. DataFrame format - uses dataset names as column names
4. Annotations in table format - annotation comes right after source ID
5. Annotations in DataFrame format - uses "dataset field" format
6. get_ortholog DataFrame support
7. label2id DataFrame support
"""

from togoid import TogoIDConverter, LabelConverter


def test_dict_format():
    """Test Dict format returns correct structure"""
    print("Test 1: Dict format")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene'],
        format='dict'
    )

    assert isinstance(result, dict), "Result should be a dict"
    assert 'ids' in result, "Result should have 'ids' key"
    assert 'route' in result, "Result should have 'route' key"
    assert 'results' in result, "Result should have 'results' key"
    assert isinstance(result['results'], dict), "Results should be a dict"
    assert '1' in result['results'], "Results should have key '1'"
    assert isinstance(result['results']['1'], list), "Results values should be lists"
    print("✓ Dict format test passed")
    print(f"  Output: {result}")
    print()


def test_table_format():
    """Test Table format returns source-target pairs"""
    print("Test 2: Table format")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene'],
        format='table'
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should have rows"
    assert len(result[0]) == 2, "Each row should have 2 columns (source, target)"
    assert result[0][0] in ['1', '9'], "First column should be source ID"
    print("✓ Table format test passed")
    print(f"  First row: {result[0]}")
    print()


def test_dataframe_format():
    """Test DataFrame format uses dataset names as columns"""
    print("Test 3: DataFrame format")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene'],
        format='dataframe'
    )

    assert list(result.columns) == ['ncbigene', 'ensembl_gene'], \
        "Column names should be dataset names"
    assert len(result) > 0, "DataFrame should have rows"
    print("✓ DataFrame format test passed")
    print(f"  Columns: {list(result.columns)}")
    print(f"  Shape: {result.shape}")
    print()


def test_table_with_annotations():
    """Test Table format with annotations - annotation right after source ID"""
    print("Test 4: Table format with annotations")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene', 'ensembl_transcript'],
        format='table',
        annotate=[('ncbigene', 'label')]
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should have rows"
    assert len(result[0]) == 4, "Each row should have 4 columns"
    # Order should be: source_id, annotation, intermediate_id, target_id
    assert result[0][0] in ['1', '9'], "First column should be source ID"
    # Second column should be the annotation (gene label like 'A1BG')
    assert isinstance(result[0][1], str), "Second column should be annotation string"
    print("✓ Table with annotations test passed")
    print(f"  First row: {result[0]}")
    print(f"  Column order: [source_id, annotation, intermediate_id, target_id]")
    print()


def test_dataframe_with_annotations():
    """Test DataFrame format with annotations - uses 'dataset field' format"""
    print("Test 5: DataFrame format with annotations")
    converter = TogoIDConverter()
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene', 'ensembl_transcript'],
        format='dataframe',
        annotate=[('ncbigene', 'label')]
    )

    expected_columns = ['ncbigene', 'ensembl_gene', 'ensembl_transcript', 'ncbigene label']
    assert list(result.columns) == expected_columns, \
        f"Column names should be {expected_columns}, got {list(result.columns)}"
    assert len(result) > 0, "DataFrame should have rows"
    print("✓ DataFrame with annotations test passed")
    print(f"  Columns: {list(result.columns)}")
    print(f"  Shape: {result.shape}")
    print()


def test_get_ortholog_dataframe():
    """Test get_ortholog with DataFrame format"""
    print("Test 6: get_ortholog DataFrame format")
    converter = TogoIDConverter()
    result = converter.get_ortholog(
        ids=['1', '9'],
        route=['ncbigene', 'homologene'],
        target_taxids=['10090', '10116'],
        format='dataframe'
    )

    expected_columns = ['ncbigene', 'homologene', 'ncbigene', 'taxonomy']
    assert list(result.columns) == expected_columns, \
        f"Column names should be {expected_columns}, got {list(result.columns)}"
    assert len(result) > 0, "DataFrame should have rows"
    print("✓ get_ortholog DataFrame test passed")
    print(f"  Columns: {list(result.columns)}")
    print(f"  Shape: {result.shape}")
    print()


def test_label2id_dataframe():
    """Test label2id with DataFrame format"""
    print("Test 7: label2id DataFrame format")
    converter = LabelConverter()
    result = converter.convert(
        labels=['BRCA1', 'TP53'],
        dataset='ncbigene',
        taxonomy='9606',
        format='dataframe'
    )

    assert 'input' in result.columns, "DataFrame should have 'input' column"
    assert 'identifier' in result.columns, "DataFrame should have 'identifier' column"
    assert len(result) > 0, "DataFrame should have rows"
    print("✓ label2id DataFrame test passed")
    print(f"  Columns: {list(result.columns)}")
    print(f"  Shape: {result.shape}")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Customer Feedback Fixes")
    print("=" * 60)
    print()

    try:
        test_dict_format()
        test_table_format()
        test_dataframe_format()
        test_table_with_annotations()
        test_dataframe_with_annotations()
        test_get_ortholog_dataframe()
        test_label2id_dataframe()

        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
