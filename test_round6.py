#!/usr/bin/env python3
"""Round 6: PR #149 (?prefix) support.

Verifies that accepting prefixed (CURIE) IDs from /convert does not break the
places where the library reuses IDs as string-match keys (annotation joins,
get_ortholog round-trips). The `_local_id` helper must be a no-op on raw IDs
so the library stays correct both before and after the API deploys ?prefix.

Fast/deterministic: network is mocked (the prefix-enabled API is not yet in prod).
Run: python test_round6.py
"""
from togoid import annotations as _ann_mod
from togoid.converter import TogoIDConverter


def _local_id_cases():
    conv = TogoIDConverter()
    # prefixed CURIE -> raw local id
    assert conv._local_id("GO:0005634") == "0005634"
    assert conv._local_id("ORPHA:217124") == "217124"
    assert conv._local_id("NCIT:C26747") == "C26747"
    # raw id without a prefix -> unchanged (no-op; pre-deploy behavior)
    assert conv._local_id("ENSG00000121410") == "ENSG00000121410"
    assert conv._local_id("1") == "1"
    assert conv._local_id("217124") == "217124"
    # None / empty -> passthrough
    assert conv._local_id(None) is None
    assert conv._local_id("") == ""
    # a full URI must not be mangled (contains '//')
    assert conv._local_id("http://purl.obolibrary.org/obo/GO_0005634") == \
        "http://purl.obolibrary.org/obo/GO_0005634"


def _annotation_join_with_prefixed_ids():
    """_add_annotations must join prefixed convert IDs against GRASP's raw-keyed
    results. GRASP only knows raw IDs, so a prefixed lookup returns nothing."""
    # GRASP knows only raw local IDs (as it does today).
    raw_labels = {"0005634": "nucleus", "0005737": "cytoplasm"}

    captured = {}

    def fake_execute_query(self, dataset_name, ids, fields, filters=None, format="json"):
        captured["ids"] = list(ids)
        # GRASP returns records only for IDs it recognises (raw, no prefix).
        return {i: {"label": raw_labels[i]} for i in ids if i in raw_labels}

    original = _ann_mod.AnnotationsConverter.execute_query
    _ann_mod.AnnotationsConverter.execute_query = fake_execute_query
    try:
        conv = TogoIDConverter()
        # convert result with PREFIXED IDs in the annotated ("go") column.
        response = {
            "ids": ["1", "9"],
            "route": ["ncbigene", "go"],
            "results": [["1", "GO:0005634"], ["9", "GO:0005737"]],
        }
        annotated = conv._add_annotations(
            response, route=["ncbigene", "go"], annotate=[("go", "label")]
        )
    finally:
        _ann_mod.AnnotationsConverter.execute_query = original

    # The library must have queried GRASP with RAW ids, not prefixed ones.
    assert captured["ids"] and all(":" not in i for i in captured["ids"]), \
        f"GRASP was queried with non-raw ids: {captured.get('ids')}"

    table = annotated["results"]
    # Prefixed display IDs are preserved, annotation column is populated.
    assert table[0] == ["1", "GO:0005634", "nucleus"], table[0]
    assert table[1] == ["9", "GO:0005737", "cytoplasm"], table[1]


def _get_ortholog_with_prefixed_ids():
    """get_ortholog matches IDs across 3 internal convert calls and compares
    taxonomy against target_taxids. With prefixed output, the raw target_taxids
    must still match (via local-id), and the displayed IDs stay prefixed."""
    conv = TogoIDConverter()

    def fake_convert(route=None, ids=None, format="json", **kwargs):
        if route == ["ncbigene", "homologene"]:
            return {"results": [["1", "HG:5"]]}
        if route == ["homologene", "ncbigene"]:
            return {"results": [["HG:5", "100"], ["HG:5", "200"]]}
        if route == ["ncbigene", "taxonomy"]:
            # taxonomy IDs come back prefixed (e.g. taxon:%s)
            return {"results": [["100", "taxon:10090"], ["200", "taxon:9606"]]}
        raise AssertionError(f"unexpected route: {route}")

    conv.convert = fake_convert
    result = conv.get_ortholog(
        ids=["1"],
        route=["ncbigene", "homologene"],
        target_taxids=["10090"],  # raw taxid, output is prefixed taxon:10090
        format="table",
    )
    # Only the mouse (10090) ortholog survives; human (9606) is filtered out.
    assert result == [["1", "HG:5", "100", "taxon:10090"]], result


def _annotations_execute_query_accepts_prefixed_ids():
    """execute_query must query GRASP with raw IDs when the caller passes prefixed
    CURIEs, and return results keyed by the caller's original ID form."""
    from togoid.annotations import AnnotationsConverter

    ann = AnnotationsConverter()
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"data": {"go": [{"id": "0005634", "label": "nucleus"}]}}

    def fake_post(url, json=None, timeout=None):
        captured["variables"] = json["variables"]
        return FakeResp()

    ann.session.post = fake_post
    result = ann.execute_query(dataset_name="go", ids=["GO:0005634"], fields=["label"])

    # GRASP is keyed by raw IDs, so the query must use the stripped local id.
    assert captured["variables"]["id"] == ["0005634"], captured["variables"]["id"]
    # The caller still sees their original (prefixed) id as the result key.
    assert result == {"GO:0005634": {"label": "nucleus"}}, result


def _convert_prefix_opt_out():
    """convert() defaults to the API's prefixed output (no param sent); prefix=False
    is the explicit opt-out that requests raw IDs via prefix=no."""
    conv = TogoIDConverter()
    captured = {}

    def fake_make_request(endpoint, method="GET", params=None, json_data=None, form_data=None):
        captured["form_data"] = dict(form_data or {})
        return {"ids": [], "route": [], "results": []}

    conv._make_request = fake_make_request

    # Default: do not send prefix -> API decides (prefixed once PR #149 ships).
    conv.convert(route=["ncbigene", "go"], ids=["1"], format="json")
    assert "prefix" not in captured["form_data"], captured["form_data"]

    # Explicit opt-out: raw IDs.
    conv.convert(route=["ncbigene", "go"], ids=["1"], format="json", prefix=False)
    assert captured["form_data"].get("prefix") == "no", captured["form_data"]

    # Explicit opt-in: rely on API default formatting (no param).
    conv.convert(route=["ncbigene", "go"], ids=["1"], format="json", prefix=True)
    assert "prefix" not in captured["form_data"], captured["form_data"]


def run():
    failures = 0
    for fn in [
        _local_id_cases,
        _annotation_join_with_prefixed_ids,
        _get_ortholog_with_prefixed_ids,
        _annotations_execute_query_accepts_prefixed_ids,
        _convert_prefix_opt_out,
    ]:
        try:
            fn()
            print(f"[PASS] {fn.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"[FAIL] {fn.__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[ERROR] {fn.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        raise SystemExit(f"\n{failures} test(s) failed.")
    print("\nAll round-6 tests passed.")


if __name__ == "__main__":
    run()
