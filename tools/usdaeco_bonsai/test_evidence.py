"""Reuse measured tests only when their source and dependency bytes still match."""
import hashlib
import json
import os
from pathlib import Path


def fingerprint(root):
    roots = [('integration', Path(root)/'tools'), ('tests', Path(root)/'testenv'), ('blender', Path(root)/'blender')]
    for variable in ('AECO_CORE_ROOT','AECO_AXIS_ROOT','AECO_SYNC_ROOT','AECO_IFC_ROOT','AECO_CCTV_ROOT','TOOLCHAIN_DIR'):
        if os.environ.get(variable):
            roots.append((variable,Path(os.environ[variable])))
    digest=hashlib.sha256()
    for label,base in roots:
        for path in sorted(base.rglob('*')):
            if path.suffix not in ('.py','.json','.usda','.toml') or not path.is_file():continue
            relative=path.relative_to(base)
            if any(p.startswith('.') or p in ('out','build','dist','__pycache__') for p in relative.parts):continue
            digest.update((label+'/'+relative.as_posix()).encode());digest.update(path.read_bytes())
    digest.update((Path(root)/'bootstrap.py').read_bytes())
    digest.update((Path(root)/'pyproject.toml').read_bytes())
    return digest.hexdigest()


def save(root, summary):
    root=Path(root)
    report=root/'out/native-report.json'
    data={'source_sha256':fingerprint(root),'native_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),
          'pytest':summary}
    (root/'out/test-evidence.json').write_text(json.dumps(data,indent=2)+'\n')


def load(root):
    root=Path(root);data=json.loads((root/'out/test-evidence.json').read_text())
    if data['source_sha256']!=fingerprint(root):raise ValueError('Test sources or dependencies changed; run fresh tests')
    if data['native_sha256']!=hashlib.sha256((root/'out/native-report.json').read_bytes()).hexdigest():
        raise ValueError('Native evidence changed; run fresh tests')
    return data['pytest']
