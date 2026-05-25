#!/usr/bin/env python3
"""Round 5 feedback verification tests."""
import pandas as pd

from togoid import LabelConverter, TogoIDConverter
from togoid.annotations import AnnotationsConverter


def pass_(name):
    print(f"[PASS] {name}")


def fail_(name, msg=""):
    print(f"[FAIL] {name} {msg}")


# ---------------- P5-A: Large convert input (POST) ----------------
print("\n========== P5-A: Large convert input (POST) ==========")
conv = TogoIDConverter()
big_ids = [str(i) for i in range(1, 6501)]
try:
    result = conv.convert(ids=big_ids, route=["ncbigene", "uniprot"], format="dataframe")
    pass_(f"convert with {len(big_ids)} IDs completed (rows={len(result)})")
except Exception as exc:  # noqa: BLE001
    fail_(f"convert with {len(big_ids)} IDs failed: {exc}")


# ---------------- P5-B: Large label2id input (POST) ----------------
print("\n========== P5-B: Large label2id input (POST) ==========")
lc = LabelConverter()
many_labels = ["Lung Cancer"] * 500
try:
    result_b = lc.convert(labels=many_labels, dataset="mondo", format="dataframe")
    if len(result_b) > 0:
        pass_(f"label2id with {len(many_labels)} labels completed (rows={len(result_b)})")
    else:
        fail_("label2id returned empty")
except Exception as exc:  # noqa: BLE001
    fail_(f"label2id failed: {exc}")


# ---------------- P5-C: converter dataframe missing value -> pd.NA ----------------
print("\n========== P5-C: converter.convert dataframe missing -> pd.NA ==========")
result_c = conv.convert(
    ids=["1", "2"],
    route=["ncbigene", "uniprot", "chembl_target"],
    format="dataframe",
)
print(result_c.to_string())
print("dtypes:", dict(result_c.dtypes))
chembl_first = result_c["chembl_target"].iloc[0]
print(f"chembl_target[0]={chembl_first!r}  type={type(chembl_first).__name__}")
# pd.NA's __bool__ raises, so check type/identity directly.
if chembl_first is pd.NA:
    pass_("dataframe missing cell is pd.NA (not the string 'None')")
elif isinstance(chembl_first, str) and chembl_first == "None":
    fail_("dataframe missing cell is still the string 'None'")
else:
    fail_(f"expected pd.NA, got {chembl_first!r} ({type(chembl_first).__name__})")


# ---------------- P5-D: converter table missing value -> Python None ----------------
print("\n========== P5-D: converter.convert table missing -> None ==========")
result_d = conv.convert(
    ids=["1", "2"],
    route=["ncbigene", "uniprot", "chembl_target"],
    format="table",
)
print(result_d)
missing_cell = result_d[0][2]
print(f"table[0][2]={missing_cell!r}  type={type(missing_cell).__name__}")
if missing_cell is None:
    pass_("table missing cell is Python None (not the string 'None')")
else:
    fail_(f"expected None, got {missing_cell!r}")


# ---------------- P5-E: label_converter dataframe Unmatched -> pd.NA ----------------
print("\n========== P5-E: label_converter.convert Unmatched -> pd.NA ==========")
result_e = lc.convert(
    labels=["AR", "dummy"], dataset="ncbigene", taxonomy="9606", format="dataframe"
)
print(result_e.to_string())
dummy_row = result_e[result_e["input"] == "dummy"].iloc[0]
identifier_val = dummy_row["identifier"]
print(f"dummy identifier={identifier_val!r}  type={type(identifier_val).__name__}")
if identifier_val is pd.NA:
    pass_("Unmatched row identifier is pd.NA (not empty string)")
elif isinstance(identifier_val, str) and identifier_val == "":
    fail_("Unmatched row identifier is still empty string")
else:
    fail_(f"expected pd.NA, got {identifier_val!r} ({type(identifier_val).__name__})")


# ---------------- P5-F: annotations execute_query missing -> pd.NA ----------------
print("\n========== P5-F: annotations missing ID -> pd.NA ==========")
ann = AnnotationsConverter()
result_f = ann.execute_query(
    dataset_name="ncbigene",
    ids=["8", "672", "7157"],
    fields=["label"],
    format="dataframe",
)
print(result_f.to_string())
row8_label = result_f[result_f["id"] == "8"]["label"].iloc[0]
print(f"id=8 label={row8_label!r}  type={type(row8_label).__name__}")
if pd.isna(row8_label):
    pass_("missing ID label is pd.NA / NaN (acceptable)")
else:
    fail_(f"expected NA, got {row8_label!r}")


print("\nAll tests completed.")
