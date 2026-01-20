#!/usr/bin/env python3
"""
Test script for config_list_targets method
"""

from togoid import TogoIDConverter


def test_ncbigene():
    """Test with ncbigene as source"""
    print("Test 1: config_list_targets(source='ncbigene')")
    converter = TogoIDConverter()
    targets = converter.config_list_targets(source="ncbigene")

    assert isinstance(targets, list), "Result should be a list"
    assert len(targets) > 0, "ncbigene should have target datasets"
    assert all(isinstance(t, str) for t in targets), "All targets should be strings"

    # Check for known targets
    expected_targets = ["ensembl_gene", "hgnc", "uniprot"]
    for expected in expected_targets:
        if expected in targets:
            print(f"  ✓ Found expected target: {expected}")

    print(f"  Total targets: {len(targets)}")
    print(f"  First 10 targets: {targets[:10]}")

    # Check that list is sorted
    assert targets == sorted(targets), "Targets should be sorted"
    print("  ✓ List is sorted")

    # Check for duplicates
    assert len(targets) == len(set(targets)), "No duplicates should exist"
    print("  ✓ No duplicates")
    print()


def test_ensembl_gene():
    """Test with ensembl_gene as source"""
    print("Test 2: config_list_targets(source='ensembl_gene')")
    converter = TogoIDConverter()
    targets = converter.config_list_targets(source="ensembl_gene")

    assert isinstance(targets, list), "Result should be a list"
    assert len(targets) > 0, "ensembl_gene should have target datasets"

    print(f"  Total targets: {len(targets)}")
    print(f"  Targets: {targets}")
    print()


def test_nonexistent_source():
    """Test with non-existent source"""
    print("Test 3: config_list_targets(source='nonexistent_dataset_xyz')")
    converter = TogoIDConverter()
    targets = converter.config_list_targets(source="nonexistent_dataset_xyz")

    assert isinstance(targets, list), "Result should be a list"
    assert len(targets) == 0, "Non-existent source should return empty list"
    print("  ✓ Returns empty list for non-existent source")
    print()


def test_uniprot():
    """Test with uniprot as source"""
    print("Test 4: config_list_targets(source='uniprot')")
    converter = TogoIDConverter()
    targets = converter.config_list_targets(source="uniprot")

    assert isinstance(targets, list), "Result should be a list"
    print(f"  Total targets: {len(targets)}")
    if len(targets) > 0:
        print(f"  First 10 targets: {targets[:10]}")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing config_list_targets method")
    print("=" * 60)
    print()

    try:
        test_ncbigene()
        test_ensembl_gene()
        test_nonexistent_source()
        test_uniprot()

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
