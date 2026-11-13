"""Command line entry: python -m extract.cli --config C --pages D --out O"""

import argparse
import json
from pathlib import Path

from .config import load_config
from .dom import parse
from .extractors import extract_fields, find_source_url
from .record import build_record


def run(config_path, pages_dir, out_path):
    config = load_config(config_path)
    pages = sorted(Path(pages_dir).glob("*.html"), key=lambda p: p.name)
    records = []
    missing_total = 0
    for path in pages:
        root = parse(path.read_text(encoding="utf-8"))
        source_url = find_source_url(root, path)
        page_type, values, missing = extract_fields(config, root, source_url)
        records.append(build_record(source_url, page_type, values, missing))
        missing_total += len(missing)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {
        "pages": len(pages),
        "records": len(records),
        "missing_fields": missing_total,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="extract.cli",
        description="Config-driven product field extractor (stdlib only).")
    parser.add_argument("--config", required=True, help="JSON config path")
    parser.add_argument("--pages", required=True, help="directory of HTML pages")
    parser.add_argument("--out", required=True, help="output JSONL path")
    args = parser.parse_args(argv)
    stats = run(args.config, args.pages, args.out)
    print("pages={pages} records={records} missing_fields={missing_fields}".format(
        **stats))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
