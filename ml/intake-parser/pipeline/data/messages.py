"""Turning field fragments into something a person would actually type.

Two jobs. ``_connected_sentence`` weaves clauses into one sentence -- v3 emitted only
comma-joined standalone clauses and consequently dropped ``location`` from every message
that named it mid-sentence, in the eval and in production. ``_rough_up`` and
``_add_distractors`` then add the surface a real message carries: stray capitals, a trailing
exclamation, a requirement the questionnaire does not ask about.

``_rough_up`` applies to **every** shape, and the reason is worth stating. It once skipped
``noise``, which left casing as a perfect signal for it -- 0% roughened against 22-44%
everywhere else -- so the model could separate a greeting from a refusal without reading a
word. Surface must carry no information here, or it becomes the thing that gets learned.
"""

from __future__ import annotations

import random

from pipeline.data.vocabulary import DISTRACTORS, SENTENCE_OPENERS, TYPE_SUFFIXES


# How a trailing bound joins on. "that costs" only fits price.
def _add_distractors(text: str) -> str:
    """Fold in one or two requirements the questionnaire does not cover.

    Gold is untouched, so the example teaches that a clause with no field is left out
    rather than forced into the nearest one.
    """
    if not text:
        return text
    # Up to three. The cap was two, and the message that prompted this states three --
    # "32ft clear height", "for lease" and "at least 20 dock doors" around one size, one
    # type and one place. A message carrying more unmapped clauses than any training
    # example is where the model starts assigning them to fields.
    extras = random.sample(DISTRACTORS, random.choices([1, 2, 3], weights=[55, 30, 15])[0])
    parts = [text, *extras]
    if random.random() < 0.4:
        random.shuffle(parts)
    return ", ".join(parts)


def _rough_up(text: str) -> str:
    """Punctuation and casing a real client uses and a template never produces.

    v3 saw no exclamation marks at all and no sentence-cased messages, so wording it had
    otherwise learned arrived looking unfamiliar.
    """
    if not text:
        return text
    roll = random.random()
    if roll < 0.10:
        text = text[0].upper() + text[1:]
    elif roll < 0.14:
        text = text.upper()
    tail = random.choices(["", "", "", "!", ".", "!!", " please", " thanks"],
                          weights=[60, 10, 10, 8, 6, 2, 2, 2])[0]
    return text + tail


def _attach(part: str, *, first: bool) -> str:
    """Join a trailing bound onto the sentence.

    Only a bound that opens with a comparator word can attach without a comma, and only
    directly after the place. A bare figure there reads as noise -- "Denver, CO 45k sqft"
    -- and a second bound run on reads as one phrase: "up to 59,500 sqft lower than
    $125k". Both appeared in the first draft of this function.
    """
    if first and part[:1].isalpha():
        return random.choice([", ", ", ", " ", " "]) + part
    return ", " + part


def _connected_sentence(pieces: dict[str, str]) -> str | None:
    """Weave field pieces into one flowing sentence, or None if they do not fit.

    v3 dropped ``location`` from every multi-field message that embedded it as a
    prepositional phrase — "retail in Miami under $3M" returned type and price only, on
    four of five multi-field eval turns and in production. It is not a merge bug: with an
    empty ``current_criteria`` the key is still absent from the model's reply.

    The cause is that this generator only ever produced comma-joined standalone clauses
    ("we need retail space, I'm looking in Miami, budget up to $3M"), so a place named
    mid-sentence was close to unseen. This is the missing shape.

    Requires both a type and a place, which is exactly the failing pattern; anything else
    falls back to the comma-joined form.
    """
    if "property_type" not in pieces or "location" not in pieces:
        return None
    head = f"{random.choice(SENTENCE_OPENERS)}{pieces['property_type']}"
    head += f"{random.choice(TYPE_SUFFIXES)} in {pieces['location']}"
    # Both orders, evenly. This was a fixed ``("size_sqft", "price")`` tuple, on the
    # grounds that size first reads more naturally -- and that made the reverse order
    # unlearnable in this shape. Every woven sentence in the set stated size before price,
    # so a woven message stating price first put its size clause exactly where the model
    # had only ever seen the sentence end. "I am gonna find a shop which is located in TX,
    # costs more than $1M, size is larger than 1000sqft" returned no size at all, 8 runs
    # out of 8; the same sentence with those two clauses swapped returned it 8 out of 8.
    #
    # The comma-joined form does emit both orders -- `random.sample` picks the keys in a
    # random order -- which is why the set as a whole looked balanced enough at 122 to 55.
    # It is balanced *across* shapes, not within this one, and the model conditions on the
    # shape: naming the place mid-sentence is what the woven form teaches, and inside it
    # price-then-size never occurred.
    #
    # Same defect as the DIRECTION wordings above, and kept symmetric for the same reason:
    # a shape the generator never emits is not learned as rare, it is learned as impossible.
    tail = [pieces[key] for key in ("size_sqft", "price") if key in pieces]
    if len(tail) == 2 and random.random() < 0.5:
        tail.reverse()
    return head + "".join(_attach(part, first=i == 0) for i, part in enumerate(tail))
