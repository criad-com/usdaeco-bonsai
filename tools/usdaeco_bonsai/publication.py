"""Export review copies after convergence, without live connection metadata."""
from pathlib import Path


def review_layer(source, target, paths=None):
    """Keep authored opinions; omit machine connections and execution clocks.

    These copies are for review, not resumable sync sessions. The native working
    layers remain untouched. The shared harness compares these exports exactly.
    """
    from pxr import Sdf
    def children(field, source_layer, path, *unused):
        # Native port enumeration varies between processes. Copy child specs
        # by name; explicit child-order metadata is copied unchanged.
        if field == 'primChildren':
            names = sorted(source_layer.GetPrimAtPath(path).nameChildren.keys())
            if paths is not None:
                names = [name for name in names if any(
                    path.AppendChild(name).HasPrefix(root) or root.HasPrefix(path.AppendChild(name))
                    for root in paths)]
            return True, names, names
        return True
    layer = Sdf.Layer.CreateAnonymous()
    if not Sdf.CopySpec(source, '/', layer, '/', lambda *unused: True, children):
        raise ValueError('Cannot copy review opinions')
    transient = {'aeco:sync:' + field for field in ('document', 'time', 'version', 'baseVersions')}
    layer.customLayerData = {key: value for key, value in layer.customLayerData.items()
                             if key not in transient}
    paths = []
    layer.Traverse(Sdf.Path.absoluteRootPath, paths.append)
    for path in paths:
        spec = layer.GetPropertyAtPath(path)
        if (spec and spec.name.startswith('aeco:host:')
                and spec.name.rsplit(':', 1)[-1] in ('document', 'version')):
            spec.owner.RemoveProperty(spec)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not layer.Export(str(target)):
        raise ValueError('Cannot export review layer: ' + target.name)


def publish_roundtrip(session, directory, out, paths=None):
    """Archive exchange opinions for the edited closure and its final view.

    The pinned facility supplies all other referents. Full operational sessions
    stay transient; selected review layers retain drivers, bodies and diagnostics.
    """
    from pxr import Sdf
    directory, out = Path(directory), Path(out)
    for label, root in (('applied', directory / 'session'),
                        ('reimported', directory / 'reimport/session')):
        for path in sorted(root.glob('*.usda')):
            if path.name == 'stage.usda':
                continue  # Operational composition wrapper, not review opinions.
            scope = None if path.name.startswith('diagnostics.') else paths
            review_layer(Sdf.Layer.FindOrOpen(str(path)), out / label / path.name, scope)
    review_layer(Sdf.Layer.FindOrOpen(str(directory / 'intent.usda')), out / 'intent.usda')
    target = out / 'final.usdc'
    review_layer(session.current().Flatten(addSourceFileComment=False), target, paths)
    return target
