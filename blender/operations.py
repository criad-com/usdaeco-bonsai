# SPDX-License-Identifier: GPL-3.0-or-later
"""Run inside Blender: native Bonsai operations promoted from S5."""

import json
import sys
from pathlib import Path
import os
sys.path.insert(0, os.environ["AECO_IFC_TOOLS"])
import ifcopenshell
import ifcopenshell.api
import bpy
import bonsai.tool as tool
import bonsai.core.material
import ifcopenshell.util.element as uel
from mathutils import Matrix, Vector
from bonsai.bim.module.model.profile import DumbProfileJoiner, DumbProfileRecalculator


def main():
    src, request_path, output = sys.argv[sys.argv.index("--") + 1 :]
    request = json.load(open(request_path))
    camera_operations = request.get("cameraOperations", [])
    if camera_operations and not request["edits"]:
        # Camera drivers do not depend on Blender scene objects. Keep the full
        # facility in Bonsai's IFC store without importing thousands of meshes.
        tool.Ifc.set(ifcopenshell.open(src))
    else:
        bpy.ops.bim.load_project(filepath=src)
    native = tool.Ifc.get()
    if camera_operations:
        from usdaeco_ifc._camera_ops import execute
        for operation in camera_operations:
            execute(native, operation)
    if request["policy"] == "disconnect":
        for path in request["closure"]["disconnect"]:
            ifcopenshell.api.run(
                "system.disconnect_port",
                native,
                port=native.by_guid(request["bindings"][path]),
            )
    for edit in request["edits"]:
        entity = native.by_guid(edit["ref"])
        obj = tool.Ifc.get_object(entity)
        if edit["name"] == "xformOpOrder":
            continue
        if edit["kind"] == "axis" and entity.is_a("IfcPipeSegment"):
            length = Vector(edit["value"]).length
            # Imported sweeps may carry a profile only in their representation.
            # Bonsai's joiner otherwise returns without applying the edit.
            bonsai.core.material.patch_non_parametric_mep_segment(
                tool.Ifc, tool.Material, tool.Profile, obj=obj
            )
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            with bpy.context.temp_override(
                active_object=obj, selected_objects=[obj], object=obj
            ):
                DumbProfileJoiner().set_depth(obj, length)
                bpy.context.view_layer.update()
                if request["policy"] == "keepConnected":
                    bpy.ops.bim.regenerate_distribution_element()
        elif edit["kind"] == "section":
            section = edit["section"]
            profile = (
                uel.get_material(entity, should_skip_usage=True)
                .MaterialProfiles[0]
                .Profile
            )
            profile.Radius = section["outer"] / 2
            profile.WallThickness = (section["outer"] - section["inner"]) / 2
            profile.ProfileName = section["label"]
            DumbProfileRecalculator().recalculate([obj])
        elif edit["kind"] == "transform" and entity.is_a("IfcWall"):
            obj.matrix_world = Matrix(edit["value"]).transposed()
            bpy.context.view_layer.update()
            tool.Model.recalculate_walls([obj])
        else:
            raise ValueError("Unsupported Bonsai operation: " + edit["name"])
    for obj in bpy.data.objects:
        if tool.Ifc.is_moved(obj):
            tool.Geometry.commit_placement_if_moved(obj)
    if camera_operations and not request["edits"]:
        native.write(output)
    else:
        bpy.ops.bim.save_project(filepath=output, should_save_as=True)
    if camera_operations:
        print("AECO_CAMERA_RESULT " + json.dumps(dict(operations=len(camera_operations), blender=bpy.app.version_string, ifcopenshell=ifcopenshell.version, authoring="Bonsai IFC store", diagnostics=[])))
    print("AECO_BONSAI_OK")


if __name__ == "__main__":
    main()
