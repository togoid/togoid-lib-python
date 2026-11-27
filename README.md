# TogoID Python Library

Python library and CLI tool for biological database ID conversion and annotation using [TogoID](https://togoid.dbcls.jp/).

```python
from togoid import TogoIDConverter

TogoIDConverter().convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="table")
# [['1', 'ENSG00000121410'], ['9', 'ENSG00000171428']]
```

```bash
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format table
```

## Features

- **ID conversion** between biological databases along any TogoID route
- **Annotations and filtering**: add annotation columns to conversion results, or keep only rows matching annotation values
- **Ortholog retrieval** through round-trip conversion and taxonomy filtering
- **Label to ID**: resolve labels (gene symbols, compound or disease names) to database IDs
- **Annotations** (labels and other fields) for database IDs
- Output as JSON, CSV, TSV, dict, table, or pandas DataFrame
- Usable as a Python library or as the `togoid` command-line tool

## Installation

```bash
git clone https://github.com/togoid/togoid-lib-python.git
cd togoid-lib-python

# With uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or with pip
pip install -e .
```

Optional extras (combine as needed, e.g. `".[pandas,dev]"`):

| Extra | Adds | Needed for |
|---|---|---|
| `pandas` | pandas | `format="dataframe"` |
| `dev` | test tools | development |

See [QUICKSTART_UV.md](QUICKSTART_UV.md) for more on uv.

## Python Usage

### ID Conversion

```python
from togoid import TogoIDConverter

converter = TogoIDConverter()

# Output formats
converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"])                       # JSON (raw API response, default)
converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dict")        # {'ids': [...], 'route': [...], 'results': {'1': ['ENSG00000121410'], ...}}
converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="table")       # [[source_id, target_id], ...]
converter.convert(ids=["1", "9"], route=["ncbigene", "ensembl_gene"], format="dataframe")   # pandas DataFrame
```

`format="dict"` is only available for two-dataset routes; use `table` or
`dataframe` for routes of three or more datasets.

#### Annotations and Filtering

`annotate` adds annotation columns; `filter` keeps only rows whose annotation
matches one of the given values.

```python
result = converter.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene", "ensembl_transcript"],
    format="table",
    annotate=[
        ("ncbigene", "label"),
        ("ncbigene", "full_name"),
    ],
    filter=[
        ("ensembl_transcript", "transcript_flag", ["MANE Select"]),  # 15 transcripts -> 2
    ],
)
```

#### Orthologs

```python
# ncbigene -> homologene -> ncbigene -> taxonomy, then filter by taxonomy ID
result = converter.get_ortholog(
    ids=["1", "9"],                      # Human genes
    route=["ncbigene", "homologene"],
    target_taxids=["10090", "10116"],    # Mouse and Rat
)
# [['1', '11167', '117586', '10090'],   # [source_id, homologene_id, target_gene_id, taxonomy_id]
#  ['1', '11167', '140656', '10116'],
#  ['9', '37329', '116632', '10116'],
#  ['9', '37329', '17961', '10090']]
```

#### Exploring Datasets and Routes

```python
converter.search_databases("uniprot")                  # Search databases by name
converter.search_id("NM_001110")                       # Databases whose ID pattern matches
converter.lookup_id("672")                             # Tables that contain an ID
converter.route(src="ncbigene", dst="uniprot", max_hops=3)
converter.config_list_targets("ncbigene")              # Datasets reachable in one hop
converter.count("ncbigene", "ensembl_gene", ids=["1", "9"])
```

Configuration of the TogoID API is available through `config_dataset()`,
`config_relation()`, `config_descriptions()`, `config_statistics()` and
`config_taxonomy()`.

### Label to ID

```python
from togoid import LabelConverter

label_converter = LabelConverter()

# Gene symbols
label_converter.convert(labels=["BRCA1", "TP53", "EGFR"], dataset="ncbigene", taxonomy="9606")
# [{"input": "BRCA1", "match_type": "symbol", "symbol": "BRCA1", "identifier": "672"}, ...]

# Compound names
label_converter.convert(labels=["caffeine"], dataset="chebi")

# Disease names, with a PubDictionaries matching threshold
label_converter.convert(labels=["breast cancer"], dataset="mondo", threshold=0.5)

# Override the label types configured for the dataset (must be a list)
label_converter.convert(labels=["BRCA1"], dataset="ncbigene", label_types=["symbol"], taxonomy="9606")
```

The upstream service is chosen from the dataset's `label_resolver`
configuration in the TogoID API (`/config/dataset`), not from the labels
themselves: SPARQList when `label_resolver.sparqlist` is present (e.g.
`ncbigene`), PubDictionaries otherwise (e.g. `chebi`, `mondo`). To call one of
them directly, use `convert_sparqlist()` or `convert_pubdictionaries()`.

### Annotations

```python
from togoid import AnnotationsConverter

annotator = AnnotationsConverter()

# Available fields for a dataset
for field_name, field_meta in annotator.list_fields("ncbigene"):
    print(f"{field_name}: {field_meta['label']}")

# Annotations for IDs (filters is optional)
result = annotator.execute_query(
    dataset_name="ncbigene",
    ids=["672", "7157"],
    fields=["label", "gene_synonym", "type_of_gene"],
    filters={"type_of_gene": ["protein-coding"]},
)
for id, annotations in result.items():
    print(f"{id}: {annotations}")
```

## Command-Line Usage

Conventions shared by all subcommands:

- Lists given on the command line (`--ids`, `--labels`, `--route`, ...) are comma-separated.
- List files (`--ids-file`, `--labels-file`, `--genes-file`) hold one entry per line; pass `-` to read from stdin.
- Short options: `-i` (list file), `-o` (`--output`), `-f` (`--format`), `-d` (`--dataset`), `-r` (`--route`).
- Run `togoid <command> --help` for the full list of options.

### convert

```bash
togoid convert --ids 1,9 --route ncbigene,ensembl_gene
togoid convert --ids 1,9 --route ncbigene,ensembl_gene --format csv --output results.csv

# IDs from stdin, with short options
cut -f1 genes.tsv | togoid convert -i - -r ncbigene,ensembl_gene -f table -o result.tsv

# Annotations and filtering (--filter DATASET FIELD=VALUE1,VALUE2)
togoid convert --ids 1,9 --route ncbigene,ensembl_gene,ensembl_transcript \
  --format table \
  --annotate ncbigene label \
  --annotate ncbigene full_name \
  --filter ensembl_transcript transcript_flag="MANE Select"
```

Formats: `json` (default), `csv`, `tsv`, `dict`, `table`, `dataframe`.
`--report` selects what is returned: `target` (default, target IDs only),
`pair` (source-target pairs) or `full` (every ID along the route).
Routes of three or more datasets, and any use of `--annotate`/`--filter`,
always use `full`. `--limit` and `--offset` page through large results.

### get-ortholog

```bash
togoid get-ortholog --ids 672,7157 \
  --route ncbigene,homologene \
  --target-taxids 10090,10116
```

Output defaults to a table with columns `[source_id, homologene_id, target_id, taxonomy_id]`.

### label2id

```bash
togoid label2id --dataset ncbigene --labels "BRCA1,TP53,EGFR" --taxonomy 9606
togoid label2id --dataset chebi --labels caffeine --label-types togoid_chebi_label
togoid label2id --dataset mondo --labels "breast cancer" --threshold 0.5

# From a file (one label per line; commas are kept as part of the label)
togoid label2id --dataset ncbigene --labels-file genes.txt --taxonomy 9606 --format csv --output results.csv
```

### annotate

```bash
togoid annotate --dataset ncbigene --list-fields

togoid annotate --dataset ncbigene --ids 672,7157 \
  --field type_of_gene --field gene_synonym \
  --filter type_of_gene=protein-coding

togoid annotate --dataset ncbigene --ids-file gene_ids.txt --field gene_synonym --format csv --output genes.csv
```

### Exploring Datasets and Routes

```bash
togoid search databases uniprot
togoid search id NM_001110
togoid lookup id 672
togoid route ncbigene uniprot --max-hops 3
togoid count ncbigene ensembl_gene --ids 1,9

togoid config dataset ncbigene
togoid config relation ncbigene ensembl_gene
togoid config list-targets ncbigene
togoid config descriptions
togoid config statistics
togoid config taxonomy
```

## Notes

### ID Prefixes (CURIE format)

The TogoID API can format converted IDs with their dataset prefix (CURIE), e.g.
`0005634` → `GO:0005634`, `217124` → `ORPHA:217124`. This is the **default**
output of `convert()`. Pass `prefix=False` (CLI: `--raw`) to get raw IDs:

```python
converter.convert(route=["orphanet_gene", "uniprot", "go"], ids=["217124"], report="full")
# [['ORPHA:217124', 'P23284', 'GO:0005737'], ...]

converter.convert(route=["orphanet_gene", "uniprot", "go"], ids=["217124"], report="full", prefix=False)
# [['217124', 'P23284', '0005737'], ...]
```

- Prefixing requires the server-side `?prefix` support ([togoid-api PR #149](https://github.com/togoid/togoid-api/pull/149)).
  Against API deployments that predate it, output is raw regardless of `prefix`.
- `annotate` / `filter` and `get_ortholog` transparently handle prefixed IDs: the
  library matches on the raw local ID internally, so joins keep working while the
  displayed IDs stay prefixed.
- `label2id` (`LabelConverter`) returns raw identifiers: it resolves labels via
  PubDictionaries / SPARQList, which are not covered by the API's `?prefix`.

### Route Suggestions

When two adjacent datasets in a route are not directly connected, the error
message suggests alternative routes:

```
RuntimeError: No direct connection between 'ncbigene' and 'chembl_compound'.

Suggested routes (2 hops):
- ncbigene → ensembl_gene → chembl_compound
- ncbigene → uniprot → chembl_compound
...
```

### API Endpoints

- `TOGOID_API_ENDPOINT`: TogoID API base URL (default: https://api.togoid.dbcls.jp)
- `TOGOID_GRASP_ENDPOINT`: GRASP GraphQL endpoint used for annotations (default: https://dx.dbcls.jp/grasp-dev-togoid)

```python
converter = TogoIDConverter(api_base_url="http://localhost:5000")
```

```bash
togoid --api-url http://localhost:5000 convert --ids 1,9 --route ncbigene,ensembl_gene
```

### Breaking Changes

See [CHANGELOG.md](CHANGELOG.md) for breaking changes between versions.

## Examples

### Enrichment Analysis for scRNA-seq

An example of building on TogoID: a conversion route that ends in an annotation
dataset (e.g. `ncbigene → uniprot → reactome_pathway`) is used as a gene-set
library for over-representation analysis of single-cell clusters, with the
results drawn on a UMAP.

> **Note:** This is an experimental, illustrative extension, not part of TogoID's
> core functionality. It ships as `togoid.enrichment` and the `togoid enrich`
> command, but its API may change.

- [examples/scRNAseq_enrichment/](examples/scRNAseq_enrichment/): a runnable pipeline on real data
- [docs/enrichment.md](docs/enrichment.md): the `togoid.enrichment` module, the `togoid enrich` command and the extras they need

## Requirements

- Python 3.7+
- requests >= 2.20.0
- Optional: pandas >= 1.0.0 (for `format="dataframe"`)

## Testing

```bash
python3 tests/test_readme_examples.py   # Python library examples
bash tests/test_cli_examples.sh         # CLI examples
python3 tests/test_enrichment.py        # Enrichment example (no network access required)
python3 tests/test_enrichment_api.py    # Enrichment example against the live TogoID API
```

See [TESTING.md](TESTING.md) for what each script covers.

## License

MIT License

## Links

- [TogoID Website](https://togoid.dbcls.jp/)
- [TogoID API](https://api.togoid.dbcls.jp/)
- [GitHub Repository](https://github.com/togoid/togoid-lib-python)

## Credits

Developed by DBCLS (Database Center for Life Science)
