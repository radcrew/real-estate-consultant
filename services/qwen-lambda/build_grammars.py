"""Compile exported JSON Schemas into GBNF grammars, at image build time.

Doing this during the build rather than per invocation keeps grammar compilation out of
the cold start, and makes a schema the image cannot express fail the build instead of
the first request that needs it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from llama_cpp.llama_grammar import json_schema_to_gbnf


def build(schema_dir: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    schemas = sorted(schema_dir.glob("*.json"))
    if not schemas:
        raise SystemExit(f"No schemas in {schema_dir}: the image would serve no route.")

    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        gbnf = json_schema_to_gbnf(json.dumps(schema))
        target = out_dir / f"{path.stem}.gbnf"
        target.write_text(gbnf, encoding="utf-8")
        print(f"{path.name} -> {target.name}")
    return len(schemas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schemas", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    count = build(args.schemas, args.out)
    print(f"Compiled {count} grammar(s).")


if __name__ == "__main__":
    main()
