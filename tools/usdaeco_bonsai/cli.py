"""Run the native Bonsai acceptance cases through sync host discovery."""
import argparse
import json
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('native-gate',))
    parser.add_argument('--output', type=Path, default=Path('out/native-gate'))
    parser.add_argument('--case', action='append', default=[])
    args = parser.parse_args(argv)
    from .gates.run import run_suite
    report = run_suite(args.output, hosts=('bonsai',), selected=args.case)
    print(json.dumps(report, indent=2))
    return 0
