"""Regressions for full-facility publication and scoped native readback."""
import json
import shutil
from types import SimpleNamespace

import pytest
from pxr import Sdf, Usd, UsdGeom

from usdaeco_bonsai.example import census, verify_facility
from usdaeco_bonsai.publication import review_layer


def test_facility_rejects_excerpt_and_changed_identity():
    source = Usd.Stage.CreateInMemory()
    for name in ('Edited', 'Unedited'):
        prim = source.DefinePrim('/Facility/' + name, 'Xform')
        prim.ApplyAPI('AecoElementAPI')
        prim.CreateAttribute('aeco:id', Sdf.ValueTypeNames.String).Set(name)
        UsdGeom.Mesh.Define(source, prim.GetPath().AppendChild('Geom'))
    manifest = {'counts': census(source)}
    final = Usd.Stage.Open(source.Flatten())
    verify_facility(source, final, manifest)
    final.RemovePrim('/Facility/Unedited')
    with pytest.raises(AssertionError, match='census'):
        verify_facility(source, final, manifest)
    final = Usd.Stage.Open(source.Flatten())
    final.GetAttributeAtPath('/Facility/Unedited.aeco:id').Set('changed')
    with pytest.raises(AssertionError, match='identity'):
        verify_facility(source, final, manifest)


def test_scoped_review_composes_above_complete_source(tmp_path):
    source = Usd.Stage.CreateNew(str(tmp_path / 'source.usda'))
    for name in ('Edited', 'Unedited'):
        cube = UsdGeom.Cube.Define(source, '/Facility/' + name)
        cube.CreateSizeAttr(2)
    source.GetRootLayer().Save()
    final = Usd.Stage.Open(source.Flatten())
    UsdGeom.Cube(final.GetPrimAtPath('/Facility/Edited')).GetSizeAttr().Set(3)
    review_layer(final.Flatten(), tmp_path / 'review.usda', [Sdf.Path('/Facility/Edited')])
    review = Sdf.Layer.FindOrOpen(str(tmp_path / 'review.usda'))
    assert not review.GetPrimAtPath('/Facility/Unedited')
    layer = Sdf.Layer.CreateAnonymous()
    layer.subLayerPaths = [str(tmp_path / 'review.usda'), str(tmp_path / 'source.usda')]
    composed = Usd.Stage.Open(layer)
    assert composed.GetAttributeAtPath('/Facility/Edited.size').Get() == 3
    assert composed.GetAttributeAtPath('/Facility/Unedited.size').Get() == 2


def test_reimported_disconnect_masks_both_source_links(tmp_path):
    from usdaeco_bonsai.example import publish_connections
    source = Usd.Stage.CreateNew(str(tmp_path / 'source.usda'))
    for name, peer in [('Pipe', 'Elbow'), ('Elbow', 'Pipe')]:
        port = source.DefinePrim('/Facility/' + name + '/Port', 'AecoPort')
        port.CreateRelationship('aeco:connectedPorts').SetTargets(['/Facility/' + peer + '/Port'])
    source.GetRootLayer().Save()
    imported = Usd.Stage.Open(source.Flatten())
    for name in ('Pipe', 'Elbow'):
        imported.GetPrimAtPath('/Facility/' + name + '/Port').RemoveProperty('aeco:connectedPorts')
    overlay = Sdf.Layer.CreateNew(str(tmp_path / 'review.usda'))
    overlay.TransferContent(imported.Flatten())
    root = Sdf.Layer.CreateAnonymous()
    root.subLayerPaths = [str(tmp_path / 'review.usda'), str(tmp_path / 'source.usda')]
    composed = Usd.Stage.Open(root)
    assert composed.GetRelationshipAtPath('/Facility/Pipe/Port.aeco:connectedPorts').GetTargets()
    publish_connections(source, imported, overlay)
    for name in ('Pipe', 'Elbow'):
        assert composed.GetRelationshipAtPath('/Facility/' + name + '/Port.aeco:connectedPorts').GetTargets() == []


@pytest.mark.parametrize('policy, target, gap_expected', [
    ('disconnect', 'IfcWall', False),
    ('disconnect', 'IfcPipeSegment', True),
    ('keepConnected', 'IfcWall', True),
])
def test_native_readback_preserves_validation_scope(tmp_path, monkeypatch, policy, target, gap_expected):
    from aeco_sync.hosts.base import Operations
    from aeco_sync.closure import Closure
    from usdaeco_bonsai.gates.baseline import build
    from usdaeco_bonsai.host import BonsaiHost
    from usdaeco_bonsai import host as module
    from usdaeco_ifc.convert import convert
    from usdaeco_ifc._ifc_utils import world
    from ifcopenshell.api import run
    native_path = tmp_path / 'native.ifc'
    native = build(str(native_path))
    pipe = native.by_type('IfcPipeSegment')[0]
    moved = world(pipe).copy()
    moved[1, 3] += 1
    run('geometry.edit_object_placement', native, product=pipe, matrix=moved)
    native.write(str(native_path))
    model = tmp_path / 'model.usda'
    convert(str(native_path), str(model))
    session = BonsaiHost.initialize(model, native_path, tmp_path / 'session', policy=policy, kind_import=True)
    adapter = BonsaiHost(session)
    try:
        entity = adapter.f.by_type(target)[0]
        path = str(adapter.path_for(entity))
        edit = SimpleNamespace(operation='set', ref=entity.GlobalId, path=path, kind='transform',
                               wire=lambda: {'name': 'test'})
        closure = Closure(paths=[str(adapter.path_for(e)) for e in adapter.f.by_type('IfcElement')], policy=policy)
        def execute(source, request, output):
            shutil.copyfile(source, output)
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        monkeypatch.setattr(module, 'run_blender', execute)
        receipt = adapter.apply(Operations([edit], closure))
        adapter.readback(receipt.touched)
        assert any(row['code'] == 'sync:gap' for row in adapter.validate()) is gap_expected
    finally:
        adapter.close()
