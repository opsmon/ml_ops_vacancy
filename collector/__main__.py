import argparse
import json
from pathlib import Path

from collector.demo import demo_dataset
from collector.models import Dataset
from collector.pipeline import run_real, write_export


def main():
    parser = argparse.ArgumentParser(prog="python -m collector")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Generate a separate fictional demo export")
    demo.add_argument("--output", default="web/public/data/demo.json")
    collect = commands.add_parser("collect", help="Authenticated real collection; no demo fallback")
    collect.add_argument(
        "--public", action="store_true", help="Requires documented hh.ru redistribution permission"
    )
    collect.add_argument("--state", default="state/real")
    collect.add_argument("--output", default="exports/market.json")
    collect.add_argument("--days", type=int, default=30, choices=range(1, 91), metavar="1..90")
    validate = commands.add_parser("validate")
    validate.add_argument("path")
    commands.add_parser("schemas")
    args = parser.parse_args()
    if args.command == "demo":
        write_export(demo_dataset(), args.output)
    elif args.command == "collect":
        return run_real(args.state, args.output, args.days, args.public)
    elif args.command == "validate":
        dataset = Dataset.model_validate_json(Path(args.path).read_text())
        import jsonschema

        jsonschema.validate(dataset.model_dump(), json.loads(Path("schemas/export-v1.json").read_text()))
        print(f"Validated {dataset.mode} export: {len(dataset.vacancies)} vacancies")
    elif args.command == "schemas":
        Path("schemas/export-v1.json").write_text(json.dumps(Dataset.model_json_schema(), indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
