"""Full-facility round-trip publication and independent source retention checks."""
import json
from pathlib import Path
import shutil

from .runtime import python


def generate_base(root, directory):
    """Generate native input in scratch space from the pinned release's sources."""
    directory.mkdir(parents=True)
    shutil.copytree(root / 'src', directory / 'src')
    shutil.copytree(root / 'spec', directory / 'spec')
    code = '''import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path('src').resolve()))
from dcbuild import layout, spec
from dcbuild.ifc.build import build, DISCIPLINES
plan = layout.resolve(spec.load())
build(plan, Path('ifc'), disciplines=list(DISCIPLINES))
'''
    print('== stage: generate pinned base IFC', flush=True)
    python(['-c', code], cwd=directory, check=True, capture_output=True, text=True, timeout=90)
    return directory / 'ifc/demo-datacentre-01.ifc'


def census(stage):
    """Measure the structural population independently of native import counts."""
    prims = list(stage.TraverseAll())
    return dict(elements=sum('AecoElementAPI' in p.GetAppliedSchemas() for p in prims),
                meshes=sum(p.GetTypeName() == 'Mesh' for p in prims),
                ports=sum(p.GetTypeName() == 'AecoPort' for p in prims),
                spaces=sum(p.GetTypeName() == 'AecoSpace' for p in prims),
                levels=sum(p.GetTypeName() == 'AecoLevel' for p in prims))


def verify_facility(source, final, manifest):
    """Reject excerpts, missing identities and changed facility population."""
    expected = {key: manifest['counts'][key] for key in census(source)}
    if census(source) != expected or census(final) != expected:
        raise AssertionError('Facility census differs from the pinned manifest')
    for prim in source.TraverseAll():
        actual = final.GetPrimAtPath(prim.GetPath())
        if not actual or actual.GetTypeName() != prim.GetTypeName():
            raise AssertionError('Pinned facility prim missing or retyped: ' + str(prim.GetPath()))
        identity = prim.GetAttribute('aeco:id')
        if identity and identity.Get() != actual.GetAttribute('aeco:id').Get():
            raise AssertionError('Pinned facility identity changed: ' + str(prim.GetPath()))
    if final.GetCompositionErrors():
        raise AssertionError('Facility composition errors')
    return expected


def connection_changes(source, imported):
    """Read native connection deletions as well as additions."""
    changes = []
    for prim in source.TraverseAll():
        if prim.GetTypeName() != 'AecoPort':
            continue
        other = imported.GetPrimAtPath(prim.GetPath())
        if not other:
            raise AssertionError('Re-import lost a pinned port')
        before = prim.GetRelationship('aeco:connectedPorts')
        after = other.GetRelationship('aeco:connectedPorts')
        targets = after.GetTargets() if after else []
        if set(before.GetTargets() if before else []) != set(targets):
            changes.append((prim.GetPath(), targets))
    return changes


def publish_connections(source, imported, layer):
    """Author explicit empty targets so a re-import deletion masks the source."""
    from pxr import Usd
    review = Usd.Stage.Open(layer)
    for path, targets in connection_changes(source, imported):
        review.OverridePrim(path).CreateRelationship('aeco:connectedPorts').SetTargets(targets)
    layer.Save()


def review_paths(source, imported, selected):
    """Include edited referents and both owners of changed port connections."""
    from pxr import Sdf
    paths = {Sdf.Path(row['path']) for row in selected.values()}
    paths.update(path.GetParentPath() for path, targets in connection_changes(source, imported))
    for path in paths:
        before, after = source.GetPrimAtPath(path), imported.GetPrimAtPath(path)
        if not before or not after or before.GetAttribute('aeco:id').Get() != after.GetAttribute('aeco:id').Get():
            raise AssertionError('Re-import changed the identity path of an edited referent')
    return sorted(paths)


def publish_view(stage, session, working, out, selected, manifest):
    """Place converged review opinions above the complete pinned base stage."""
    from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade
    from .publication import publish_roundtrip
    from .roundtrip import frame_camera
    source = Usd.Stage.Open(str(out.parent / 'inputs/source/dist/base/dc.usda'))
    paths = review_paths(source, session.current(), selected)
    final = publish_roundtrip(session, working, out / 'roundtrip', paths)
    publish_connections(source, session.current(), Sdf.Layer.FindOrOpen(str(final)))
    display = Sdf.Layer.CreateNew(str(out / 'display.usda'))
    source_layer = Sdf.Layer.CreateNew(str(out / 'source.usda'))
    source_layer.subLayerPaths = ['../inputs/source/dist/base/dc.usda']
    source_layer.Save()
    # Keep the harness's complete source arc through inputs/source weakest.
    stage.GetRootLayer().subLayerPaths[-1] = str(source_layer.realPath)
    stage.GetRootLayer().subLayerPaths.insert(0, str(final))
    stage.GetRootLayer().subLayerPaths.insert(0, str(display.realPath))
    with Usd.EditContext(stage, display):
        # A roof cutaway exposes the edited riser while retaining every prim.
        # Muting this presentation layer restores the complete enclosure.
        for prim in stage.Traverse():
            code = prim.GetAttribute('aeco:class:ifc:code')
            if code and code.Get() and (code.Get().startswith('IfcRoof') or code.Get() == 'IfcSlab.ROOF'):
                UsdGeom.Imageable(prim).CreateVisibilityAttr().Set('invisible')
        for name, row in selected.items():
            prim = stage.GetPrimAtPath(row['path'])
            # The native body is the review representation; proxies remain
            # available as guides without obscuring the measured mesh.
            proxy = prim.GetChild('Proxy')
            if proxy:
                UsdGeom.Imageable(proxy).CreateVisibilityAttr().Set('invisible')
            mesh = UsdGeom.Mesh(prim.GetChild('Geom'))
            UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).UnbindAllBindings()
            mesh.GetDisplayColorAttr().Set([Gf.Vec3f(1., .3, .035) if name == 'wall' else Gf.Vec3f(.02, .85, 1.)])
        selected_paths = [row['path'] for row in selected.values()]
        print('== stage: frame facility and edited corner', flush=True)
        frames = {name: frame_camera(stage, selected_paths, context=context)
                  for name, context in [('overview', True), ('edited_corner', False)]}
    display.Save()
    counts = verify_facility(source, stage, manifest)
    evidence = dict(counts=counts, sourcePrims=sum(1 for _ in source.TraverseAll()),
                    finalPrims=sum(1 for _ in stage.TraverseAll()),
                    selected=selected, reviewPaths=list(map(str, paths)), frames=frames)
    (out / 'facility.json').write_text(json.dumps(evidence, indent=2) + '\n')
    return evidence
