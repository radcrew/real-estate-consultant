"""Generate programmatically-labelled intake training examples.

    cd backend
    python -m ml.data.generate --count 2000 --out ml/data/train.jsonl

Labels are correct by construction: a target criteria dict is chosen first, then rendered
into natural language, and the dict is kept as gold. Nothing is inferred from model output,
so there is no teacher to be wrong.

**What this set has to teach is precision, not recall.** The P2 baseline
(``ml/eval/results.md``) put the stock 0.5B at precision 0.15 with recall 1.0: it returns
every schema property on every turn, nulls included, and lists the same key in ``extracted``
and ``skipped_fields`` at once. So the generator is built around negative space —

- most examples state one or two fields and their gold names one or two, absent not null;
- a fixed share have gold ``extracted == {}`` (empty input, greetings, off-topic, pure
  skips), because "say nothing" is the behaviour most missing from the stock model;
- no example ever lists a key in both ``extracted`` and ``skipped_fields``.

Prompts are built by ``build_intake_messages``, the same function production calls, so the
training text cannot drift from what the model will see at serving time.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from app.llm.intake.service import build_intake_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput

ML_DIR = Path(__file__).resolve().parents[1]
DEFAULT_QUESTIONS = ML_DIR / "eval" / "questions.json"
DEFAULT_EVAL_SET = ML_DIR / "eval" / "dataset.jsonl"

# Drawn from backend/dataset/raw-data.json so the distribution matches real listings.
CITIES = [
    ("Austin", "TX"), ("Dallas", "TX"), ("Houston", "TX"), ("Denver", "CO"),
    ("Phoenix", "AZ"), ("Miami", "FL"), ("Seattle", "WA"), ("Chicago", "IL"),
    ("Atlanta", "GA"), ("Portland", "OR"), ("Nashville", "TN"), ("Charlotte", "NC"),
    ("Wailuku", "HI"), ("Boise", "ID"), ("Reno", "NV"), ("Tampa", "FL"),
]
PROPERTY_TYPES = ["Office", "Retail", "Industrial", "Warehouse", "Flex", "Land"]

# (template, whether the phrasing names the state). Gold must contain exactly what the
# message states: labelling "Tampa area please" as "Tampa, FL" would teach the model to
# invent a state, which is the over-emission P2 found.
LOCATION_TEMPLATES = [
    ("I'm looking in {city}, {state}", True),
    ("we need something in {city}, {state}", True),
    ("{city}, {state}", True),
    ("somewhere around {city}", False),
    ("{city} area please", False),
    ("looking at {city}", False),
]
TYPE_TEMPLATES = [
    "we need {types} space", "{types} please", "looking for {types}",
    "something {types}", "{types} would work",
]
LISTING_TEMPLATES = {
    "Sale": ["we want to buy", "looking to purchase", "buying, not leasing", "for sale"],
    "Lease": ["we want to lease", "looking to rent", "leasing", "for lease"],
}
SKIP_PHRASES = [
    "skip", "pass", "no preference", "doesn't matter", "let's move on", "next question",
    "I don't care", "not important", "skip that one", "I'd rather not say",
    "move on please", "no strong feelings there", "whatever works", "not fussed",
]
NOISE_INPUTS = [
    "", "   ", "hi", "hello there", "hey", "what can you help me with?",
    "how does this work?", "asdkjfh", "???", "thanks", "ok", "sounds good",
    "got it", "cool", "sure", "yes", "that's everything", "nothing else",
]


def _fmt_money(value: int) -> str:
    if value >= 1_000_000 and value % 100_000 == 0:
        millions = value / 1_000_000
        text = f"{millions:g}M"
        return random.choice([f"${text}", f"{text}", f"${millions:g} million"])
    if value >= 1000 and value % 1000 == 0:
        return random.choice([f"${value:,}", f"${value // 1000}k"])
    return f"${value:,}"


def _fmt_sqft(value: int) -> str:
    if value >= 1000 and value % 1000 == 0:
        return random.choice([f"{value:,} sqft", f"{value // 1000}k sqft",
                              f"{value:,} square feet"])
    return f"{value:,} sqft"


def _price_value() -> int:
    return random.choice([
        random.randrange(200_000, 5_000_000, 100_000),
        random.randrange(20_000, 200_000, 5_000),
    ])


def _sqft_value() -> int:
    return random.randrange(1_000, 60_000, 500)


def _range_phrase(fmt, low_word: str, high_word: str) -> tuple[dict[str, int], str]:
    """Return (gold bounds, phrasing). Bare figures are upper bounds by convention."""
    style = random.choice(["max", "max", "min", "between"])
    if style == "max":
        value = fmt[1]()
        return {"max": value}, random.choice([
            f"up to {fmt[0](value)}", f"no more than {fmt[0](value)}",
            f"under {fmt[0](value)}", f"{fmt[0](value)} {high_word}",
        ])
    if style == "min":
        value = fmt[1]()
        return {"min": value}, random.choice([
            f"at least {fmt[0](value)}", f"{fmt[0](value)} {low_word}",
            f"minimum {fmt[0](value)}",
        ])
    low = fmt[1]()
    high = low + fmt[1]()
    return {"min": low, "max": high}, f"between {fmt[0](low)} and {fmt[0](high)}"


PRICE_FMT = (_fmt_money, _price_value)
SQFT_FMT = (_fmt_sqft, _sqft_value)


def _field_fragment(key: str) -> tuple[Any, str]:
    """Return (gold value, natural-language fragment) for one field."""
    if key == "location":
        city, state = random.choice(CITIES)
        template, names_state = random.choice(LOCATION_TEMPLATES)
        gold = f"{city}, {state}" if names_state else city
        return gold, template.format(city=city, state=state)
    if key == "property_type":
        picked = random.sample(PROPERTY_TYPES, random.choice([1, 1, 1, 2]))
        words = " or ".join(t.lower() for t in picked)
        return picked, random.choice(TYPE_TEMPLATES).format(types=words)
    if key == "listing_type":
        choice = random.choice(["Sale", "Lease"])
        return choice, random.choice(LISTING_TEMPLATES[choice])
    if key == "price":
        bounds, phrase = _range_phrase(PRICE_FMT, "or more", "or less")
        return bounds, random.choice([f"budget {phrase}", phrase, f"we can spend {phrase}"])
    if key == "size_sqft":
        bounds, phrase = _range_phrase(SQFT_FMT, "or more", "or less")
        return bounds, phrase
    if key == "loading_docks":
        count = random.randint(1, 8)
        return count, random.choice([f"{count} loading docks", f"we need {count} docks"])
    raise ValueError(f"no generator for {key}")


def _next_question_key(
    answered: set[str], skipped: set[str], ordered_required: list[str]
) -> str | None:
    return next((k for k in ordered_required if k not in answered and k not in skipped), None)


def make_example(
    *,
    question_keys: list[str],
    required: list[str],
    ordered_required: list[str],
) -> dict[str, Any]:
    """One training example. Shape is chosen first, so sparsity is controlled, not incidental."""
    # Weighted so nearly half of the set teaches restraint rather than extraction.
    shape = random.choices(
        ["single", "multi", "skip", "noise", "carried-skip", "complete"],
        weights=[30, 22, 20, 14, 8, 6],
    )[0]

    prior: dict[str, Any] = {}
    skipped: list[str] = []
    # Some turns start mid-conversation, so the model must learn not to re-extract what
    # is already in current_criteria.
    if random.random() < 0.45:
        for key in random.sample(required, random.randint(1, max(1, len(required) - 2))):
            prior[key], _ = _field_fragment(key)

    remaining = [k for k in question_keys if k not in prior]
    if not remaining:
        remaining = [random.choice(question_keys)]

    extracted: dict[str, Any] = {}
    fragments: list[str] = []

    if shape == "noise":
        user_input = random.choice(NOISE_INPUTS)
    elif shape == "skip":
        target = _next_question_key(set(prior), set(), ordered_required)
        if target is None:
            target = random.choice(required)
        skipped = [target]
        user_input = random.choice(SKIP_PHRASES)
    elif shape == "carried-skip":
        carried = random.sample(required, random.randint(1, 2))
        skipped = list(carried)
        prior = {k: v for k, v in prior.items() if k not in carried}
        available = [k for k in remaining if k not in carried]
        if available:
            key = random.choice(available)
            extracted[key], fragment = _field_fragment(key)
            fragments.append(fragment)
        user_input = ", ".join(fragments)
    elif shape == "complete":
        for key in required:
            if key not in prior:
                prior[key], _ = _field_fragment(key)
        user_input = random.choice(["that's everything", "yes that's correct",
                                    "sounds good", "looks right"])
    else:
        count = 1 if shape == "single" else random.randint(2, min(4, len(remaining)))
        for key in random.sample(remaining, count):
            extracted[key], fragment = _field_fragment(key)
            fragments.append(fragment)
        user_input = ", ".join(fragments)

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
            "next_question": {"text": None} if next_key is None else {"text": _ask(next_key)},
        },
        "next_question_key": next_key,
    }


_QUESTION_TEXT = {
    "location": "Which city or area are you looking in?",
    "property_type": "What kind of space do you need?",
    "listing_type": "Are you looking to buy or lease?",
    "price": "What budget range are you working with?",
    "size_sqft": "How much space do you need?",
    "loading_docks": "How many loading docks do you need?",
}


def _ask(key: str) -> str:
    return _QUESTION_TEXT.get(key, "What else should I know?")


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
    except Exception as exc:  # noqa: BLE001 - reported, not raised
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


def eval_input_keys(path: Path) -> set[str]:
    """Inputs from the eval set, so training never contains a turn we score on."""
    if not path.exists():
        return set()
    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            keys.add((row["user_input"], json.dumps(row["current_criteria"], sort_keys=True)))
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=2000)
    parser.add_argument("--questions", default=str(DEFAULT_QUESTIONS))
    parser.add_argument("--eval-set", default=str(DEFAULT_EVAL_SET))
    parser.add_argument("--out", default=str(ML_DIR / "data" / "train.jsonl"))
    parser.add_argument("--val-out", default=str(ML_DIR / "data" / "val.jsonl"))
    parser.add_argument("--val-fraction", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()

    random.seed(args.seed)
    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    question_keys = [q["key"] for q in questions]
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
        )
        reason = validate(example, set(question_keys), set(required))
        if reason:
            rejected[reason.split(":")[0]] += 1
            continue
        identity = (
            example["user_input"],
            json.dumps(example["current_criteria"], sort_keys=True),
        )
        if identity in held_out:
            rejected["collides with eval set"] += 1
            continue
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
