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

from pydantic import ValidationError

from app.llm.intake.service import build_intake_messages
from app.schemas.llm_intake_parse import LlmParseModelOutput
from ml.paths import EVAL_DATASET_PATH, PHRASINGS_PATH, QUESTIONS_PATH, TRAIN_PATH, VAL_PATH

# Drawn from backend/dataset/raw-data.json so the distribution matches real listings.
CITIES = [
    ("Austin", "TX"), ("Dallas", "TX"), ("Houston", "TX"), ("Denver", "CO"),
    ("Phoenix", "AZ"), ("Miami", "FL"), ("Seattle", "WA"), ("Chicago", "IL"),
    ("Atlanta", "GA"), ("Portland", "OR"), ("Nashville", "TN"), ("Charlotte", "NC"),
    ("Wailuku", "HI"), ("Boise", "ID"), ("Reno", "NV"), ("Tampa", "FL"),
]

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
# A refusal and a piece of noise both produce empty ``extracted``; the only signal
# separating them is phrasing. The first pass used 14 refusal strings and the model
# learned the strings, not the concept - it answered four of ten eval refusals by
# re-asking the very field being refused. Breadth here is the fix, so these are
# deliberately long and varied in register.
SKIP_PHRASES = [
    "skip", "skip it", "skip this", "skip that one", "skip this one", "just skip it",
    "pass", "pass on that", "I'll pass", "next", "next question", "next one please",
    "move on", "let's move on", "move on please", "can we move on", "moving on",
    "no preference", "no strong preference", "no strong feelings there", "no opinion",
    "doesn't matter", "does not matter", "doesn't really matter", "it doesn't matter to me",
    "I don't care", "don't care", "I really don't mind", "I don't mind", "not fussed",
    "not important", "that's not important", "not important right now", "unimportant",
    "whatever works", "anything works", "any is fine", "either is fine", "open to anything",
    "I'd rather not say", "prefer not to answer", "rather not answer that",
    "I don't want to answer that", "not answering that", "leave that one",
    "leave it blank", "leave that empty", "no answer", "n/a", "not applicable",
    "flexible on that", "we're flexible there", "we're open on that", "undecided",
    "haven't decided", "not sure yet", "no idea yet", "TBD", "come back to that",
    "ask me later", "later", "I'll figure that out later", "no requirement there",
]
NOISE_INPUTS = [
    "", "   ", "\n", "hi", "hello there", "hey", "hey there", "good morning",
    "what can you help me with?", "how does this work?", "what do you need from me?",
    "who are you?", "are you a bot?", "can you explain?", "what happens next?",
    "asdkjfh", "???", "...", "test", "aaa", "qwerty",
    "thanks", "thank you", "ok", "okay", "alright", "sounds good", "got it",
    "cool", "nice", "sure", "yes", "yep", "yeah", "no worries", "perfect",
    "that's everything", "nothing else", "that's all", "done", "all set",
]

# Confirmations that add no new criteria. Deliberately longer than the four this used to
# hold: ``eval_input_keys`` now excludes any wording the eval scores on, and three of the
# original four were eval turns, which would have collapsed this shape to one string.
COMPLETE_PHRASES = [
    "that's everything", "yes that's correct", "sounds good", "looks right",
    "that covers it", "that's the lot", "correct, that's all of it",
    "yep, we're good", "no changes needed", "confirmed", "that all looks right",
]

# Labels a user would plausibly use when naming a field they want to skip. Keyed by the
# questionnaire's required fields; ``_skip_label`` falls back for any key added later.
FIELD_LABELS = {
    "location": ["location", "city", "area"],
    "property_type": ["property type", "space type", "building type"],
    "price": ["budget", "price", "price range"],
    "size_sqft": ["size", "square footage", "size question"],
}


def _skip_label(key: str) -> str:
    """A phrase for naming ``key`` in a refusal.

    A new required question would otherwise raise KeyError mid-generation. The fallback is
    poorer training text than a hand-written label, so add one here when that happens —
    but a plain de-underscored key is a real thing a user would type, and generating is
    better than crashing.
    """
    return random.choice(FIELD_LABELS.get(key) or [key.replace("_", " ")])


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


# The model has to read DIRECTION off the wording, so both sides need comparable breadth.
# v2 had 4 upper phrasings against 3 lower, and a 2:1 style weighting on top, producing
# 445 upper-bound examples against 199 lower. It generalised unseen *upper* wordings fine
# ("less than", "lower than") because the prior agreed, and inverted unseen *lower* ones:
# "higher than $500K" came back as {"max": 500000}.
MAX_PHRASES = [
    "up to {v}", "no more than {v}", "under {v}", "less than {v}", "lower than {v}",
    "below {v}", "at most {v}", "not over {v}", "{v} or less", "{v} max", "maximum {v}",
]
MIN_PHRASES = [
    "at least {v}", "no less than {v}", "more than {v}", "higher than {v}", "over {v}",
    "above {v}", "starting at {v}", "north of {v}", "{v} or more", "{v} and up",
    "minimum {v}",
]
BETWEEN_PHRASES = [
    "between {lo} and {hi}", "from {lo} to {hi}", "{lo} to {hi}",
    "more than {lo} but under {hi}", "at least {lo} and no more than {hi}",
]


def _range_phrase(fmt) -> tuple[dict[str, int], str]:
    """Return (gold bounds, phrasing).

    Weights are set on the **gold** distribution, not the style names: ``bare`` also
    yields a ``max`` bound, so explicit ``max`` is damped to compensate. The result is
    roughly 40% max-only, 40% min-only, 20% two-sided — parity is the point, because the
    imbalance is what let a learned prior override an explicit comparator.
    """
    style = random.choices(["max", "min", "between", "bare"], weights=[25, 40, 20, 15])[0]
    if style == "max":
        value = fmt[1]()
        return {"max": value}, random.choice(MAX_PHRASES).format(v=fmt[0](value))
    if style == "min":
        value = fmt[1]()
        return {"min": value}, random.choice(MIN_PHRASES).format(v=fmt[0](value))
    if style == "bare":
        # A figure with no comparator is an upper bound. The eval has always tested this
        # ("half a million"), but v2 never generated it — every phrasing carried a
        # comparator word, so the convention was scored and never taught.
        value = fmt[1]()
        return {"max": value}, fmt[0](value)
    low = fmt[1]()
    high = low + fmt[1]()
    return {"min": low, "max": high}, random.choice(BETWEEN_PHRASES).format(
        lo=fmt[0](low), hi=fmt[0](high)
    )


PRICE_FMT = (_fmt_money, _price_value)
SQFT_FMT = (_fmt_sqft, _sqft_value)


def load_phrasings(path: Path) -> dict[str, list[str]]:
    """Wordings a client uses for each option, from ``ml.data.make_phrasings``.

    Every property_type example used to render the option word itself, so the most
    reinforced rule in the set was *copy the noun you see* — and the tuned model echoed
    "warehouse" back instead of answering "industrial". These phrasings put a different
    word in the message from the one in the gold label, which is the only way the set can
    teach anything other than copying.

    Absent is not fatal: examples fall back to the literal option, which is the old
    behaviour.
    """
    if not path.exists():
        print(f"no phrasings at {path}; run ml.data.make_phrasings to teach generalisation")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def property_type_values(questions: list[dict[str, Any]]) -> list[str]:
    """The property types this questionnaire actually offers.

    Read from ``questions.json`` rather than hardcoded. The hardcoded list held six
    title-case types including "Warehouse" — which no listing carries and the
    questionnaire has never offered — so every generated example naming it taught a
    value the model could not legally emit.
    """
    for row in questions:
        if row.get("key") != "property_type":
            continue
        options = row.get("options")
        if not isinstance(options, list):
            break
        return [
            value
            for option in options
            if isinstance(
                value := (option.get("value") if isinstance(option, dict) else option), str
            )
            and value.strip()
        ]
    raise SystemExit("questions.json has no property_type options; run ml.eval.dump_questions")


def _field_fragment(
    key: str, property_types: list[str], phrasings: dict[str, list[str]]
) -> tuple[Any, str]:
    """Return (gold value, natural-language fragment) for one field."""
    if key == "location":
        city, state = random.choice(CITIES)
        template, names_state = random.choice(LOCATION_TEMPLATES)
        gold = f"{city}, {state}" if names_state else city
        return gold, template.format(city=city, state=state)
    if key == "property_type":
        picked = random.sample(property_types, random.choice([1, 1, 1, 2]))
        words = []
        for option in picked:
            pool = phrasings.get(option, [])
            # Half literal. All-phrasing would teach the mirror-image mistake: the model
            # would stop recognising the option words themselves.
            words.append(random.choice(pool) if pool and random.random() < 0.5 else option)
        return picked, random.choice(TYPE_TEMPLATES).format(types=" or ".join(words))
    if key == "price":
        bounds, phrase = _range_phrase(PRICE_FMT)
        return bounds, random.choice([f"budget {phrase}", phrase, f"we can spend {phrase}"])
    if key == "size_sqft":
        bounds, phrase = _range_phrase(SQFT_FMT)
        return bounds, phrase
    # Reached when the questionnaire gains a key this generator has no renderer for.
    # Raising is deliberate: silently skipping would ship a set that never teaches the
    # new field, and the shortfall would look like ordinary deduplication loss.
    raise ValueError(f"no generator for {key}; add one before regenerating")


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
        ["single", "multi", "skip", "noise", "carried-skip", "complete", "answer-and-skip"],
        weights=[22, 18, 28, 14, 7, 4, 7],
    )[0]

    prior: dict[str, Any] = {}
    skipped: list[str] = []
    # Some turns start mid-conversation, so the model must learn not to re-extract what
    # is already in current_criteria.
    if random.random() < 0.45:
        for key in random.sample(required, random.randint(1, max(1, len(required) - 2))):
            prior[key], _ = _field_fragment(key, property_types, phrasings)

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
    else:
        count = 1 if shape == "single" else random.randint(2, min(4, len(remaining)))
        for key in random.sample(remaining, count):
            extracted[key], fragment = _field_fragment(key, property_types, phrasings)
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
    return {
        json.loads(line)["user_input"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


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
        if example["user_input"] in held_out:
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
