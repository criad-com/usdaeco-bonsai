# Full-facility round trip — 0.1.5

The published result builds on the pinned base facility and retains all source
referents. The native round trip moves a wall 0.15 m and extends a pipe 0.20 m,
then re-imports the exported IFC and compares 14 drivers and two native bodies.
The facility census is read from the pinned publication manifest. Explicit empty
relationship targets preserve both sides of a native port disconnection when
the review layer composes above the pinned source.

[Measured gate and relocation evidence](facility-acceptance.json) records the
pinned sources, census, convergence, image sizes and result inventory.

| Acceptance | Original layout | Relocated layout |
|---|---:|---:|
| Family gate | 70 checks, 0 failed, 0 not run | 70 checks, 0 failed, 0 not run |
| Structure | 29/0 (14 not applicable) | 29/0 (14 not applicable) |
| ResultStale | PASS | PASS |
| Verified tests | 34 passed, 0 skipped | Same source and native-evidence hashes |
| Native cases / data-centre cases | 21/21 / 9/9 | Verified native evidence reused |
| Core registry / errors / warnings | 8 / 0 / 4 | 8 / 0 / 4 |
| Source / final prims | 12,266 / 12,273 | 12,266 / 12,273 |
| Drivers / bodies / driver differences | 14 / 2 / 0 | 14 / 2 / 0 |
| Repeat mutations | 0 | 0 |
| Re-imported authored attributes compared | 179 | 179 |
| Result tree | 20 files, 1,927,637 bytes | Canonical content matches |
| Public-name and term sweeps | PASS | PASS |

The full pytest run passed 34 tests in 174.61 seconds, with no skips. Both final
`check.py --reuse-tests` runs verified the current source and native-report hashes
before reusing that measured test evidence. Each gate ran the full facility
round trip, core validation, stock rendering and ResultStale comparison afresh.
The relocated checkout and every pinned dependency were copied into a separate
nested layout; relative source symlinks retained the tagged file structure.
All eight core validators loaded through UsdValidation; none were skipped.
The remaining warnings are two ExactWithoutTolerance and two proxyClassified
findings from the imported representations. There are zero core errors.

## Deviations

- The complete model exposed two limitations hidden by the smaller fixture.
  Disconnect readback now includes edited objects and former port peers rather
  than the entire pre-edit network. The generated base has 520 existing terminal
  connection gaps; unrelated ones remain outside this transaction. Checks still
  reject gaps in the selected closure and whole-document validation remains
  available. Bonsai's existing material-profile repair operation prepares an
  imported pipe sweep before its profile editor changes the depth. The example
  now checks that the requested 0.20 m extension was actually applied.
- Review copies retain session opinions for the wall, riser and former elbow
  peer. Full operational sessions stay transient. The pinned base supplies all
  other referents, with no duplicate full-facility snapshot in review layers.
- The presentation layer hides two roof objects to expose the edited corner.
  It retains their prims, geometry and identities. Muting presentation restores
  the enclosure. The stock facility overview and closer study use 960×600 images
  to stay within the shared 400,000-byte cap.
- Datacentre is pinned at v0.4.6. Its base publication is unchanged from the
  manifest's recorded generator v0.4.2; its three layer hashes are recorded by
  the example harness. Other dependencies retain the preceding release's pins,
  except toolchain v0.3.8. All public repository names use github.com/criad-com.
- The single Nix attempt used offline mode, direct local source overrides and
  no substituters. Resolution stopped at the nested aeco-toolchain revision
  with HTTP 404; Nix packaging remains NOT PROVEN. No retry was made.
- Source checks use usd-core 26.8. Stock Embree rendering and native Blender
  use the available runtime binaries; no package was installed. Python tests
  run from source without setuptools. Wheel packaging remains NOT PROVEN.
