"""Shared ID helpers for the TogoID library."""
from typing import Any


def local_id(id_value: Any) -> Any:
    """
    Return the raw local ID from a (possibly) prefixed CURIE.

    Since togoid-api PR #149, /convert formats IDs with their dataset prefix
    (e.g. ``0005634`` -> ``GO:0005634``). Wherever the library reuses a converted
    ID as a string-match key (annotation joins, get_ortholog round-trips, GRASP
    lookups), it must match on the raw local ID, because those lookups are keyed
    by raw DB IDs.

    The API's format is ``PREFIX:%s`` (a single leading prefix), so the local ID
    is everything after the first ':'. IDs without a prefix (or None) are returned
    unchanged, which makes this a no-op on the current raw-ID API output — keeping
    the library correct both before and after ?prefix is deployed.

    Examples:
        ``"GO:0005634"`` -> ``"0005634"``; ``"ENSG00000121410"`` -> unchanged;
        ``None`` -> ``None``; a URI (contains ``//``) -> unchanged.
    """
    if not isinstance(id_value, str) or ':' not in id_value or '//' in id_value:
        return id_value
    return id_value.split(':', 1)[1]
