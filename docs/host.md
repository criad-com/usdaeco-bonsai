# The live IFC host

The IFC store is authoritative. Blender objects are views of products; pending
placements are committed explicitly before regeneration and export. This adapter
runs a headless Blender process with the same Bonsai operators as the live tool.
Set AECO_BLENDER to its executable. On macOS the default is the Blender executable
inside `Blender.app/Contents/MacOS` in the system Applications directory.

| Driver operation | This adapter | Native behaviour |
|---|---|---|
| Pipe end / length | Supported | DumbProfileJoiner.set_depth, then regenerate_distribution_element |
| Connected pipe end | Supported | Regenerate the port graph; extend segments, translate other neighbours |
| Pipe diameter | Supported | Published size-table profile; recalculate all affected occurrences |
| Wall transform | Supported | recalculate_walls over the connected wall set; openings follow |
| Wall height, joins, type and flip | Unsupported in this adapter | Bonsai has native operations; they are not exposed by this subset |
| New pipe or fitting | Unsupported | Requires additional native operators and take-out readback |
| Camera create, delete, move, pan/tilt, zoom, presets, type | Supported | Shared IFC authoring protocol inside Bonsai’s IFC store |
| Mesh as input | Refused | Bodies always come from native readback |

The operation contract is in [protocol.md](protocol.md). The implementation derives
from the operation survey in the released core
[host research §11.4](https://github.com/criad-com/usdaeco-core/blob/v0.8.4/docs/11-host-research-walls-pipes.md#114-bonsai--the-live-ifc-host).
That survey distinguishes native Bonsai capability from the smaller adapter subset.

A successful Blender process must produce the resolved IFC. Sync writes a temporary
file, publishes result/derived/diagnostic layers and then replaces the document.
Blender failure leaves the source file unchanged. Camera-only edits avoid importing
thousands of display meshes; they still execute against Bonsai’s IFC store.

For disconnect transactions, readback covers the edited objects, their former
port peers and affected joined walls. This keeps unrelated pre-existing gaps
outside a local edit while still rejecting gaps within its affected objects.
Other wall/pipe policies retain the released full element readback. Imported
pipe sweeps receive Bonsai's existing material-profile repair before profile
editing, and the full-facility example checks the requested depth change.
The [facility acceptance](facility-acceptance.md) records the native and
publication measurements for this release.
