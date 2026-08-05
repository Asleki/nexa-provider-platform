from pathlib import Path
import argparse
from .service import DeploymentQualificationService
from .formatting import format_human, format_json

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repository-root", default=".")
    args=parser.parse_args(argv)
    result=DeploymentQualificationService().qualify(Path(args.repository_root))
    print(format_json(result) if args.json else format_human(result))
    return 0 if result.status == "PASSED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
