# Source portability — 0.1.4

The fixture's archived `dc.usda` now resolves its own `dc.geometry.usda`.
The runner serializes the copied geometry as USDA before the round trip, so
both runtime and archive use the same filename. S29 verifies both source arcs.
[Measured evidence](source-portability.json) records both independent layouts.

| Acceptance | Original layout | Relocated layout |
|---|---:|---:|
| check.py | 69 checks, 0 failed | 69 checks, 0 failed |
| Structure, including S29 | 29 passed, 0 failed | 29 passed, 0 failed |
| ResultStale comparison | PASS | PASS |
| pytest | 28 passed, 0 skipped | 28 passed, 0 skipped |
| Native cases / repeat mutations | 21/21 / 0 | 21/21 / 0 |
| Core validators loaded / errors | 8/8 / 0 | 8/8 / 0 |
| Published prims, plugin-free | 33 | 33 |
| Compared drivers / bodies / differences | 14 / 2 / 0 | 14 / 2 / 0 |
| Published authored attributes compared | 269 | 269 |

The second checkout used a renamed repository nested separately from copied
pinned releases. Explicit dependency roots selected those releases; core
preceded axis on the plugin path, and the core checkout plus current repo
were importable through the documented PYTHONPATH. Both full check.py runs
executed pytest, all 21 native cases and the round trip afresh. No test evidence
was reused. The archived source composes with 23 prims and zero errors.

Publication retains one crate and both PNGs byte for byte against v0.1.3.
Within result/, only one geometry-reference line changed; the manifest updates
its hash and the toolchain pin. The result remains 22 files, 403005 bytes.
Fresh runs compare every authored layer byte and canonical crate content;
new images are independently checked, rather than promised byte-identical.

## Deviations

- The observed defect was a reference to `dc.geometry.usdc` after archival had
  serialized that file as `dc.geometry.usda`. No parent-checkout reference was
  present. This generated wallpipe fixture is an explicit stage override with
  example-owned source files; it needs no `inputs/source` alias. Pinned facility
  runs of the shared harness retain the documented ignored alias convention.
- The example proves the released wallpipe fixture's supported operations;
  a full-facility wall/pipe round trip remains NOT PROVEN. All nine separate
  native data-centre camera cases pass in both layouts.
- Four pre-existing exact-axis tolerance warnings remain; there are zero core
  errors. The remote live integration row remains NOT RUN in both gates.
- The one offline Nix attempt with local source overrides stopped before
  evaluation: Nix rejected their temporary directory's symlinked ancestor.
  Nix packaging remains NOT PROVEN; no retry or network fetch was made.
- The analysis interpreter uses usd-core 26.8. Stock rendering uses the existing
  OpenUSD 0.26.11 Embree runtime through a temporary launcher. No package was
  installed. README setup now selects the renderer explicitly. Blender 5.1.2
  and Bonsai / IfcOpenShell 0.8.5 supplied native execution.
