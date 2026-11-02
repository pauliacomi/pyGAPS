# Parsing and persistence: review findings

## Scope and status

This review collects parsing/persistence findings transferred from the
[core assessment](core.md). It is not yet a comprehensive parsing review.
Original finding identifiers are retained for traceability.

## High-priority findings

### C10. JSON and SQLite round trips can change branch assignments

**Status:** Open; transferred from the core review on 2026-11-02.

**Evidence.** An explicitly adsorption-only, descending point isotherm with
branches `[0, 0, 0]` becomes `[1, 1, 1]` after JSON export/import. The JSON
writer omits every adsorption marker, and the reader guesses when no marker
remains. Separately, an explicitly desorption-only ascending isotherm with
`[1, 1, 1]` becomes `[0, 0, 0]` after a SQLite round trip; its `iso_id` also
changes. SQLite stores pressure/loading and supplementary columns but excludes
the branch column.

**Action points.** Persist explicit branches in both formats and keep
legacy missing-branch interpretation versioned/backward-compatible. Test
adsorption-only descending, desorption-only ascending and mixed branches, not
only examples where the branch guess happens to recover the original.

**Sources:** [JSON writer](../../src/pygaps/parsing/json.py#L59),
[JSON reader](../../src/pygaps/parsing/json.py#L161),
[SQLite writer](../../src/pygaps/parsing/sqlite.py#L877),
[SQLite reader](../../src/pygaps/parsing/sqlite.py#L964).

## Medium-priority findings

### C18. JSON does not round-trip all valid point-isotherm coordinates

**Status:** Open; transferred from the core review on 2026-11-02.

A point isotherm with DataFrame index `[10, 20, 30]` round-trips through JSON
with index `[0, 1, 2]`, and its ID changes because the hash includes the
index. A duplicate index, which the constructor and existing tests allow,
makes `to_json()` raise `ValueError` because `orient='index'` requires unique
labels. DataFrame columns named `p` and `q` can be exported, but a default
JSON import fails unless the caller manually resupplies those keys.

**Action points.** Serialize records without requiring a unique index,
preserve coordinate-column names, and explicitly decide whether the index is
scientific identity to persist or incidental metadata to exclude from identity.
Version the format as needed. Test default and non-default keys, unique and
duplicate indices, and ID semantics. Coordinate the identity decision with
[C11 in the core review](core.md#c11-distinct-measurements-can-have-the-same-isotherm-identity).

**Sources:** [JSON representation](../../src/pygaps/parsing/json.py#L54),
[JSON reader defaults](../../src/pygaps/parsing/json.py#L84),
[point reserved keys](../../src/pygaps/core/pointisotherm.py#L91).

### C19. Database autoinsert checks the in-memory registry, not the target DB

**Status:** Open; transferred from the core review on 2026-11-02.

With a material created using `store=True` but absent from a disposable target
database, `iso.to_db(..., autoinsert_material=True)` raises `ParsingError`
from a foreign-key failure. The writer skips insertion because the material
is in `MATERIAL_LIST`; the same design is used for adsorbates. An in-memory
registry cannot establish membership in an arbitrary target database.

**Action points.** Check the target database through the active
connection, insert missing referenced records transactionally, and handle
conflicts explicitly. Test registered and unregistered objects against a
different DB, plus `autoinsert=False`.

**Source:** [SQLite autoinsert checks](../../src/pygaps/parsing/sqlite.py#L815).
