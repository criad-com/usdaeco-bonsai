# Acceptance — 0.1.2

Measured on 2026-09-11 with Blender 5.1.2, Bonsai / IfcOpenShell 0.8.5,
core v0.9.1, axis v0.1.0, sync v0.5.0, IFC v0.1.0 and toolchain v0.3.2.
Exact refs and revisions are in [dependencies.json](../dependencies.json);
machine-readable evidence is in [acceptance.json](acceptance.json).
Release-tag snapshots keep verification independent of advancing checkouts.

| Row | Result |
|---|---|
| Structure | S01–S28 PASS; 14 applicable rules, 14 schema rules not applicable |
| check.py | 68 checks, 0 failed, 1 not run |
| pytest | 28 passed, 0 skipped |
| Native cases through entry points | 21/21: 3 wall/pipe, 9 camera, 9 data-centre cases |
| Repeat apply | 0 mutations in all 21 cases |
| Round trip | 2 elements, 14 drivers, 2 bodies, 0 differences; repeat 0 mutations |
| Final re-import comparison | 269 authored attributes match the committed crate; presentation colour/visibility excluded |
| Core validation | All 8 validators imported and loaded through UsdValidation; 0 errors, 4 warnings |
| S27 | 33 prims, 0 composition errors after relocation; complete stock fallbacks; fresh result matches committed result |
| S28 | Fresh isolated stock Embree render, no family plugins; committed PNG 960×600, 252107 bytes |
| Result inventory | 22 files, 403005 bytes / 10000000-byte cap |
| Crate | 14211 bytes, flattened final composed re-import |
| Authored layers | 19 USDA files; largest 38901 bytes / 2000000-byte cap |
| Illustrative render | 960×600, 252241 bytes; purposes guide,proxy,render |
| Term sweep | S25 clean, including archived layers; serialized crate also clean |
| Licences | MIT root; GPL-3.0-or-later for blender/operations.py and blender/__init__.py |
| Remote live integration | NOT RUN |
| Nix | One attempt; public axis v0.1.0 input resolution failed (HTTP 404) |

## Deviations

- Toolchain v0.3.1 requires Apache-2.0 text in S01 and rejects the required MIT
  root licence. The pin advances to v0.3.2, which adds MIT and per-directory
  licence support while retaining the v0.3.1 S27/S28 publication contract.
- The round trip retains the released wallpipe fixture as an explicit stage
  override. It does not prove a full-facility wall/pipe round trip. Existing
  terminal-port gaps remain outside the supported subset; the separate nine
  data-centre camera cases run natively against the base generator.
- Published layers are review copies, not resumable sync sessions. Export omits
  live document paths, execution timestamps and native transaction version
  hashes, and orders child specs by name. Explicit child-order opinions and
  driver/geometry values are retained. Native working layers are unchanged;
  the shared harness compares the review exports exactly.
- Four existing exact axis guides omit positive tolerances and produce
  ExactWithoutTolerance warnings. No precision value is invented during
  republication. There are no core validation errors.
- Sync v0.5.0 retains its old core loader; the existing local registration bridge
  loads core then axis and retains optional camera bounds. The pinned CCTV
  v0.4.8 importer callback is adapted during data-centre imports. Native operators,
  camera contracts and original case assertions remain unchanged.
- Nix packaging and an installed wheel are NOT PROVEN. The single
  `nix flake check --offline --no-write-lock-file` attempt failed on the public
  axis input. Source tests require no setuptools or installed package.
- Remote live execution remains NOT RUN. Arbitrary pipe creation, fitting
  factories and additional wall operations remain outside this release.
