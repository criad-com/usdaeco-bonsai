#!/usr/bin/env python3
"""Edit the pinned base facility through Bonsai, re-import, converge and publish."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import bootstrap
from usdaeco_check.example import run_example
from usdaeco_bonsai.example import generate_base, publish_view
from usdaeco_bonsai.roundtrip import roundtrip


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args(argv)
    example = Path(__file__).resolve().parent
    if os.environ.get('AECO_DATACENTRE_STAGE'):
        raise ValueError('This example requires the pinned base variant; unset AECO_DATACENTRE_STAGE')
    dc = Path(os.environ.get('AECO_DATACENTRE_ROOT', ROOT.parent / 'usdaeco-datacentre')).resolve()
    os.environ['AECO_DATACENTRE_ROOT'] = str(dc)
    publication = json.loads((dc / 'dist/base/dc.manifest.json').read_text())
    if os.environ.get('USDRECORD'):
        os.environ['PATH'] = str(Path(os.environ['USDRECORD']).resolve().parent) + os.pathsep + os.environ.get('PATH', '')
    # Load the released kind libraries before any schema registry is created.
    # The protocol test fixture is deliberately not used for this example.
    from aeco_sync import register_plugins
    from pxr import Plug
    from usdaeco_bonsai.plugins import _resource
    plugins = []
    for name, library in (("buildup", "usdAecoBuildUp"), ("wall", "usdAecoWall"), ("pipe", "usdAecoPipe")):
        sibling = Path(os.environ.get("AECO_" + name.upper() + "_ROOT", ROOT.parent / ("usdaeco-" + name)))
        plugins.append(_resource(sibling, library))
    core = Path(os.environ.get("AECO_CORE", os.environ.get("AECO_CORE_ROOT", ROOT.parent / "usdaeco-core")))
    axis = Path(os.environ.get("AECO_AXIS_ROOT", ROOT.parent / "usdaeco-axis"))
    os.environ["PXR_PLUGINPATH_NAME"] = os.pathsep.join([
        str(_resource(core, "usdAeco", "CORE_PLUGIN_DIR")),
        str(_resource(axis, "usdAecoAxis", "AXIS_PLUGIN_DIR")), *map(str, plugins)])
    os.environ["AECO_KIND_PLUGIN"] = str(plugins[0])
    register_plugins()
    for plugin in plugins[1:]: Plug.Registry().RegisterPlugins(str(plugin))
    with tempfile.TemporaryDirectory(prefix='aeco-bonsai-example-') as temporary:
        temporary = Path(temporary)
        def hook(stage, out):
            source = generate_base(dc, temporary / 'native')
            model = example / 'inputs/source/dist/base/dc.usda'
            session, comparison, selected = roundtrip(source, model, temporary / 'roundtrip')
            evidence = publish_view(stage, session, temporary / 'roundtrip', out, selected, publication)
            shutil.copyfile(temporary / 'roundtrip/convergence.json', out / 'roundtrip/convergence.json')
            return [dict(mode='native-base', facility=publication['facility'], variant=publication['variant'],
                         counts=evidence['counts'], sourcePrims=evidence['sourcePrims'],
                         elements=comparison['elements'], driversCompared=comparison['driversCompared'],
                         driverDifferences=len(comparison['driverDifferences']),
                         bodiesCompared=len(comparison['bodies']), repeatMutations=0)]
        return run_example(example, hook, variant='base', publish=args.publish, size=(960, 600), keywords=[])


if __name__ == '__main__':
    main()
