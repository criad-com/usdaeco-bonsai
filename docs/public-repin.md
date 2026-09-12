# Public re-pin — 0.1.6

All eleven direct family inputs now use public release tags. Source checks use
stable checkouts whose HEADs match the peeled tag revisions recorded in
[dependencies.json](../dependencies.json). Those source revisions are evidence;
flake URLs resolve tags because public release trees have separate commit IDs.
The toolchain selects `aeco-toolchain v0.4.0` recursively. Supported requirement
ranges are unchanged.

[Measured acceptance](public-repin.json) records the gate, native cases,
publication comparison, fresh renders and public tag probes. Earlier acceptance
records remain historical evidence for their named releases.

## Acceptance

| Check | Measured result |
|---|---|
| Family gate | 70 checks, 0 failed, 0 not run |
| Structure, including S05 | 29 rules passed; 14 not applicable |
| Pytest | 34 passed, 0 skipped; 164.30 seconds |
| Native cases / data-centre cases | 21/21 / 9/9 |
| Core validators / errors / warnings | 8 / 0 / 4 |
| Drivers / bodies / driver differences | 14 / 2 / 0 |
| Repeat mutations | 0 |
| Re-imported authored attributes compared | 179 |
| Fresh result comparison (S27) | PASS |
| Relocated plugin-free composition and rendering | PASS |
| Tagged source revisions matched | 11/11 |
| Anonymous public direct tags verified | 8/11; three not proven |
| Requirement ranges widened | 0 |

The gate reused the measured full pytest result only after verifying both source
and native-report fingerprints. It executed the full round trip, result comparison
and plugin-free checks afresh. All eight core validators loaded through
UsdValidation. Four existing warnings remain: two ExactWithoutTolerance and two
proxyClassified. There are no core errors.

## Publication

The documented `examples/roundtrip/run.py --publish` command generated the base
IFC, applied the wall and pipe edits in Bonsai, re-imported, compared drivers and
bodies, and rendered through stock USD. Against v0.1.5, all 18 published USD files
are byte-identical (1,720,909 bytes), including the flattened crate and every
archived layer. The three pinned source-layer hashes and source manifest hash,
findings, cameras and census also match. The final publication changes only pins,
recorded revisions and the resulting README hash.

The result retains 12,273 prims above the 12,266-prim source, including 2,954
elements, 2,987 meshes, 6,212 ports, 33 spaces and two levels. The result tree
remains 20 files and 1,927,637 bytes.

## Deviations

- Fresh Embree renders differ from the existing PNGs by mean absolute RGB channel
  differences of 0.33310 (edited corner), 0.32188 (overview) and 0.32202 (vanilla)
  on a 0–255 scale. All USD and camera bytes are unchanged. Retain the three
  existing PNGs and their manifest records after fresh rendering; the acceptance
  JSON preserves the fresh hashes, sizes and pixel comparisons. S28 proves fresh
  plugin-free rendering without requiring PNG byte determinism.
- Anonymous GitHub probes verified eight of the eleven direct tags, plus the
  recursive processing toolchain tag. CCTV v0.5.6, IFC v0.2.2 and scenarios v0.8.0
  requested authentication. Their public availability is **not proven** here;
  retain the specified targets pending public access and online resolution review.
- The single `nix flake check --offline --no-write-lock-file` attempt used eleven
  direct local source overrides and disabled substituters. It resolved inputs and
  evaluated the flake, then started uncached dependency builds. The attempt was
  interrupted under the no-install constraint after 38.93 seconds (exit 1).
  Nix packaging is **not proven**; no second attempt was made.
- Source tests use usd-core 26.8, Blender 5.1.2 and Bonsai/IfcOpenShell 0.8.5.
  No Python package was installed; setuptools and wheel packaging remain outside
  this evidence. The previous full dependency-layout relocation gate was not
  repeated; S27/S28 still relocate and inspect the result in isolated processes.
