#!/usr/bin/env python3
"""
Test script to verify route suggestion feature
"""

from togoid import TogoIDConverter


def test_route_suggestion_with_alternatives():
    """Test that route suggestions are provided when direct connection fails"""
    print("Test 1: Route suggestion when direct connection fails")
    converter = TogoIDConverter()

    try:
        # Try to convert between datasets that might not be directly connected
        result = converter.convert(
            ids=['1'],
            route=['ncbigene', 'chebi'],
            format='table'
        )
        print("  ⚠ Direct connection exists, skipping this test")
        print()
    except RuntimeError as e:
        error_msg = str(e)
        print(f"  Error message:\n{error_msg}")

        # Check that the error message contains route suggestions
        if 'Try one of these routes instead' in error_msg:
            print("  ✓ Route suggestions provided")
            assert '->' in error_msg, "Should contain route format with '->'"
        elif 'No connection found' in error_msg:
            print("  ✓ No connection message displayed")
        else:
            print("  ✗ Unexpected error message format")
            raise
        print()


def test_successful_conversion():
    """Test that normal conversions still work"""
    print("Test 2: Successful conversion (no error)")
    converter = TogoIDConverter()

    # This should work without errors
    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene'],
        format='table'
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should have data"
    print(f"  ✓ Conversion successful, {len(result)} rows returned")
    print()


def test_multi_hop_route():
    """Test that multi-hop routes work correctly"""
    print("Test 3: Multi-hop route (3 datasets)")
    converter = TogoIDConverter()

    result = converter.convert(
        ids=['1', '9'],
        route=['ncbigene', 'ensembl_gene', 'ensembl_transcript'],
        format='table'
    )

    assert isinstance(result, list), "Result should be a list"
    assert len(result) > 0, "Result should have data"
    assert len(result[0]) == 3, "Each row should have 3 columns"
    print(f"  ✓ Multi-hop conversion successful, {len(result)} rows returned")
    print()


def test_find_alternative_routes_direct():
    """Test _find_alternative_routes method with direct connection"""
    print("Test 4: _find_alternative_routes - direct connection")
    converter = TogoIDConverter()

    routes = converter._find_alternative_routes('ncbigene', 'ensembl_gene')

    if routes:
        print(f"  ✓ Found {len(routes)} route(s)")
        for i, route in enumerate(routes, 1):
            print(f"    {i}. {' -> '.join(route)}")
    else:
        print("  ⚠ No routes found (may indicate API or connection issue)")
    print()


def test_find_alternative_routes_multi_hop():
    """Test _find_alternative_routes method with multi-hop connection"""
    print("Test 5: _find_alternative_routes - multi-hop connection")
    converter = TogoIDConverter()

    # Try to find routes from ncbigene to a dataset that requires multiple hops
    routes = converter._find_alternative_routes('ncbigene', 'pdb', max_hops=3)

    if routes:
        print(f"  ✓ Found {len(routes)} route(s)")
        for i, route in enumerate(routes[:3], 1):  # Show first 3
            print(f"    {i}. {' -> '.join(route)}")
        if len(routes) > 3:
            print(f"    ... and {len(routes) - 3} more")
    else:
        print("  ℹ No routes found between ncbigene and pdb")
    print()


def test_error_message_format():
    """Test that error messages are properly formatted"""
    print("Test 6: Error message format verification")
    converter = TogoIDConverter()

    try:
        # Try a conversion that will likely fail
        result = converter.convert(
            ids=['1'],
            route=['ncbigene', 'nonexistent_dataset_xyz'],
            format='table'
        )
        print("  ⚠ Unexpected success")
    except RuntimeError as e:
        error_msg = str(e)

        # Check error message format
        if 'No direct connection' in error_msg and 'Try one of these routes' in error_msg:
            print("  ✓ Error message has route suggestions")
            # Count the number of suggested routes
            route_count = error_msg.count('  - ')
            print(f"  ✓ {route_count} route(s) suggested")
        elif 'No connection found' in error_msg:
            print("  ✓ Error message indicates no connection")
        else:
            print(f"  ℹ Error message: {error_msg[:100]}...")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("Testing Route Suggestion Feature")
    print("=" * 60)
    print()

    try:
        test_successful_conversion()
        test_multi_hop_route()
        test_find_alternative_routes_direct()
        test_find_alternative_routes_multi_hop()
        test_route_suggestion_with_alternatives()
        test_error_message_format()

        print("=" * 60)
        print("All tests completed! ✓")
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
