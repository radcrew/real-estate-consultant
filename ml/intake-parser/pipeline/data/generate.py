"""Assemble labelled intake training examples, and write the dataset.

    cd ml/intake-parser
    python -m pipeline.data.generate --count 2000 --out datasets/train.jsonl

Labels are correct by construction: a target criteria dict is chosen first, then rendered
into natural language, and the dict is kept as gold. Nothing is inferred from model output,
so there is no teacher to be wrong.

**What this set has to teach is precision, not recall.** The P2 baseline
(``results/results.md``) put the stock 0.5B at precision 0.15 with recall 1.0: it returns
every schema property on every turn, nulls included, and lists the same key in ``extracted``
and ``skipped_fields`` at once. So the generator is built around negative space --

- most examples state one or two fields and their gold names one or two, absent not null;
- a fixed share have gold ``extracted == {}`` (empty input, greetings, off-topic, pure
  skips), because "say nothing" is the behaviour most missing from the stock model;
- no example ever lists a key in both ``extracted`` and ``skipped_fields``.

Prompts are built by ``build_intake_messages``, the same function production calls, so the
training text cannot drift from what the model will see at serving time.

This module decides *what* an example says. Four others decide how it is worded, and the
dependency runs one way through them:

    vocabulary  the corpora, data only
    figures     how a number is sampled and written -- money against area
    fields      gold and wording for one field, always as a pair
    messages    fragments woven into a sentence, then roughed up

``make_example`` composes those into one labelled turn; ``validate`` refuses the ones that
would teach something wrong; ``main`` writes the split and stamps it.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.llm.intake.service import build_intake_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput
from pipeline.data.fields import (
    _bare_answer,
    _field_fragment,
    _field_piece,
    _skip_label,
    load_phrasings,
    property_type_values,
)
from pipeline.data.messages import _add_distractors, _connected_sentence, _rough_up
from pipeline.data.vocabulary import COMPLETE_PHRASES, DISTRACTORS, NOISE_INPUTS, SKIP_PHRASES
from pipeline.paths import (
    EVAL_DATASET_PATH,
    PHRASINGS_PATH,
    QUESTIONS_PATH,
    TRAIN_PATH,
    VAL_PATH,
)
from pipeline.provenance import write_dataset_stamp


def _next_question_key(
    answered: set[str], skipped: set[str], ordered_required: list[str]
) -> str | None:
    return next((k for k in ordered_required if k not in answered and k not in skipped), None)


def make_example(
    *,
    question_keys: list[str],
    required: list[str],
    ordered_required: list[str],
    property_types: list[str],
    phrasings: dict[str, list[str]],
) -> dict[str, Any]:
    """One training example. Shape is chosen first, so sparsity is controlled, not incidental."""
    # Weighted so over half the set teaches restraint rather than extraction. `skip` is
    # over-weighted against its target share because refusal phrasings collapse under
    # deduplication far harder than extraction phrasings do.
    shape = random.choices(
        ["single", "multi", "skip", "noise", "carried-skip", "complete",
         "answer-and-skip", "correction", "pending-answer"],
        # `multi` is held at 20 because ~70% of its examples state 3+ fields, and that
        # share is the location-drop fix -- adding shapes below it once pushed 3+ down to
        # 11%, back to the v3 level the fix exists to move. `skip` stays over-weighted
        # against its target share because refusal phrasings collapse under dedup far
        # harder than extraction phrasings do.
        weights=[16, 20, 23, 9, 5, 4, 6, 9, 8],
    )[0]

    prior: dict[str, Any] = {}
    skipped: list[str] = []
    # Some turns start mid-conversation, so the model must learn not to re-extract what
    # is already in current_criteria.
    #
    # Never for `multi`: a pre-filled prior shrinks `remaining`, which caps how many
    # fields the message can state. That is why v3 saw so few 3- and 4-field examples --
    # 10.8% of the set -- and learned to stop at two.
    #
    # `correction` fills its own prior below, because it needs a field that is already
    # answered -- the opposite of what `remaining` selects for.
    if shape not in ("multi", "correction", "pending-answer") and random.random() < 0.45:
        for key in random.sample(required, random.randint(1, max(1, len(required) - 2))):
            prior[key], _ = _field_fragment(key, property_types, phrasings)

    remaining = [k for k in question_keys if k not in prior]
    if not remaining:
        remaining = [random.choice(question_keys)]

    extracted: dict[str, Any] = {}
    fragments: list[str] = []

    if shape == "pending-answer":
        # Answer the outstanding question with a value and nothing else. Every other
        # required field is filled, so `pending_question` in the prompt names exactly the
        # one this message answers -- which is the only thing that disambiguates it.
        #
        # "10" is price after the budget question and size_sqft after the size question.
        # Identical message, different field, and the message itself cannot say which:
        # that is why the prompt carries pending_question and why this shape exists.
        target = random.choice(required)
        for key in required:
            if key != target:
                prior[key], _ = _field_fragment(key, property_types, phrasings)
        extracted[target], user_input = _bare_answer(target, property_types, phrasings)
    elif shape == "correction":
        # A field that is ALREADY answered, restated. Every other shape draws from
        # `remaining`, so v3 never saw gold overlap current_criteria and learned that an
        # answered field is closed. In production a user correcting a stored value got
        # their old value echoed back unchanged, turn after turn.
        #
        # Half carry an explicit marker ("actually", "make it") and half are a bare
        # restatement, because the bare form is what failed: "100sqft" after a wrong size
        # is a correction whether or not the user says so.
        for key in random.sample(required, random.randint(1, max(1, len(required) - 1))):
            prior[key], _ = _field_fragment(key, property_types, phrasings)
        target = random.choice(list(prior))
        extracted[target], fragment = _field_fragment(target, property_types, phrasings)
        if random.random() < 0.5:
            marker = random.choice([
                "actually", "actually, make it", "sorry, make that", "no,", "scratch that,",
                "change that to", "let's say", "on second thought,", "correction:",
                "I meant", "no I meant", "update that to",
            ])
            user_input = f"{marker} {fragment}"
        else:
            user_input = fragment
    elif shape == "noise":
        # A requirement the questionnaire does not cover, stated *alone*. DISTRACTORS only
        # ever arrived appended to a message that answered something (see the `if
        # extracted` guard below), so a message that is nothing but an unmapped clause was
        # never taught -- and "3 floors" on its own came back as property_type
        # multifamily, the type it most often sat beside. Gold is empty here for exactly
        # the reason it ignores the appended form, and `prior` is carried, so the example
        # also teaches that a clause with no field disturbs no answered one.
        if random.random() < 0.3:
            user_input = ", ".join(random.sample(DISTRACTORS, random.choice([1, 1, 2])))
        else:
            user_input = random.choice(NOISE_INPUTS)
    elif shape == "skip":
        target = _next_question_key(set(prior), set(), ordered_required)
        if target is None:
            target = random.choice(required)
        skipped = [target]
        user_input = random.choice(SKIP_PHRASES)
    elif shape == "answer-and-skip":
        # One message that answers one field and refuses another. The first pass had no
        # example of this, and the eval turn that needs it failed: every skip example
        # had empty `extracted`, so answering and skipping looked mutually exclusive.
        answerable = [k for k in remaining if k in required] or remaining
        answer_key = random.choice(answerable)
        extracted[answer_key], fragment = _field_fragment(answer_key, property_types, phrasings)
        candidates = [
            k for k in required if k not in prior and k != answer_key
        ]
        if candidates:
            skip_key = random.choice(candidates)
            skipped = [skip_key]
            label = _skip_label(skip_key)
            refusal = random.choice([
                f"but skip the {label}", f"but let's skip {label}",
                f"no preference on {label} though", f"{label} doesn't matter",
                f"and I'd rather not answer the {label} question",
                f"leave {label} blank", f"flexible on {label}",
            ])
            user_input = f"{fragment}, {refusal}"
        else:
            user_input = fragment
    elif shape == "carried-skip":
        carried = random.sample(required, random.randint(1, 2))
        skipped = list(carried)
        prior = {k: v for k, v in prior.items() if k not in carried}
        available = [k for k in remaining if k not in carried]
        if available:
            key = random.choice(available)
            extracted[key], fragment = _field_fragment(key, property_types, phrasings)
            fragments.append(fragment)
        user_input = ", ".join(fragments)
    elif shape == "complete":
        for key in required:
            if key not in prior:
                prior[key], _ = _field_fragment(key, property_types, phrasings)
        user_input = random.choice(COMPLETE_PHRASES)
    elif shape == "single":
        key = random.choice(remaining)
        extracted[key], fragment = _field_fragment(key, property_types, phrasings)
        user_input = fragment
    else:
        # Skewed high on purpose. A flat randint(2, 4) still leaves 3- and 4-field
        # messages rarer than 2-field ones once the other shapes are counted, and
        # under-representing them is what taught v3 to stop after two keys.
        count = min(len(remaining), random.choices([2, 3, 4], weights=[30, 40, 30])[0])
        keys = random.sample(remaining, count)
        # Most qualifying messages are woven into one sentence; the rest stay comma-joined
        # clauses. Weighted toward weaving because that is the shape v3 failed on, but not
        # all of it -- an all-sentence set would just move the blind spot, and the
        # comma-joined form is still ~14% of the set through the other shapes.
        pieces = {}
        for key in keys:
            extracted[key], pieces[key] = _field_piece(key, property_types, phrasings)
        sentence = _connected_sentence(pieces) if random.random() < 0.6 else None
        if sentence is not None:
            user_input = sentence
        else:
            # Re-render as standalone clauses; gold is re-taken because the wording, and
            # therefore what the message actually states, differs between the two forms.
            extracted = {}
            for key in keys:
                extracted[key], fragment = _field_fragment(key, property_types, phrasings)
                fragments.append(fragment)
            user_input = ", ".join(fragments)

    # Applied once, here, so every shape gets them rather than only the ones edited last.
    #
    # `noise` is exempt from distractors: its whole job is bare greetings and typos, and
    # appending a requirement to "hi" would turn a say-nothing example into a say-something
    # one. That exemption is already implied by `if extracted` -- noise always golds {} --
    # but it is stated because the reason is not obvious from the condition.
    #
    # It is NOT exempt from `_rough_up`, and used to be. A `shape != "noise"` guard wrapped
    # both, so noise was the one shape never sentence-cased, upper-cased or given a
    # trailing "!" -- measured at 0% against 22-44% for every other shape. `skip` and
    # `complete` also gold nothing and *were* roughened, so the set taught a surface cue
    # that separates noise from a refusal: a capitalised message was never noise. Teaching
    # the model to read casing instead of content is the exact failure `_rough_up` exists
    # to prevent.
    if extracted and random.random() < 0.22:
        user_input = _add_distractors(user_input)
    user_input = _rough_up(user_input)

    current_criteria = dict(prior)
    if skipped and shape == "carried-skip":
        current_criteria["_skipped_fields"] = list(skipped)

    answered = set(prior) | set(extracted)
    next_key = _next_question_key(answered, set(skipped), ordered_required)

    return {
        "shape": shape,
        "user_input": user_input,
        "current_criteria": current_criteria,
        "target": {
            "extracted": extracted,
            "skipped_fields": sorted(skipped),
        },
        "next_question_key": next_key,
    }



def validate(example: dict[str, Any], question_keys: set[str], required: set[str]) -> str | None:
    """Return a reason the example is unusable, or None. Runs on every row before writing."""
    target = example["target"]
    extracted = target["extracted"]
    skipped = set(target["skipped_fields"])

    for key in extracted:
        if key not in question_keys:
            return f"extracted unknown key {key}"
    for key in skipped:
        if key not in required:
            return f"skipped non-required key {key}"
    # The stock model does exactly this; never show it an example that does.
    both = set(extracted) & skipped
    if both:
        return f"key in both extracted and skipped: {sorted(both)}"
    try:
        LlmParseModelOutput.model_validate(target)
    except ValidationError as exc:
        return f"fails LlmParseModelOutput: {exc}"
    return None


def to_chat_record(
    example: dict[str, Any], questions: list[dict[str, Any]]
) -> dict[str, Any]:
    """Render one example as chat messages, using the builder production calls."""
    prompt = build_intake_messages(
        user_input=example["user_input"],
        current_criteria=example["current_criteria"],
        questions=questions,
    )
    completion = json.dumps(example["target"], ensure_ascii=True, separators=(",", ":"))
    return {
        "messages": [*prompt.messages, {"role": "assistant", "content": completion}],
        "shape": example["shape"],
    }


def collision_key(text: str) -> str:
    """Fold the variation ``_rough_up`` adds, so a roughened wording still collides.

    The guard used to compare raw strings, and roughening runs *after* an example is
    built. So the eval turn "that's everything" shipped into the r6 training set four
    times over -- ``THAT'S EVERYTHING``, ``That's everything``, ``That's everything.``,
    ``That's everything!!`` -- and "yes that's correct" three times. Both are completion
    turns, where the wording is the entire signal, so the category was scoring recall on
    two of its four turns while the guard reported them held out.

    Returns ``""`` for a blank message, which both callers read as "no wording here" and
    skip. The eval's empty and whitespace turns score a behaviour rather than a phrasing
    -- emit nothing when there is nothing -- and there is nothing to memorise. Holding
    them out would leave that behaviour untaught while the eval went on scoring it.
    """
    text = text.lower().strip()
    if not text:
        return ""
    for tail in (" please", " thanks"):
        if text.endswith(tail):
            text = text[: -len(tail)]
    return text.rstrip("!. ").strip()


def eval_input_keys(path: Path) -> set[str]:
    """Wordings the eval scores on, so training never teaches one of them.

    Keyed on ``user_input`` alone, **not** the (input, criteria) pair. For skip and
    noise turns the wording *is* the whole signal, so the same phrase under different
    conversation state is still the model recognising a string it trained on. Keying on
    the pair let r2 ship with 9 of 25 skip turns reusing a ``SKIP_PHRASES`` entry, which
    made roughly a third of skip recall memorisation.

    Deduplication still keys on the pair — see ``main`` — because the same wording
    against different state is legitimate variety *within* training.
    """
    if not path.exists():
        return set()
    keys = {
        collision_key(json.loads(line)["user_input"])
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    return keys - {""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2500)
    parser.add_argument("--questions", default=str(QUESTIONS_PATH))
    parser.add_argument("--eval-set", default=str(EVAL_DATASET_PATH))
    parser.add_argument("--phrasings", default=str(PHRASINGS_PATH))
    parser.add_argument("--out", default=str(TRAIN_PATH))
    parser.add_argument("--val-out", default=str(VAL_PATH))
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    random.seed(args.seed)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    question_keys = [q["key"] for q in questions]
    property_types = property_type_values(questions)
    phrasings = load_phrasings(Path(args.phrasings))
    required = [q["key"] for q in questions if q.get("required")]
    ordered_required = [
        q["key"] for q in sorted(questions, key=lambda q: q["order_index"]) if q.get("required")
    ]

    held_out = eval_input_keys(Path(args.eval_set))
    seen: set[str] = set()
    rejected: Counter[str] = Counter()
    records: list[dict[str, Any]] = []
    shapes: Counter[str] = Counter()

    attempts = 0
    while len(records) < args.count and attempts < args.count * 60:
        attempts += 1
        example = make_example(
            question_keys=question_keys,
            required=required,
            ordered_required=ordered_required,
            property_types=property_types,
            phrasings=phrasings,
        )
        reason = validate(example, set(question_keys), set(required))
        if reason:
            rejected[reason.split(":")[0]] += 1
            continue
        if collision_key(example["user_input"]) in held_out:
            rejected["collides with eval set"] += 1
            continue
        identity = (
            example["user_input"],
            json.dumps(example["current_criteria"], sort_keys=True),
        )
        fingerprint = json.dumps([identity, example["target"]], sort_keys=True)
        if fingerprint in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(fingerprint)
        records.append(to_chat_record(example, questions))
        shapes[example["shape"]] += 1

    if len(records) < args.count:
        print(f"only produced {len(records)} of {args.count} after {attempts} attempts")

    random.shuffle(records)
    split = int(len(records) * (1 - args.val_fraction))
    train, val = records[:split], records[split:]

    # Refuse before the write, not after it. Everything below opens the output paths with
    # "w", and the defaults are the real datasets/train.jsonl and datasets/validation.jsonl
    # — so a run that produced nothing usable used to truncate the training set on its way
    # to a ZeroDivisionError in the summary, leaving an empty file and a stamp claiming 0
    # rows. An empty split is a failed generation, and a failed generation writes nothing.
    if not records:
        print(
            f"produced no records in {attempts} attempts - refusing to write.",
            file=sys.stderr,
        )
        if rejected:
            print("every attempt was rejected:", file=sys.stderr)
            for reason, count in rejected.most_common():
                print(f"  {reason:<34} {count}", file=sys.stderr)
        else:
            print(f"nothing was attempted; --count is {args.count}.", file=sys.stderr)
        return 1
    if not train or not val:
        print(
            f"a {len(train)}/{len(val)} train/validation split from {len(records)} records "
            "leaves one side empty - refusing to write.\n"
            f"raise --count or lower --val-fraction (currently {args.val_fraction}).",
            file=sys.stderr,
        )
        return 1

    for path_str, rows in ((args.out, train), (args.val_out, val)):
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=True) + "\n")
        print(f"wrote {len(rows):>5} -> {path}")

    empty = sum(
        1 for r in records
        if json.loads(r["messages"][-1]["content"])["extracted"] == {}
    )

    # Written before the summary below so the numbers on screen and the numbers on disk
    # are the same numbers. --count and --seed are the two flags that change the dataset
    # without changing a line of code, and not recording --count cost a training cycle.
    stamp = write_dataset_stamp(
        out_dir=Path(args.out).parent,
        args={
            "count": args.count,
            "seed": args.seed,
            "val_fraction": args.val_fraction,
        },
        inputs={
            "questions": Path(args.questions),
            "eval_set": Path(args.eval_set),
            "phrasings": Path(args.phrasings),
            "generator": Path(__file__),
        },
        outputs={"train": Path(args.out), "validation": Path(args.val_out)},
        counts={
            "requested": args.count,
            "produced": len(records),
            "train": len(train),
            "validation": len(val),
            "attempts": attempts,
            "empty_extracted": empty,
            "shape_mix": dict(shapes),
            "rejected": dict(rejected),
        },
    )
    if stamp:
        print(f"wrote provenance -> {stamp}")

    print("\nshape mix:")
    for name, count in shapes.most_common():
        print(f"  {name:<14} {count:>5}  {count / len(records):>6.1%}")
    print(f"\nexamples with empty extracted: {empty} ({empty / len(records):.1%})")
    print("This share is the point: the stock model's failure is over-emission.")
    if rejected:
        print("\nrejected:")
        for reason, count in rejected.most_common():
            print(f"  {reason:<34} {count}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
