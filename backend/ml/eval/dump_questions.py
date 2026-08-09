"""Write ``ml/eval/questions.json`` from the live ``questions`` table.

    cd backend
    python -m ml.eval.dump_questions

``questions.json`` was hand-authored when the harness was built and drifted from
production immediately — it described six questions where the database has had four
since 2026-04-21, and gave them plain-string options where the real rows use
``{"label": ..., "value": ...}``. Both differences were invisible for the life of the
branch: every eval row and every generated training example was built against a
questionnaire that does not exist, and the filter that validates answers against the
configured choices silently matched nothing.

Regenerating from the database removes the class of problem. The harness and the data
generator both read this file, so a questionnaire change reaches them by re-running this
rather than by someone remembering.

**Rewriting it invalidates the dataset**: gold keys, gold values and
``next_question_key`` are all keyed to the questionnaire, and so is every generated
training example. Rebuild ``dataset.jsonl`` and ``train.jsonl`` after running this, and
start a new revision in ``results.md`` — rows scored against the old questionnaire are
not comparable to rows scored against this one.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.core.supabase_sdk import close_supabase, get_supabase_sdk_client, init_supabase
from app.repositories.questions import list_intake_questions
from ml.paths import QUESTIONS_PATH


async def fetch_questions() -> list[dict]:
    await init_supabase()
    try:
        return await list_intake_questions(get_supabase_sdk_client())
    finally:
        await close_supabase()


async def main_async(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(QUESTIONS_PATH))
    args = parser.parse_args(argv)

    questions = await fetch_questions()
    out = Path(args.out)
    out.write_text(json.dumps(questions, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print(f"wrote {len(questions)} questions -> {out}\n")
    for row in questions:
        options = row.get("options")
        if isinstance(options, list):
            shown = ", ".join(str(o.get("value", o)) if isinstance(o, dict) else str(o)
                              for o in options)
        else:
            shown = json.dumps(options)
        print(f"  {row.get('order_index')}. {row.get('key'):<16} "
              f"{str(row.get('type')):<14} required={row.get('required')}  {shown}")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
