"""Out-of-process Bonsai operators followed by the common IFC read-back."""

import json
from pathlib import Path
import tempfile
from usdaeco_ifc.host import IfcHost
from aeco_sync.hosts.base import Operations, MutationReceipt
from .runner import run_blender
from usdaeco_ifc._ifc_utils import ifcopenshell
from usdaeco_ifc import _ifc_cctv as cctv


class BonsaiHost(IfcHost):
    name = "bonsai"

    def supports(self, edit):
        if edit.operation == "create" and edit.value.get("kind") == "camera":
            return super().supports(edit)
        if edit.operation == "create":
            self._unsupported_reason = "Bonsai pipe creation is not implemented"
            return False
        if edit.name == "xformOp:transform" and edit.current is None:
            # Identity transforms may be omitted by an IFC conversion.
            from dataclasses import replace
            from pxr import UsdGeom
            from aeco_sync.stack import value
            prim = self.current.GetPrimAtPath(edit.path)
            edit = replace(edit, current=value(UsdGeom.Xformable(prim).GetLocalTransformation()))
        if not super().supports(edit):
            return False
        entity = self.f.by_guid(edit.ref)
        if cctv.is_camera(entity):
            return True
        return (
            edit.name in ("aeco:axis:end", "aeco:pipe:nominalDiameter", "xformOpOrder")
            and entity.is_a("IfcPipeSegment")
        ) or (edit.name in ("xformOp:transform", "xformOpOrder") and entity.is_a("IfcWall"))

    def apply(self, edits):
        closure = edits.closure
        bindings = {
            str(p.GetPath()): p.GetAttribute("aeco:host:ifc:ref").Get()
            for p in self.current.Traverse()
            if p.GetAttribute("aeco:host:ifc:ref")
        }
        camera_edits = [e for e in edits if (e.operation == "create" and e.value.get("kind") == "camera") or (e.ref and cctv.is_camera(self.f.by_guid(e.ref)))]
        if camera_edits:
            # Compile the shared authoring protocol in a disposable IFC transaction.
            # The authoritative application executes in Blender from the source file.
            from aeco_sync.closure import Closure
            IfcHost.apply(self, Operations(camera_edits, Closure(policy=closure.policy)))
            self.f = ifcopenshell.open(str(self.document))
        request = {
            "cameraOperations": self.camera_operations,
            "edits": [e.wire() for e in edits if e not in camera_edits],
            "closure": closure.wire(),
            "policy": closure.policy,
            "bindings": bindings,
        }
        with tempfile.TemporaryDirectory(prefix="aeco-bonsai-") as tmp:
            tmp = Path(tmp)
            request_path, out = tmp / "request.json", tmp / "resolved.ifc"
            request_path.write_text(json.dumps(request))
            proc = run_blender(self.document, request_path, out)
            if proc.returncode or not out.exists():
                raise RuntimeError(
                    "Bonsai transaction failed: " + (proc.stdout + proc.stderr)[-2500:]
                )
            self.f = ifcopenshell.open(str(out))
            evidence = next((line.removeprefix("AECO_CAMERA_RESULT ") for line in proc.stdout.splitlines() if line.startswith("AECO_CAMERA_RESULT ")), None)
            self.native_evidence = json.loads(evidence) if evidence else {}
        # Disconnect readback excludes the old network beyond the former peer.
        # Keep the released whole-document readback for other wall/pipe policies.
        paths = set(closure.paths)
        if closure.policy == "disconnect":
            # The pre-edit graph can join several services through equipment.
            # A disconnected end changes only its owner and former peer, not
            # every device reachable through the old network.
            paths = {e.path for e in edits}
            for path in closure.disconnect:
                port = self.current.GetPrimAtPath(path)
                paths.add(str(port.GetParent().GetPath()))
                paths.update(str(p.GetParentPath()) for p in
                             port.GetRelationship("aeco:connectedPorts").GetTargets())
            paths.update(path for path in closure.paths if bindings.get(path) and
                         self.f.by_guid(bindings[path]).is_a("IfcWall"))
        refs = ([op["ref"] for op in self.camera_operations if op["operation"] not in ("publishType", "delete")]
                if camera_edits and len(camera_edits) == len(edits) else
                ([bindings[path] for path in paths if bindings.get(path)] +
                 [e.ref for e in edits if e.ref]) if closure.policy == "disconnect" else
                [e.GlobalId for e in self.f.by_type("IfcElement")])
        refs = sorted(set(refs))
        self.validation_refs = set(refs)
        if (
            any(e.kind in ("axis", "transform") for e in edits)
            and closure.policy == "keepConnected"
        ):
            edited = {e.path for e in edits}
            others = [p for p in closure.paths if p not in edited]
            if others:
                self._diagnostics.add(
                    "info",
                    "sync:neighbourMoved",
                    "Bonsai regenerated the connected set",
                    others,
                )
        return MutationReceipt(tuple(refs), self.version())
