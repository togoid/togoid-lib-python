# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

The package version has stayed at 1.0.0 since the first commit, so every change
after it is listed under *Unreleased*, with its date and, where there is one, the
pull request in this repository.

## Unreleased

### Breaking Changes

- **CLI options unified** (2026-11-25, #5):
  - `label2id --label-file` is renamed to `--labels-file`, and labels in the file
    are no longer split on commas (one label per line).
  - `label2id --label_types` is renamed to `--label-types`.
  - `annotate --ids` takes a comma-separated list (`--ids 672,7157`) instead of
    space-separated values.
  - `convert --filter` takes `DATASET FIELD=VALUES` (the same condition syntax as
    `annotate --filter`) instead of three separate arguments.
- **Annotation column names** in `convert(..., annotate=...)` are joined with a
  dot: `"ncbigene label"` → `"ncbigene.label"` (2026-05-01).
- **`LabelConverter.convert_pubdictionaries()` output** follows the PubDictionaries
  Web UI layout (2026-05-01): `match_type` holds the label type from the dataset
  configuration (e.g. `Name`, `Exact synonym`), the `dictionary` column is
  removed, and a column with the preferred label is added.
- **Missing values** are `pd.NA` in DataFrame output and `None` in table output
  (2026-05-25). Previously they could appear as the string `"None"` or as `""`.

### Added

- **Experimental:** `togoid.enrichment` and the `togoid enrich` command:
  enrichment analysis that uses a TogoID route as a gene-set library, with UMAP
  visualisation, and a runnable scRNA-seq example in
  `examples/scRNAseq_enrichment/` (2026-11-04, #2; example input aligned with the
  R package's pbmc4k data on 2026-11-24, #3). This is an illustrative extension,
  not part of TogoID's core functionality. See [docs/enrichment.md](docs/enrichment.md).
- `--ids-file` for `convert`, `count` and `get-ortholog`; every list file accepts
  `-` for stdin (2026-11-25, #5).
- `togoid config list-targets SRC` (2026-11-25, #5).
- Short options `-i`, `-o`, `-f`, `-d` and `-r` across subcommands (2026-11-25, #5).
- `convert(..., prefix=False)` / `convert --raw` to get raw IDs; see *Changed*
  below (2026-07-06).
- `AnnotationsConverter.execute_query(..., format="dataframe")` for pandas output
  (2026-04-06). In DataFrame output, IDs whose lookup fails are kept as rows of
  missing values and the input order is preserved (2026-05-01).
- For PubDictionaries datasets, `label_types` accepts the label-type names from
  the dataset configuration (e.g. `Name`) as well as dictionary names
  (2026-04-06).
- `LICENSE` file, `py.typed` marker (PEP 561) and `MANIFEST.in` for the source
  distribution (2026-10-07).

### Changed

- **IDs are returned with their dataset prefix (CURIE)** by default, e.g.
  `0005634` → `GO:0005634`, when the TogoID API supports `?prefix`
  ([togoid-api PR #149](https://github.com/togoid/togoid-api/pull/149))
  (2026-07-06). Annotations, filters and `get_ortholog` match on the raw local
  ID internally, so they work with prefixed and raw output alike. `label2id`
  still returns raw IDs.
- `convert`, `count` and `label2id` send form-encoded POST requests instead of
  GET, so large inputs no longer fail with HTTP 494 (URL too long) (2026-05-25).
- `togoid --version` reports the installed package version (2026-11-25, #5).
- Test scripts moved from the repository root to `tests/` (2026-11-26).

### Fixed

- `label2id` reports an error when a dataset that requires a taxonomy is given
  none, and PubDictionaries lookups use n-gram similarity (2026-03-17).
- `config_list_targets` also lists datasets reachable through reverse links
  (2026-04-06).
- Malformed `--filter` conditions on the command line report an error instead of
  a traceback (2026-11-25, #5).

## 1.0.0 - 2026-02-09

First release in this repository. Changes relative to the earlier 0.x
development versions:

### Breaking Changes

- `LabelConverter.convert(label_types=...)` takes a list instead of a
  comma-separated string:

  ```python
  # Before
  label_converter.convert(labels=["BRCA1"], dataset="ncbigene", label_types="symbol,synonym")
  # After
  label_converter.convert(labels=["BRCA1"], dataset="ncbigene", label_types=["symbol", "synonym"])
  ```

- `format="dict"` is no longer supported for routes of three or more datasets;
  use `format="table"` or `format="dataframe"`.

### Added

- `TogoIDConverter.config_list_targets()`: datasets reachable from a source
  dataset in one hop.
- Route suggestions: when two datasets in a route are not directly connected,
  the error message suggests alternative routes.

### Changed

- Routes of three or more datasets return every intermediate ID (`report="full"`).
- The `filters` argument of `AnnotationsConverter.execute_query()` is optional.

### Fixed

- Table format outputs source-target pairs.
- DataFrame format uses dataset names as column names.
- Column order and headers of annotation output.
