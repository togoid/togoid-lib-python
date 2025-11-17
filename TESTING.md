# Testing Guide

This document describes how to test the TogoID Python library to ensure all functionality works as expected.

## Test Files

### 1. `test_readme_examples.py`

Python script that tests all the Python library examples from README.md.

**Run the tests:**

```bash
python3 test_readme_examples.py
```

**What it tests:**
- Quick Start examples (ID conversion, label conversion, annotations)
- Different output formats (JSON, dict, table, DataFrame)
- Label to ID conversion with automatic API detection
- Annotations with filters
- Various API methods (count, config, etc.)

**Expected output:**

```
============================================================
Testing README.md Examples
============================================================

=== Testing Quick Start - ID Conversion ===
✓ JSON format
✓ Dict format
✓ Table format
✓ DataFrame format

... (more tests) ...

============================================================
Test Results: 7 passed, 0 failed
============================================================
```

### 2. `test_cli_examples.sh`

Bash script that tests all CLI examples from README.md.

**Run the tests:**

```bash
bash test_cli_examples.sh
# or
./test_cli_examples.sh
```

**What it tests:**
- All CLI commands: convert, label2id, annotate, config, count
- File input/output
- Different output formats
- Various command-line options

**Expected output:**

```
======================================================================
Testing CLI Examples from README.md
======================================================================

=== Quick Start CLI Examples ===

Testing: Convert IDs (basic)
Command: timeout 15 python3 -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene
✓ PASSED

... (more tests) ...

======================================================================
Test Results Summary
======================================================================
Passed:   XX
Failed:   0
Warnings: X
======================================================================
All critical tests passed!
```

## Running Specific Tests

### Test only Python library functionality

```bash
python3 test_readme_examples.py
```

### Test only CLI functionality

```bash
bash test_cli_examples.sh
```

### Test both

```bash
python3 test_readme_examples.py && bash test_cli_examples.sh
```

## Understanding Test Results

### ✓ PASSED (Green)
The test completed successfully with expected output.

### ✗ FAILED (Red)
The test failed. This indicates a potential issue with the implementation.

### ⚠ WARNING (Yellow)
The test completed but may have issues. Often occurs when:
- External APIs are unavailable (e.g., TogoID API endpoints)
- Network timeouts
- Optional features not installed (e.g., pandas)

## Continuous Testing

You can run these tests after:
- Making changes to the codebase
- Updating dependencies
- Installing the package in a new environment
- Before creating a release

## Test Coverage

The test scripts cover:

### Python Library Tests
- [x] TogoIDConverter class
  - [x] convert() with different formats
  - [x] count() method
  - [x] config methods
- [x] LabelConverter class
  - [x] Automatic API detection
  - [x] SPARQList conversion
  - [x] PubDictionaries conversion
- [x] AnnotationsConverter class
  - [x] list_fields() method
  - [x] execute_query() method
  - [x] Filters support

### CLI Tests
- [x] convert subcommand
  - [x] Basic conversion
  - [x] Different output formats
  - [x] File output
- [x] label2id subcommand
  - [x] Basic conversion
  - [x] File input
  - [x] CSV output
  - [x] PubDictionaries usage
- [x] annotate subcommand
  - [x] Get annotations
  - [x] List fields
  - [x] Filters
  - [x] CSV output
  - [x] File input
- [x] config subcommand
- [x] count subcommand

## Known Limitations

Some API endpoints may be unavailable or return 404 errors:
- `search databases`
- `route` finding
- `lookup id`

These are API-side issues and not implementation problems. The tests will show warnings for these cases.

## Troubleshooting

### Import Errors

If you get import errors:

```bash
# Install the package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/home/souta/projects/togoid-lib-python:$PYTHONPATH
```

### Timeout Errors

If tests timeout:
- Check internet connection
- Verify TogoID API is accessible: https://api.togoid.dbcls.jp/
- Increase timeout values in test scripts

### Pandas Not Found

If DataFrame tests are skipped:

```bash
# Install pandas
pip install pandas

# Or install with pandas support
pip install -e ".[pandas]"
```

## Contributing

When adding new features:
1. Add examples to README.md
2. Add corresponding tests to test scripts
3. Run tests to ensure they pass
4. Update this document if needed
