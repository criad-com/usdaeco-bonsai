"""Native acceptance through the registered host, plus transaction boundaries."""
import json
from pathlib import Path
import pytest
from aeco_sync.hosts.base import Host, host_class
from usdaeco_bonsai.host import BonsaiHost
from usdaeco_bonsai.runner import executable
from usdaeco_bonsai.gates.run import run_suite

ROOT = Path(__file__).resolve().parents[1]
CASES = [c['id'] for c in json.loads((ROOT/'tools/usdaeco_bonsai/gates/cases.json').read_text()) if 'bonsai' in c['hosts']]

def test_entry_point_contract(tmp_path, monkeypatch):
    assert host_class('bonsai') is BonsaiHost
    assert issubclass(BonsaiHost, Host)
    assert not BonsaiHost.__abstractmethods__
    assert isinstance(BonsaiHost().capabilities(), frozenset)
    from pxr import Plug, Usd
    from usdaeco_bonsai.plugins import register_plugins
    registry = Plug.Registry()
    core = registry.GetPluginWithName('usdAeco')
    assert core.metadata['aeco']['version'] == '0.9.2'
    assert registry.GetPluginWithName('usdAecoAxis').metadata['aeco']['version'] == '0.1.2'
    assert registry.GetPluginForType(Usd.SchemaRegistry.GetTypeFromSchemaTypeName('AecoAxisAPI')).name == 'usdAecoAxis'
    stage = Usd.Stage.CreateInMemory()
    prim = stage.DefinePrim('/Element', 'Xform')
    assert prim.ApplyAPI('AecoAxisAPI')
    assert prim.GetAttribute('aeco:axis:length').GetMetadata('aecoDerived') is True
    old = tmp_path / 'usdAeco'
    old.mkdir()
    metadata = dict(core.metadata['aeco'], version='0.8.4')
    (old / 'plugInfo.json').write_text(json.dumps({'Plugins': [{'Info': {'aeco': metadata}}]}))
    with pytest.raises(RuntimeError, match='requires usdAeco'):
        register_plugins(core=tmp_path)
    monkeypatch.setenv('AXIS_PLUGIN_DIR', str(tmp_path / 'missing-axis'))
    with pytest.raises(RuntimeError, match='usdAecoAxis'):
        register_plugins()


def test_missing_blender_fails_before_request(monkeypatch):
    monkeypatch.setenv('AECO_BLENDER', 'missing-blender-executable')
    with pytest.raises(FileNotFoundError, match='AECO_BLENDER'):
        executable()

@pytest.fixture(scope='module')
def native_report(tmp_path_factory):
    report = run_suite(tmp_path_factory.mktemp('bonsai'), hosts=('bonsai',))
    output = ROOT/'out/native-report.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    return report

@pytest.mark.native
@pytest.mark.parametrize('case', CASES)
def test_native_case(native_report, case):
    rows = {r['id']: r for r in native_report['hosts']['bonsai']}
    assert rows[case]['passed']
    assert rows[case]['repeatMutations'] == 0
