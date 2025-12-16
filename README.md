# TogoID Python Library

Python library and CLI tool for biological database ID conversion and annotation using [TogoID](https://togoid.dbcls.jp/).

## Features

- **ID Conversion**: Convert IDs between biological databases
- **ID Conversion with Annotations**: Add annotation columns during conversion
- **ID Conversion with Filtering**: Filter conversion results by annotation values
- **Ortholog Retrieval**: Get orthologs through round-trip conversion and taxonomy filtering
- **Label to ID**: Convert biological labels (gene names, etc.) to database IDs with dataset-based API selection
- **Annotations**: Get labels and annotations for database IDs
- **Multiple Formats**: Support for JSON, CSV, TSV, dict, table, and pandas DataFrame
- **Dual Interface**: Use as Python library or command-line tool
- **Comprehensive**: Search databases, find routes, get configurations

## Installation

### Using uv (recommended - faster)

[uv](https://github.com/astral-sh/uv) is a blazingly fast Python package installer and resolver (10-100x faster than pip).

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/togoid/togoid-lib-python.git
cd togoid-lib-python

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install -e .

# With pandas support
uv pip install -e ".[pandas]"

# With development tools
uv pip install -e ".[dev]"
```

**💡 Tip:** See [QUICKSTART_UV.md](QUICKSTART_UV.md) for a detailed uv quick start guide.

### Using pip (traditional)

```bash
# From source
git clone https://github.com/togoid/togoid-lib-python.git
cd togoid-lib-python
pip install -e .

# With pandas support
pip install -e ".[pandas]"
```

## Quick Start

### As a Python Library

```python
from togoid import TogoIDConverter, AnnotationsConverter, LabelConverter

# ID Conversion
converter = TogoIDConverter()

# JSON format (default)
result = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"])

# Dict format
result_dict = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dict")
# Output: {"1": ["ENSG00000121410"], "9": ["ENSG00000075624"]}

# Table format
result_table = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="table")
# Output: [["1", "ENSG00000121410"], ["9", "ENSG00000075624"]]

# DataFrame format (requires pandas)
result_df = converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dataframe")

# ID Conversion with Annotations
result_with_annotations = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="table",
    annotate=[("ncbigene", "label")]  # Add ncbigene label as annotation column
)

# ID Conversion with Filtering
result_filtered = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="table",
    annotate=[("ncbigene", "label")],
    filter=[("ensembl_transcript", "transcript_flag", ["MANE Select"])]  # Only MANE Select transcripts
)

# Get Orthologs
orthologs = converter.get_ortholog(
    ids=["1", "9"],
    route=["ncbigene", "homologene"],
    target_taxids=["10090", "10116"]  # Mouse and Rat
)

# Label to ID Conversion
label_converter = LabelConverter()

# Convert labels with dataset specification
results = label_converter.convert(
    labels=["BRCA1", "TP53"],
    dataset="ncbigene",
    taxonomy="9606"  # Human
)

# Convert labels for other datasets
results = label_converter.convert(
    labels=["caffeine"],
    dataset="chebi",
    label_types="togoid_chebi_label"
)

# Get Annotations
annotator = AnnotationsConverter()
annotations = annotator.execute_query(
    dataset_name="ncbigene",
    ids=["672", "7157"],
    fields=["label", "gene_synonym"],
    filters={}
)
```

### As a Command-Line Tool

```bash
# Basic ID Conversion
togoid convert --ids 1,9 --route ncbigene,ensembl_gene

# Convert with different output formats
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format table

# ID Conversion with Annotations
togoid convert --ids 1,9 --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label \
  --annotate ncbigene full_name

# ID Conversion with Filtering
togoid convert --ids 1,9 --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label \
  --filter ensembl_transcript transcript_flag "MANE Select"

# Get Orthologs
togoid get-ortholog --ids 672,7157 \
  --route ncbigene,homologene \
  --target-taxids 10090,10116 \
  --format table

# Label to ID Conversion
togoid label2id --labels "BRCA1,TP53,EGFR" --dataset ncbigene --taxonomy 9606

# Get Annotations
togoid annotate --dataset ncbigene --ids 672,7157 \
  --field gene_synonym \
  --field full_name

# List available annotation fields
togoid annotate --dataset ncbigene --list-fields

# Configuration
togoid config dataset ncbigene
togoid config descriptions
togoid count ncbigene ensembl_gene --ids 1,9
```

## Usage Examples

### ID Conversion

#### Different Output Formats

```python
from togoid import TogoIDConverter

converter = TogoIDConverter()

# JSON (default) - raw API response
json_result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"]
)

# Dict - {source_id: [target_ids]} mapping
dict_result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    format="dict"
)

# Table - [[source_id, target_id], ...] 2D array
table_result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    format="table"
)

# DataFrame - pandas DataFrame with source_id and target_id columns
df_result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    format="dataframe"
)
```

#### ID Conversion with Annotations

```python
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
# Result includes original conversion + 3 annotation columns
```

#### ID Conversion with Filtering

```python
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
# Only returns transcripts with "MANE Select" flag
# 15 transcripts → 2 transcripts (filtered)
```

#### Get Orthologs

```python
# Get orthologs through round-trip conversion and taxonomy filtering
# Process: ncbigene -> homologene -> ncbigene -> taxonomy -> filter by taxid
result = converter.get_ortholog(
    ids=["1", "9"],                      # Human genes
    route=["ncbigene", "homologene"],    # Via homologene
    target_taxids=["10090", "10116"]     # Mouse and Rat
)
# Returns: [
#   ['1', '11167', '117586', '10090'],   # source_id, homologene_id, mouse_gene_id, taxid
#   ['1', '11167', '140656', '10116'],   # same source via same homologene group
#   ['9', '37329', '116632', '10116'],
#   ['9', '37329', '17961', '10090']
# ]
# Rows are ordered as: [source_id, homologene_id, target_gene_id, taxonomy_id]
```

#### Search and Route

```python
# Search databases by name
databases = converter.search_databases("uniprot")

# Find routes between databases
routes = converter.route(src="ncbigene", dst="uniprot", max_hops=3)

# Lookup which tables contain an ID
tables = converter.lookup_id("672")
```

### Label to ID Conversion

```python
from togoid import LabelConverter

converter = LabelConverter(verbose=True)

# Convert gene symbols (uses SPARQList API based on dataset config)
results = converter.convert(
    labels=["BRCA1", "TP53", "EGFR"],
    dataset="ncbigene",
    taxonomy="9606"  # Human
)
# Returns: [{"input": "BRCA1", "match_type": "symbol", "symbol": "BRCA1", "identifier": "672"}, ...]

# Convert chemical names (uses PubDictionaries API based on dataset config)
results = converter.convert(
    labels=["caffeine"],
    dataset="chebi",
    label_types="togoid_chebi_label"  # Optional: override dataset config
)

# Convert disease names
results = converter.convert(
    labels=["breast cancer"],
    dataset="mondo",
    threshold=0.5  # PubDictionaries matching threshold
)

# Label types are auto-configured from dataset, or can be manually specified
results = converter.convert(
    labels=["BRCA1"],
    dataset="ncbigene",
    label_types="symbol",  # Override: only search by symbol
    taxonomy="9606"
)
```

### Annotations

```python
from togoid import AnnotationsConverter

annotator = AnnotationsConverter()

# List available fields for a dataset
fields = annotator.list_fields("ncbigene")
for field_name, field_meta in fields:
    print(f"{field_name}: {field_meta['label']}")

# Get annotations for IDs
result = annotator.execute_query(
    dataset_name="ncbigene",
    ids=["672", "7157"],
    fields=["label", "gene_synonym", "type_of_gene"],
    filters={"type_of_gene": ["protein-coding"]}
)

for id, annotations in result.items():
    print(f"{id}: {annotations}")
```

## Command-Line Interface

### Convert Command

```bash
# Basic conversion
togoid convert --ids 1,9 --route ncbigene,ensembl_gene

# With output format
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict

# Save to file
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format csv --output results.csv

# With additional parameters
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --report pair --limit 100
```

### Label2ID Command

```bash
# Basic conversion
togoid label2id --dataset ncbigene --labels "BRCA1,TP53,EGFR" --taxon 9606
togoid label2id --dataset chebi --labels 'caffeine' --label_types 'togoid_chebi_label'

# From file
echo -e "BRCA1\nTP53\nEGFR" > genes.txt
togoid label2id --dataset ncbigene --label-file genes.txt --taxon 9606

# CSV output
togoid label2id --dataset ncbigene --labels "BRCA1,TP53" --taxon 9606 --format csv --output results.csv

# With PubDictionaries (for non-gene labels)
togoid label2id --dataset chebi --labels "breast cancer" --label_types "togoid_mondo_label"

# Verbose mode
togoid label2id --dataset ncbigene --labels "BRCA1,TP53" --taxon 9606 --verbose
```

### Annotate Command

```bash
# Get annotations
togoid annotate --dataset ncbigene --ids 672,7157 --field gene_synonym --field full_name

# List available fields
togoid annotate --dataset ncbigene --list-fields

# With filters
togoid annotate --dataset ncbigene --ids 672,7157 \
    --field type_of_gene --field gene_synonym \
    --filter type_of_gene=protein-coding

# CSV output
togoid annotate --dataset ncbigene --ids 672,7157 \
    --field gene_synonym --format csv --output genes.csv

# From file
togoid annotate --dataset ncbigene --ids-file gene_ids.txt --field gene_synonym
```

### Other Commands

```bash
# Search databases
togoid search databases uniprot
togoid search id NM_001110

# Lookup ID
togoid lookup id 672

# Find routes
togoid route ncbigene uniprot --max-hops 3

# Count mappings
togoid count ncbigene ensembl_gene --ids 1,9

# Get configuration
togoid config dataset ncbigene
togoid config relation ncbigene-ensembl_gene
togoid config descriptions
togoid config statistics
togoid config taxonomy
```

## API Documentation

### TogoIDConverter

Main class for ID conversion operations.

**Methods:**
- `convert(route, ids, format='json', **kwargs)` - Convert IDs between databases
- `count(src, dst, ids, link=None)` - Count mappings
- `search_databases(name)` - Search databases by name
- `search_id(id_string)` - Search databases by ID pattern
- `lookup_id(id_string)` - Lookup which tables contain an ID
- `route(src, dst, max_hops=3)` - Find routes between databases
- `config_dataset(name=None)` - Get dataset configuration
- `config_relation(src=None, dst=None)` - Get relation configuration
- `config_descriptions()` - Get database descriptions
- `config_statistics()` - Get database statistics
- `config_taxonomy()` - Get taxonomy list

### LabelConverter

Main class for converting biological labels to database IDs with automatic API detection.

**Methods:**
- `convert(labels, dictionaries=None, tags=None, threshold=0.5, preferred_dictionary=None, label_types='symbol,synonym', taxon=None)` - Convert labels to IDs (auto-detects API)
- `convert_pubdictionaries(labels, dictionaries, tags=None, threshold=0.5, preferred_dictionary=None)` - Convert using PubDictionaries API
- `convert_sparqlist(labels, sparqlist, label_types, taxon=None)` - Convert using SPARQList API

**Auto-detection Logic:**
- If labels are gene symbols (non-numeric) → Uses SPARQList API for ncbigene
- If labels are numeric IDs or other formats → Uses PubDictionaries API
- ncbigene regex pattern is fetched from TogoID API dynamically

### AnnotationsConverter

Main class for getting annotations and labels for IDs.

**Methods:**
- `list_fields(dataset_name)` - List available annotation fields
- `execute_query(dataset_name, ids, fields, filters)` - Execute GraphQL query to get annotations
- `build_rows(dataset_label, fields, field_meta, records, filters, compact)` - Build table rows from query results

## CLI Command Reference

### Basic Commands

```bash
# Convert IDs between databases
togoid convert --ids 1,9 --route ncbigene,ensembl_gene
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict

# Label to ID conversion
togoid label2id --labels "BRCA1,TP53" --dataset ncbigene --taxonomy 9606

# Get annotations
togoid annotate --dataset ncbigene --ids 672,7157 --field label --field gene_synonym
togoid annotate --dataset ncbigene --list-fields

# Utilities
togoid count ncbigene ensembl_gene --ids 1,9

# Configuration
togoid config dataset ncbigene
togoid config descriptions
```

### Advanced Features

#### ID Conversion with Annotations

Add annotation columns to your conversion results:

```bash
# Add single annotation
togoid convert --ids 1,9 \
  --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label

# Add multiple annotations
togoid convert --ids 1,9 \
  --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label \
  --annotate ncbigene full_name \
  --annotate ensembl_transcript transcript_flag
```

#### ID Conversion with Filtering

Filter results by annotation values:

```bash
# Filter by single value
togoid convert --ids 1,9 \
  --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --filter ensembl_transcript transcript_flag "MANE Select"

# Combine annotations and filtering
togoid convert --ids 1,9 \
  --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label \
  --filter ensembl_transcript transcript_flag "MANE Select"
```

#### Ortholog Retrieval

Get orthologs using round-trip conversion:

```bash
# Get mouse and rat orthologs for human genes
togoid get-ortholog \
  --ids 672,7157 \
  --route ncbigene,homologene \
  --target-taxids 10090,10116 \
  --format table

# Output as JSON
togoid get-ortholog \
  --ids 672,7157 \
  --route ncbigene,homologene \
  --target-taxids 10090 \
  --format json
```

Table output columns are `[source_id, homologene_id, target_id, taxonomy_id]`.

### Input/Output Options

```bash
# Read IDs from file
echo "1\n9\n672" > ids.txt
togoid convert --ids-file ids.txt --route ncbigene,ensembl_gene

# Save output to file
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --output result.json

# Different output formats
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format json
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format table
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format csv
```

### Report Options

Control what information is returned:

```bash
# Only target IDs (default)
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --report target

# Source-target pairs
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --report pair

# Full path including intermediate IDs
togoid convert --ids 1,9 --route ncbigene,ensembl_gene,ensembl_transcript --report full
```

## Configuration

### Environment Variables

- `TOGOID_API_ENDPOINT` - TogoID API base URL (default: https://api.togoid.dbcls.jp)
- `TOGOID_GRASP_ENDPOINT` - GRASP GraphQL endpoint (default: https://dx.dbcls.jp/grasp-dev-togoid)

### Custom API Endpoints

```python
# Python
converter = TogoIDConverter(api_base_url="http://localhost:5000")

# CLI
togoid --api-url http://localhost:5000 convert --ids 1,9 --route ncbigene,ensembl_gene
```

## Requirements

- Python 3.7+
- requests >= 2.20.0
- pandas >= 1.0.0 (optional, for DataFrame format)

## Testing

This package includes comprehensive test scripts to verify all functionality:

```bash
# Test Python library examples
python3 test_readme_examples.py

# Test CLI examples
bash test_cli_examples.sh
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## License

MIT License

## Links

- [TogoID Website](https://togoid.dbcls.jp/)
- [TogoID API](https://api.togoid.dbcls.jp/)
- [GitHub Repository](https://github.com/togoid/togoid-lib-python)

## Credits

Developed by DBCLS (Database Center for Life Science)
