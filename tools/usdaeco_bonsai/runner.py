"""Launch one isolated native transaction; the output is published by sync."""
import os
from pathlib import Path
import shutil
import subprocess

def executable():
    configured = os.environ.get("AECO_BLENDER")
    candidate = configured or str(Path(os.sep) / "Applications" / "Blender.app" / "Contents" / "MacOS" / "Blender")
    resolved = shutil.which(candidate)
    if not resolved:
        raise FileNotFoundError("Set AECO_BLENDER to Blender with Bonsai 0.8.5")
    return resolved

def run_blender(document, request, output):
    import usdaeco_ifc
    environment = {k:v for k,v in os.environ.items() if k != "PYTHONPATH"}
    environment["AECO_IFC_TOOLS"] = str(Path(usdaeco_ifc.__file__).resolve().parent.parent)
    return subprocess.run([executable(), "-b", "--python-exit-code", "1", "--python",
                           str(Path(__file__).resolve().parents[2] / "blender/operations.py"), "--",
                           str(document), str(request), str(output)],
                          capture_output=True, text=True, timeout=240, env=environment)
