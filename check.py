#!/usr/bin/env python3
"""Verify source integration and print the family N checks, M failed line."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import bootstrap
from usdaeco_check import Report
from usdaeco_check.structure import check_structure
from usdaeco_check.example import check_example
from usdaeco_bonsai.runtime import python

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-tests',action='store_true',help='reuse measured tests only if source and native evidence hashes match')
    args=parser.parse_args()
    report=Report();evidence={}
    print('== stage: integration structure',flush=True)
    for result in check_structure(ROOT):report.add(result)
    import aeco_sync
    aeco_sync.register_plugins()
    print('== stage: core validator registry',flush=True)
    from pxr import Plug, Usd, UsdValidation
    core = Path(os.environ.get('AECO_CORE_ROOT', ROOT.parent/'usdaeco-core'))
    Plug.Registry().RegisterPlugins(str(core/'usdAecoValidators'))
    import usdAecoValidators  # Required: an unavailable plugin must fail loudly.
    registry = UsdValidation.ValidationRegistry()
    metadata = registry.GetValidatorMetadataForKeyword('UsdAecoValidators')
    validators = registry.GetOrLoadValidatorsByName([item.name for item in metadata])
    if len(validators) != 8 or not all(validators):
        raise RuntimeError('All eight core validators must load through UsdValidation')
    report.check('core validators loaded',True,f'{len(validators)} registry validators')
    from aeco_sync.hosts.base import Host,discover,host_class
    from usdaeco_bonsai.host import BonsaiHost
    report.check('sync v0.5 contract',aeco_sync.__version__.startswith('0.5.'))
    entry=discover().get('bonsai')
    report.check('declared entry point',entry is not None and entry.value=='usdaeco_bonsai.host:BonsaiHost')
    report.check('discovered host implements lifecycle',host_class('bonsai') is BonsaiHost and not BonsaiHost.__abstractmethods__ and issubclass(BonsaiHost,Host))
    report.check('immutable capabilities',isinstance(BonsaiHost().capabilities(),frozenset))
    print('== stage: regression tests',flush=True)
    from usdaeco_bonsai import test_evidence
    if args.reuse_tests:
        summary=test_evidence.load(ROOT)
        test_ok=summary['passed']>=26 and summary['skipped']==0
        print(f"Reused {summary['passed']} passing tests; source and native evidence hashes match",flush=True)
    else:
        tests=python(['-m','pytest','-q','--tb=short','-rs'],cwd=ROOT,capture_output=True,text=True,timeout=900)
        print(tests.stdout)
        if tests.returncode:print(tests.stderr)
        passed=re.search(r'(\d+) passed',tests.stdout);skipped=re.search(r'(\d+) skipped',tests.stdout)
        summary={'passed':int(passed[1]) if passed else 0,'skipped':int(skipped[1]) if skipped else 0}
        test_ok=tests.returncode==0
        if test_ok:test_evidence.save(ROOT,summary)
    report.check('pytest',test_ok,'reused measured evidence' if args.reuse_tests else 'fresh execution')
    evidence['pytest']=summary
    print('== stage: native Bonsai evidence',flush=True)
    native_path=ROOT/'out/native-report.json'
    native=json.loads(native_path.read_text()) if test_ok and native_path.exists() else {'hosts':{'bonsai':[]}}
    rows=native['hosts']['bonsai']
    report.check('native case set count',len(rows)==21,f'{sum(bool(r["passed"]) for r in rows)}/{len(rows)}')
    for row in rows:
        report.check(row['id'],row['passed'] and row['repeatMutations']==0)
    report.check('data-centre case set',sum(r['id'].startswith('D-') for r in rows)==9)
    report.check('actual Bonsai camera execution',all(r.get('nativeEvidence',{}).get('blender')=='5.1.2' and r.get('nativeEvidence',{}).get('ifcopenshell')=='0.8.5' for r in rows if r.get('mutations',0)>0))
    evidence['native']=[{k:r[k] for k in ('id','passed','repeatMutations','nativeEvidence') if k in r} for r in rows]

    print('== stage: roundtrip and render',flush=True)
    run=python([str(ROOT/'examples/roundtrip/run.py')],cwd=ROOT,capture_output=True,text=True,timeout=900)
    print(run.stdout)
    if run.returncode:print(run.stderr[-4000:])
    report.check('roundtrip runner',run.returncode==0)
    report.add(check_example(ROOT/'examples/roundtrip',execute=False))
    if run.returncode==0:
        published=Usd.Stage.Open(str(ROOT/'examples/roundtrip/result/example.usdc'))
        from usdaeco_bonsai.example import verify_facility
        source_root=Path(os.environ['AECO_DATACENTRE_ROOT'])/'dist/base'
        source=Usd.Stage.Open(str(source_root/'dc.usda'))
        publication=json.loads((source_root/'dc.manifest.json').read_text())
        counts=verify_facility(source,published,publication)
        report.check('complete pinned facility retained',True,json.dumps(counts,sort_keys=True))
        evidence['facility']=json.loads((ROOT/'examples/roundtrip/out/facility.json').read_text())
        errors=list(UsdValidation.ValidationContext(validators).Validate(published))
        failures=[error for error in errors if error.GetType()==UsdValidation.ValidationErrorType.Error]
        report.check('published result core validation',not failures,
                     f'{len(validators)} validators, {len(failures)} errors, {len(errors)-len(failures)} warnings')
        evidence['coreValidation']={'validators':len(validators),'errors':len(failures),
                                    'warnings':len(errors)-len(failures)}
        final=Usd.Stage.Open(str(ROOT/'examples/roundtrip/out/roundtrip/final.usdc'))
        compared=0
        for prim in final.TraverseAll():
            for relationship in prim.GetRelationships():
                actual=published.GetRelationshipAtPath(relationship.GetPath())
                if not actual or actual.GetTargets()!=relationship.GetTargets():
                    raise AssertionError('Published relationship differs from re-import: '+str(relationship.GetPath()))
            for attribute in prim.GetAttributes():
                if not attribute.HasAuthoredValueOpinion() or attribute.GetName() in ('visibility','primvars:displayColor'):
                    continue
                actual=published.GetAttributeAtPath(attribute.GetPath())
                if not actual or actual.Get()!=attribute.Get():
                    raise AssertionError('Published value differs from re-import: '+str(attribute.GetPath()))
                compared+=1
        report.check('published values match converged re-import',compared>0,f'{compared} authored attributes')
        evidence['publishedAttributesCompared']=compared
        findings=json.loads((ROOT/'examples/roundtrip/out/findings.json').read_text())
        evidence['roundtrip']=findings
        row=findings[-1]
        report.check('wall and pipe drivers compared',row['driversCompared']==14)
        report.check('zero driver differences',row['driverDifferences']==0)
        report.check('two native bodies compared',row['bodiesCompared']==2)
        report.check('repeat apply zero mutations',row['repeatMutations']==0)
    probe="""import sys
from pxr import Usd, UsdGeom
assert Usd.SchemaRegistry.GetTypeFromSchemaTypeName('AecoPort').isUnknown
stage=Usd.Stage.Open(sys.argv[1]);assert stage and not stage.GetCompositionErrors() and stage.Flatten()
mappings=stage.GetMetadata('fallbackPrimTypes') or {}
for prim in stage.TraverseAll():
    if prim.GetTypeName().startswith('Aeco'):
        assert prim.GetTypeName() in mappings, prim.GetTypeName()
        assert prim.IsA(UsdGeom.Xform) or prim.IsA(UsdGeom.Scope), str(prim.GetPath())
"""
    clean={k:v for k,v in os.environ.items() if k not in ('PYTHONPATH','PXR_PLUGINPATH_NAME','PXR_AR_DEFAULT_SEARCH_PATH')}
    vanilla=python(['-c',probe,str(ROOT/'examples/roundtrip/out/example.usda')],env=clean,capture_output=True,text=True)
    report.check('roundtrip composes with no family plugins',vanilla.returncode==0,vanilla.stderr[-1000:] if vanilla.returncode else '')
    report.check('live Bonsai integration',len(rows)==21 and all(row['passed'] for row in rows),
                 'Local Blender/Bonsai execution; includes nine full-facility camera cases')
    evidence.update(checks=len(report.results),failed=report.failed)
    output=ROOT/'out';output.mkdir(exist_ok=True)
    (output/'check.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return report.finish()

if __name__=='__main__':raise SystemExit(main())
