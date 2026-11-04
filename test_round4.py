#!/usr/bin/env python3
"""Round 4 feedback verification tests."""
from togoid import LabelConverter, TogoIDConverter
from togoid.annotations import AnnotationsConverter

def pass_(name): print(f"[PASS] {name}")
def fail_(name, msg=""): print(f"[FAIL] {name} {msg}")

print("\n========== P-A: PubDictionaries Web UI format ==========")
lc = LabelConverter()
df = lc.convert(labels=["Lung Cancer"], dataset="mondo", format="dataframe")
print(df.to_string())
print("Columns:", list(df.columns))
if "Name" in df.columns:
    pass_("preferred label column 'Name' exists")
else:
    fail_("preferred label column 'Name' missing")
if "dictionary" not in df.columns:
    pass_("'dictionary' column removed")
else:
    fail_("'dictionary' column should be removed")
match_types = set(df["match_type"].tolist())
if match_types & {"Name", "Exact synonym", "Broad synonym"}:
    pass_(f"match_type uses human-readable labels: {match_types}")
else:
    fail_(f"match_type should use dataset.yaml label values, got {match_types}")

broad_rows = df[df["match_type"] == "Broad synonym"]
if not broad_rows.empty:
    canon = broad_rows["Name"].iloc[0]
    if canon and canon != "":
        pass_(f"canonical label resolved for Broad synonym: '{canon}'")
    else:
        fail_("canonical label not resolved for Broad synonym")
else:
    fail_("no Broad synonym row found")

print("\n========== P-B: execute_query missing IDs -> NA rows ==========")
ann = AnnotationsConverter()
df_b = ann.execute_query(
    dataset_name="ncbigene",
    ids=["1", "8", "9"],
    fields=["label", "gene_synonym"],
    format="dataframe",
)
print(df_b.to_string())
if "8" in df_b["id"].astype(str).tolist():
    row8 = df_b[df_b["id"] == "8"].iloc[0]
    label_8 = row8["label"]
    if label_8 is None or (isinstance(label_8, float) and str(label_8) == "nan"):
        pass_("missing ID '8' present with None label")
    else:
        fail_(f"missing ID '8' label should be None, got {label_8!r}")
    syn_8 = row8["gene_synonym"]
    if isinstance(syn_8, list) and len(syn_8) == 0:
        pass_("missing ID '8' gene_synonym is empty list")
    else:
        fail_(f"missing ID '8' gene_synonym should be []: {syn_8!r}")
else:
    fail_("missing ID '8' not in output")

print("\n========== P-C: annotation column dot separator ==========")
conv = TogoIDConverter()
result = conv.convert(
    ids=["1", "9"],
    route=["ncbigene", "ensembl_gene"],
    annotate=[("ncbigene", "label")],
    format="dataframe",
)
print(result.to_string())
print("Columns:", list(result.columns))
if "ncbigene.label" in result.columns:
    pass_("annotation column uses dot separator: 'ncbigene.label'")
else:
    fail_(f"expected 'ncbigene.label' column, got {list(result.columns)}")
if "ncbigene label" in result.columns:
    fail_("space-separated column 'ncbigene label' should not exist")

print("\nAll tests completed.")
