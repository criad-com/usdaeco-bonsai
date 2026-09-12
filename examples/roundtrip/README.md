# Bonsai round trip on the full base facility

Run from the repository root after the setup in the main README:

```sh
env -u PYTHONPATH "$AECO_PYTHON" examples/roundtrip/run.py --publish
```

The example composes the complete `demo-datacentre-01` base publication from
`usdaeco-datacentre v0.4.9`: 12,266 source prims, 2,954 elements, 2,987 meshes,
6,212 ports, 33 spaces and two levels. Census expectations come from the pinned
`dist/base/dc.manifest.json`. The base publication is unchanged from its recorded
generator v0.4.2; v0.4.9 supplies the release and generator used here.

The runner generates a matching IFC in temporary space, imports native drivers
through sync, moves the nearest wall by 0.15 m and extends its neighbouring pipe
by 0.20 m in Bonsai. The disconnect policy frees the edited pipe end and updates
both sides of that connection. Bonsai repairs an imported sweep's missing
material profile before its native profile editor changes the depth. The runner
requires the requested extension to appear in native readback, exports the whole
IFC, re-imports it, compares 14 drivers and two bodies, and repeats apply.

Open `result/example.usdc` with stock `usdview`. It retains every pinned facility
prim plus the converged review opinions, with no family plugin or sibling checkout
needed. The wall is orange and the pipe cyan. The presentation layer hides roof
objects to expose the interior; muting that layer restores the enclosure.
`result/vanilla.png` is the facility overview rendered from that crate in a fresh
process without family plugins, using purposes `proxy,render`. `renders/` includes
the overview and the closer edited-corner study. Cameras fit composed geometry;
`out/facility.json` records their bounds and the measured population.

The shared harness refreshes the ignored `inputs/source` alias from
`AECO_DATACENTRE_ROOT`. `out/source.usda` references
`../inputs/source/dist/base/dc.usda`; its archived copy rebases that path within
the example. Source files are never copied or edited. Recreate the alias by
running the example before opening archived overlays in a relocated checkout.

Ordinary runs refresh `out/`. `--publish` also refreshes `result/`, `renders/`
and `manifest.json`; expected findings are never rewritten. The gate compares
fresh authored USDA bytes and canonical crate content against the publication,
checks every source identity and manifest census, loads all eight core validators,
and compares authored re-imported values with the published crate.

`result/layers/out/roundtrip/` retains intent, applied and re-imported drivers,
results, derived geometry and diagnostics for the two edits and former port peer.
The full operational sessions remain temporary. Review copies omit local document
connections, execution timestamps and native file hashes. The published result
composes these opinions above the complete pinned facility. No full-facility
semantic or geometric snapshot is duplicated in the editable review layers.

Native validation uses the affected closure. Under `disconnect`, the transaction
reads the edited referents and former peers; it does not revalidate unrelated
existing terminal-port gaps across the old network. `keepConnected` retains the released whole-document readback and validation;
`validate_all` also explicitly enables whole-document validation.

The result tree is limited to 10,000,000 bytes, each USDA to 2,000,000 bytes,
and each PNG to 400,000 bytes and 1600 pixels per dimension. The native runner
has a declared 900-second budget. Packaging and source/native execution are
reported separately in [the acceptance record](../../docs/facility-acceptance.md).
