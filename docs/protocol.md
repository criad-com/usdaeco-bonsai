# JSON operation protocol

One UTF-8 request file enters Blender and one resolved IFC leaves it. No meshes
are accepted as drivers. `runner.run_blender(document, request, output)` selects
AECO_BLENDER, strips PYTHONPATH, sets the shared IFC tools path explicitly and
requires a zero process exit plus a real output artifact.

| Request member | Shape |
|---|---|
| edits | Array of sync Edit.wire() records: operation, path, ref, kind, name, value; section for size edits |
| closure | paths and disconnect arrays; the preflighted connected set |
| policy | keepConnected, disconnect or refuse |
| bindings | USD prim path to IFC GlobalId |
| cameraOperations | Compiled camera operation dictionaries, including publishType/create/delete and driver updates |

`blender/operations.py` loads the project, applies operations, commits pending
placements and saves. Camera-only batches instead use tool.Ifc.set and the shared
IFC authoring functions. `AECO_CAMERA_RESULT` reports operation count and actual
Blender / IfcOpenShell versions; `AECO_BONSAI_OK` marks completed native execution.
The adapter returns a MutationReceipt; sync owns all USD layer publication.
