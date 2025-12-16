===============================================================================
TogoID Python Library - Distribution Package
===============================================================================

Version: 1.0.0
Date: 2025-12-16
License: MIT
Package: togoid-lib-python-v1.0.0.zip (42KB)

===============================================================================
KEY FEATURES
===============================================================================

This package includes the following features:

1. ID Conversion
   - Convert biological database IDs between databases
   - Support for multiple output formats (JSON, CSV, TSV, table, DataFrame)
   - Multi-hop conversions through intermediate databases

2. Annotation Support
   - Add annotation columns during ID conversion
   - Python API: annotate parameter in convert()
   - CLI: --annotate option for convert command

3. Filtering Support
   - Filter conversion results by annotation values
   - Python API: filter parameter in convert()
   - CLI: --filter option for convert command

4. Ortholog Retrieval
   - Round-trip conversion with taxonomy filtering
   - Python API: get_ortholog() method
   - CLI: get-ortholog subcommand

5. Label to ID Conversion
   - Convert gene symbols, chemical names, disease names to database IDs
   - Dataset-based API selection (SPARQList vs PubDictionaries)
   - Auto-configuration of label_types from dataset configuration
   - Support for taxonomy filtering

6. Annotation Retrieval
   - Fetch annotations from GraphQL endpoint
   - Support for multiple fields and filtering
   - Integration with ID conversion

7. Comprehensive CLI
   - Unified command-line interface with multiple subcommands
   - Support for all library features
   - File input/output support

===============================================================================
PACKAGE CONTENTS
===============================================================================

This archive contains:

1. Source Code
   - togoid/              # Main package
     - __init__.py        # Package initialization
     - __main__.py        # CLI entry point
     - converter.py       # ID conversion (TogoIDConverter)
     - annotations.py     # Annotations (AnnotationsConverter)
     - label_converter.py # Label to ID conversion (LabelConverter)
     - cli.py            # Unified CLI

2. Documentation
   - README.md           # Main documentation
   - QUICKSTART_UV.md    # Quick start with uv
   - TESTING.md          # Testing guide
   - PROJECT_STRUCTURE.md # Project structure overview
   - DISTRIBUTION_README.txt # This file

3. Configuration
   - pyproject.toml      # Package configuration
   - requirements.txt    # Dependencies
   - .gitignore         # Git ignore rules

4. Tests
   - test_readme_examples.py  # Python library tests
   - test_cli_examples.sh     # CLI tests

===============================================================================
QUICK START
===============================================================================

Method 1: Using uv (Recommended - 10-100x faster)
--------------------------------------------------

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Extract and navigate
unzip togoid-lib-python.zip
cd togoid-lib-python

# Create virtual environment and install
uv venv
source .venv/bin/activate
uv pip install -e ".[pandas]"

# Test
togoid --version


Method 2: Using pip (Traditional)
----------------------------------

# Extract and navigate
unzip togoid-lib-python.zip
cd togoid-lib-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install
pip install -e ".[pandas]"

# Test
togoid --version


===============================================================================
USAGE EXAMPLES
===============================================================================

Command Line (CLI):
------------------

# Basic ID conversion
togoid convert --ids 1,9 --route ncbigene,ensembl_gene

# ID conversion with annotations (NEW in v1.1)
togoid convert --ids 1,9 --route ncbigene,ensembl_gene \
  --format table --annotate ncbigene label --annotate ncbigene full_name

# ID conversion with filtering (NEW in v1.1)
togoid convert --ids 1,9 --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table --filter ensembl_transcript transcript_flag "MANE Select"

# Get orthologs (NEW in v1.1)
togoid get-ortholog --ids 672,7157 --route ncbigene,homologene \
  --target-taxids 10090,10116 --format table

# Label to ID conversion
togoid label2id --labels "BRCA1,TP53" --dataset ncbigene --taxonomy 9606

# Get annotations
togoid annotate --dataset ncbigene --ids 672,7157 --field gene_synonym

# List available fields
togoid annotate --dataset ncbigene --list-fields

# Configuration info
togoid config dataset ncbigene


Python Library:
--------------

See README.md for complete examples. Here's a quick preview:

from togoid import TogoIDConverter

# Basic conversion
converter = TogoIDConverter()
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    format="table"
)

# With annotations (NEW in v1.1)
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    format="table",
    annotate=[("ncbigene", "label"), ("ncbigene", "full_name")]
)

# With filtering (NEW in v1.1)
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="table",
    filter=[("ensembl_transcript", "transcript_flag", ["MANE Select"])]
)

# Get orthologs (NEW in v1.1)
orthologs = converter.get_ortholog(
    ids=["672", "7157"],
    route=["ncbigene", "homologene"],
    target_taxids=["10090", "10116"]  # Mouse and Rat
)


===============================================================================
TESTING
===============================================================================

Quick Test:
----------
# Verify installation
togoid --version

Comprehensive Tests:
-------------------
# Test Python library (recommended)
python3 test_readme_examples.py

# Test CLI (optional, takes longer)
bash test_cli_examples.sh


===============================================================================
DOCUMENTATION
===============================================================================

Included Documentation Files:
- README.md              - Complete API documentation and usage guide
- CHANGELOG.md           - Version history and detailed change log
- QUICKSTART_UV.md       - Quick start guide using uv package manager
- TESTING.md             - Comprehensive testing guide
- PROJECT_STRUCTURE.md   - Project structure and architecture overview
- LICENSE                - MIT License full text

For the latest documentation, visit:
https://github.com/togoid/togoid-lib-python


===============================================================================
REQUIREMENTS
===============================================================================

Minimum Requirements:
- Python 3.7 or higher
- requests >= 2.20.0

Optional Dependencies:
- pandas >= 1.0.0 (for DataFrame format support)


===============================================================================
SUPPORT
===============================================================================

For issues, questions, or contributions:
- Website: https://togoid.dbcls.jp
- Repository: https://github.com/togoid/togoid-lib-python
- Issues: https://github.com/togoid/togoid-lib-python/issues


===============================================================================
LICENSE
===============================================================================

MIT License

Copyright (c) 2024 DBCLS (Database Center for Life Science)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


===============================================================================
CREDITS
===============================================================================

Developed by DBCLS (Database Center for Life Science)
https://dbcls.rois.ac.jp/

===============================================================================
