"""Native process failures never publish partial file or driver edits."""
from types import SimpleNamespace
import pytest
from aeco_sync import engine
from aeco_sync.stack import digest
from usdaeco_bonsai.gates.cctv import fixture,author
from usdaeco_bonsai import host,runner

@pytest.mark.parametrize('mode', ['exit','missing-output'])
def test_native_failure_preserves_document_and_intent(tmp_path,monkeypatch,mode):
    session=fixture(tmp_path)
    engine.readback(session,'bonsai',session.document('ifc'))
    source=session.document('bonsai');before=digest(source)
    author(session,'C-pan-tilt')
    monkeypatch.setattr(host,'run_blender',lambda *args:SimpleNamespace(returncode=1 if mode=='exit' else 0,stdout='',stderr='native failed'))
    result=engine.apply(session,'bonsai')
    assert result['mutations']==0 and result['pending']>0
    assert digest(source)==before
    assert any(d['blocking'] for d in result['diagnostics'])

def test_runner_strips_pythonpath_and_sets_explicit_ifc_tools(tmp_path,monkeypatch):
    monkeypatch.setenv('PYTHONPATH','unrelated-modules')
    monkeypatch.setattr(runner,'executable',lambda:'blender')
    observed={}
    def run(command,**options):
        observed.update(command=command,**options)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(runner.subprocess,'run',run)
    runner.run_blender('source.ifc','request.json','result.ifc')
    assert 'PYTHONPATH' not in observed['env']
    assert observed['env']['AECO_IFC_TOOLS']
    assert observed['command'][-3:]==['source.ifc','request.json','result.ifc']
    assert observed['timeout']==240
    script=runner.Path(observed['command'][observed['command'].index('--python')+1])
    assert script.is_file() and script.parent.name=='blender'

def test_review_export_keeps_drivers_geometry_and_native_layers(tmp_path):
    from pxr import Sdf, Usd, UsdGeom
    from usdaeco_bonsai.publication import review_layer
    stage=Usd.Stage.CreateInMemory()
    mesh=UsdGeom.Mesh.Define(stage,'/Element/Geom')
    mesh.GetPointsAttr().Set([(0,0,0),(1,0,0),(0,1,0)])
    prim=stage.GetPrimAtPath('/Element')
    prim.CreateAttribute('aeco:wall:height',Sdf.ValueTypeNames.Double).Set(3.)
    prim.CreateAttribute('aeco:host:bonsai:document',Sdf.ValueTypeNames.String).Set(str(tmp_path/'source.ifc'))
    prim.CreateAttribute('aeco:host:bonsai:version',Sdf.ValueTypeNames.String).Set('volatile')
    prim.CreateAttribute('aeco:host:bonsai:ref',Sdf.ValueTypeNames.String).Set('stable-reference')
    layer=stage.GetRootLayer()
    layer.customLayerData={'aeco:sync:time':'execution-time','aeco:sync:protocol':'1'}
    original=layer.ExportToString()
    target=tmp_path/'review.usda'
    review_layer(layer,target)
    assert layer.ExportToString()==original
    reviewed=Usd.Stage.Open(str(target))
    assert reviewed.GetAttributeAtPath('/Element.aeco:wall:height').Get()==3.
    assert reviewed.GetAttributeAtPath('/Element.aeco:host:bonsai:ref').Get()=='stable-reference'
    assert reviewed.GetAttributeAtPath('/Element/Geom.points').Get()==mesh.GetPointsAttr().Get()
    assert not reviewed.GetAttributeAtPath('/Element.aeco:host:bonsai:document')
    assert not reviewed.GetAttributeAtPath('/Element.aeco:host:bonsai:version')
    assert reviewed.GetRootLayer().customLayerData=={'aeco:sync:protocol':'1'}

def test_review_export_has_stable_child_order(tmp_path):
    from pxr import Sdf
    from usdaeco_bonsai.publication import review_layer
    for index, names in enumerate((('Port_Z','Port_A'),('Port_A','Port_Z'))):
        layer=Sdf.Layer.CreateAnonymous()
        parent=Sdf.CreatePrimInLayer(layer,'/Element')
        for name in names:
            Sdf.CreatePrimInLayer(layer,'/Element/'+name)
        parent.nameChildrenOrder=['Port_Z','Port_A']
        layer.customLayerData={'aeco:sync:baseVersions':{'ifc':'run-'+str(index)}}
        review_layer(layer,tmp_path/f'{index}.usda')
    assert (tmp_path/'0.usda').read_bytes()==(tmp_path/'1.usda').read_bytes()
    result=Sdf.Layer.FindOrOpen(str(tmp_path/'0.usda'))
    assert list(result.GetPrimAtPath('/Element').nameChildrenOrder)==['Port_Z','Port_A']
