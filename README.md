# TogoID Python Library

Python library and CLI tool for biological database ID conversion and annotation using [TogoID](https://togoid.dbcls.jp/).

## Features

- **ID Conversion**: Convert IDs between biological databases
- **Annotations**: Get labels and annotations for database IDs
- **Multiple Formats**: Support for JSON, CSV, TSV, dict, table, and pandas DataFrame
- **Dual Interface**: Use as Python library or command-line tool
- **Comprehensive**: Search databases, find routes, get configurations

## Installation

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
from togoid import TogoIDConverter, AnnotationsConverter

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
# Convert IDs
python -m togoid convert --ids 1,9 --route ncbigene,ensembl_gene

# or using the togoid command (after installation)
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format dict

# Get annotations
togoid annotate --dataset ncbigene --ids 672,7157 --field gene_synonym --field full_name

# List available annotation fields
togoid annotate --dataset ncbigene --list-fields

# Search databases
togoid search databases uniprot

# Find routes
togoid route ncbigene ensembl_gene

# Get configuration
togoid config dataset ncbigene
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

#### Search and Route

```python
# Search databases by name
databases = converter.search_databases("uniprot")

# Find routes between databases
routes = converter.route(src="ncbigene", dst="uniprot", max_hops=3)

# Lookup which tables contain an ID
tables = converter.lookup_id("672")
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

### AnnotationsConverter

Main class for getting annotations and labels for IDs.

**Methods:**
- `list_fields(dataset_name)` - List available annotation fields
- `execute_query(dataset_name, ids, fields, filters)` - Execute GraphQL query to get annotations
- `build_rows(dataset_label, fields, field_meta, records, filters, compact)` - Build table rows from query results

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

## License

MIT License

## Links

- [TogoID Website](https://togoid.dbcls.jp/)
- [TogoID API](https://api.togoid.dbcls.jp/)
- [GitHub Repository](https://github.com/togoid/togoid-lib-python)

## Credits

Developed by DBCLS (Database Center for Life Science)
