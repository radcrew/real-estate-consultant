"""How a number is chosen, and how it gets written down.

Sampling and formatting live together because they are one decision. ``_price_value`` picks
a figure a client would say and ``_fmt_money`` writes it the way they would say it, and a
mismatch between the two is invisible in the data: perfectly valid JSON describing a
sentence nobody would type.

The distinction this module exists to hold is **money against area**. The digits are
identical -- "100k" is a budget and "100k sqft" is a size -- and the unit is the only thing
separating them. That is also the production bug this project has spent the most on, so
every renderer here states its unit or deliberately omits it, and ``FieldNumbers`` binds a
sampler to the renderers allowed to write its output.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import NamedTuple

from pipeline.data.vocabulary import (
    APPROX_PREFIXES,
    BETWEEN_PHRASES,
    HYPHEN_PHRASES,
    MAX_PHRASES,
    MIN_PHRASES,
    MONEY_IN_WORDS,
    REVERSED_BETWEEN_PHRASES,
    SQFT_IN_WORDS,
    SQFT_PER_SQM,
    SQFT_PER_SQYD,
    SQFT_UNITS,
    SQM_UNITS,
    SQYD_UNITS,
)


def _in_millions(value: int) -> str:
    """"$2.5M" / "2.5M" / "$2.5 million" -- including below a million: "$0.5M"."""
    millions = value / 1_000_000
    return random.choice([
        f"${millions:g}M", f"{millions:g}M", f"${millions:g}m",
        f"${millions:g} million", f"{millions:g} million", f"{millions:g} mil",
    ])


def _in_thousands(value: int) -> str:
    """"$500k" / "500K" / "500 grand" / "500k bucks".

    v3 wrote only "${n}k": always a dollar sign, always lowercase. So "costs more than
    100K" and "less than 10K bucks" -- both real messages -- arrived in a form the model
    had never seen, and it read neither as a budget.
    """
    thousands = value // 1000
    return random.choice([
        f"${thousands}k", f"${thousands}K", f"{thousands}k", f"{thousands}K",
        f"${thousands}k", f"{thousands} grand", f"{thousands}k bucks",
        f"${thousands},000", f"{thousands} thousand",
    ])


def _fmt_money(value: int) -> str:
    if value in MONEY_IN_WORDS and random.random() < 0.25:
        return random.choice(MONEY_IN_WORDS[value])
    if value >= 1_000_000 and value % 100_000 == 0:
        return _in_millions(value)
    # Sub-million budgets written in millions. M-notation used to start at 1,000,000, so
    # the model only ever saw a leading digit of 1 or more and broke on a leading zero
    # two ways: "$0.1M" came back as the bare token 0.1M -- invalid JSON, not merely a
    # wrong number -- and "$0.1 million" as 1000000, a factor of ten out.
    #
    # Kept a minority form, because "$500k" is still how most people write this.
    if value >= 100_000 and value % 50_000 == 0 and random.random() < 0.3:
        return _in_millions(value)
    if value >= 1000 and value % 1000 == 0:
        return random.choice([f"${value:,}", f"{value:,} dollars", _in_thousands(value)])
    return f"${value:,}"


def _sqm_to_sqft(sqm: int) -> int:
    return round(sqm * SQFT_PER_SQM)


def _sqm_figure(value: int) -> int | None:
    """The round metre figure ``value`` was generated from, or None if it was not."""
    sqm = round(value / SQFT_PER_SQM)
    return sqm if sqm > 0 and _sqm_to_sqft(sqm) == value else None


def _fmt_sqft(value: int) -> str:
    """Square feet, always. Safe to pair with another figure in the same phrase."""
    if value in SQFT_IN_WORDS and random.random() < 0.2:
        return random.choice(SQFT_IN_WORDS[value])
    unit = random.choice(SQFT_UNITS)
    if value >= 1000 and value % 1000 == 0 and random.random() < 0.35:
        return f"{value // 1000}k {unit}"
    return f"{value:,} {unit}"


def _fmt_sqft_solo(value: int) -> str:
    """The only figure in its phrase, so it may be stated in square yards.

    Yards are kept out of two-figure phrasings on purpose. Each side of a range renders
    independently, so a shared unit cannot be agreed on: "9,000-1,500 yards" is what a
    hyphenated range produces when the high side picks yards and the low side does not,
    and no reading of that text yields the gold. A plot is quoted as a single figure
    anyway, which is where the unit actually occurs.
    """
    if value % SQFT_PER_SQYD == 0 and random.random() < 0.45:
        return f"{value // SQFT_PER_SQYD:,} {random.choice(SQYD_UNITS)}"
    if (sqm := _sqm_figure(value)) is not None and random.random() < 0.45:
        return f"{sqm:,} {random.choice(SQM_UNITS)}"
    return _fmt_sqft(value)


def _price_value() -> int:
    """A budget, drawn from one of four bands.

    The institutional band is why this is no longer a flat ``random.choice``. "from $30M
    to $40M" came back as 3,000,000 - 4,000,000, a factor of ten out in both bounds, and
    the set explains it exactly: the sampler stopped at $4.9M, so **every** M-notation
    figure ever generated had a single digit before the decimal point -- the integer parts
    across the whole set were 0 through 8, never two digits. "$30M" was a token shape the
    model had never seen, and "$3.0M" -- which it had seen hundreds of times -- is one dot
    away. Commercial real estate does not stop at five million.
    """
    band = random.choices(["mid", "small", "round", "large"], weights=[30, 30, 25, 15])[0]
    if band == "small":
        return random.randrange(20_000, 200_000, 5_000)
    if band == "round":
        # Round six-figure budgets. Without this the two bands above meet at 200k, so
        # the band a client is most likely to state in millions -- "$0.5M" -- was reachable
        # only as one of eight values, and M-notation had almost nothing to attach to.
        return random.randrange(100_000, 1_000_000, 50_000)
    if band == "large":
        # Starts where "mid" stops, so the two are continuous. Multiples of 500k keep
        # `_in_millions` to one decimal place: "$42.5M", never "$42.4713M".
        #
        # Skewed low on purpose. $10-50M is an ordinary institutional deal and $100M+ is
        # not; a flat draw to $150M put a third of the band in three digits, which teaches
        # the rare shape as often as the common one.
        if random.random() < 0.8:
            return random.randrange(5_000_000, 60_000_000, 500_000)
        return random.randrange(60_000_000, 200_000_000, 1_000_000)
    return random.randrange(200_000, 5_000_000, 100_000)


def _sqft_value() -> int:
    # A fifth of the draws are a whole number of square yards, so the yard renderer has
    # round figures to state. 13,500 sqft is "1,500 yards"; 13,700 sqft is 1,522.2 yards,
    # which nobody writes, and rounding the text would put the gold out by 2 sqft.
    if random.random() < 0.2:
        return random.randrange(100, 6_500, 50) * SQFT_PER_SQYD
    # Round metre figures, so the metre renderer has something clean to state. Drawn to
    # 90,000 m2 because that is ~970k sqft, the top of the six-figure band below.
    if random.random() < 0.15:
        return _sqm_to_sqft(random.randrange(100, 90_000, 50))
    # Six-figure sizes. This stopped at 59,500, so no size the model ever saw reached
    # 100,000 -- while `_price_value` draws exactly 100,000 in ~2% of budgets. "100k" was
    # therefore money and nothing else, and "100k sqft industrial warehouse" came back as
    # {"price": {"max": 100000}} with no size at all. The wording the app *suggests* to
    # every user, in INTAKE_OPENING_MESSAGE, asks for 100k sqft.
    #
    # This is the defect `_price_value` documents, in the other field: a sampler that
    # stops short does not teach a shape as rare, it teaches it as impossible. Capped
    # below 1,000,000 because `_fmt_sqft` has no M-notation and would write "1000k sqft".
    if random.random() < 0.25:
        return random.randrange(60_000, 1_000_000, 10_000)
    return random.randrange(1_000, 60_000, 500)


class FieldNumbers(NamedTuple):
    """How one numeric field renders and samples, and what a bare figure means for it.

    Replaces a bare ``(callable, callable)`` tuple indexed as ``fmt[0]`` / ``fmt[1]``,
    where only the first element formatted and nothing said what the second did.
    """

    render: Callable[[int], str]  # 4200 -> "4,200 sqft"
    sample: Callable[[], int]  # draw a plausible value
    # The low side of a hyphenated range, where the unit belongs only on the high side:
    # "10,000-15,000 sqft". Money keeps its symbol, since "$500k-$1M" is how it is written.
    render_low: Callable[[int], str]
    # The only figure in its phrase. Free to pick a unit the other renderers cannot, since
    # there is no second figure it has to agree with -- square yards, for size.
    render_solo: Callable[[int], str]


def _range_high(low: int) -> int:
    """A ceiling a client would state beside ``low``, not a second independent draw.

    ``low + sample()`` takes the two ends from unrelated bands. That was merely odd while
    budgets stopped at $5M -- "between $25,000 and $4.5M" -- and is untenable once the
    sampler reaches $150M, where the same code pairs a $45,000 floor with a $92.5M
    ceiling. Nobody writes that, and the model would be learning that the two figures in
    a range are unrelated.

    Scaling the span to the floor keeps both ends in one world at any magnitude, and the
    grain keeps the ceiling a figure someone would say. It is taken from the ceiling's own
    magnitude rather than the floor's, because those differ across a power of ten: a
    $950,000 floor rounded on the floor's grain yields $1,905,000, which ``_fmt_money``
    writes as "$1905k".
    """
    high = low + int(low * random.uniform(0.2, 2.0))
    grain = 100_000 if high >= 1_000_000 else 5_000 if high >= 100_000 else 500
    # Rounding down can meet or cross the floor when the span is short next to the grain.
    return max(low + grain, high - high % grain)


def _range_phrase(numbers: FieldNumbers) -> tuple[dict[str, int], str]:
    """Return (gold bounds, phrasing).

    Weights are set on the **gold** distribution, not the style names: ``bare`` also
    yields a ``max`` bound for price, so explicit ``max`` is damped to compensate. The
    result is roughly 40% max-only, 40% min-only, 20% two-sided — parity is the point,
    because the imbalance is what let a learned prior override an explicit comparator.
    """
    style = random.choices(["max", "min", "between", "bare"], weights=[25, 40, 20, 15])[0]

    def soften(text: str) -> str:
        """Sometimes hedge a bare figure. The bound is unchanged; only the wording is.

        Only bare figures. Prefixing one that already carries a comparator produces
        "we can spend above around 35,000 dollars", which no one writes -- the comparator
        already conveys the imprecision.
        """
        return random.choice(APPROX_PREFIXES) + text if random.random() < 0.15 else text

    if style == "max":
        value = numbers.sample()
        return {"max": value}, random.choice(MAX_PHRASES).format(v=numbers.render_solo(value))
    if style == "min":
        value = numbers.sample()
        return {"min": value}, random.choice(MIN_PHRASES).format(v=numbers.render_solo(value))
    if style == "bare":
        # A figure with no comparator is a ceiling in both fields: "half a million" is a
        # budget the client is shopping under, and "130k sqft" is a size they are shopping
        # under too. Neither states a floor, and reading either as exact makes the search
        # match only listings that hit the figure dead on.
        #
        # This is *unit-carrying* bare only. A naked figure answering a direct question
        # stays exact -- see `_bare_answer`, where v3's max-only turned an answer of "32"
        # into a 32 sqft ceiling that every later correction stacked against.
        value = numbers.sample()
        return {"max": value}, soften(numbers.render_solo(value))
    low = numbers.sample()
    high = _range_high(low)
    if random.random() < 0.3:
        return {"min": low, "max": high}, random.choice(HYPHEN_PHRASES).format(
            lo=numbers.render_low(low), hi=numbers.render(high)
        )
    # Held well below the {lo}-first share: stating the ceiling first is the rarer way to
    # write a range, and over-weighting it would only move the positional prior rather
    # than remove it. The gold is identical either way -- only the word order differs.
    if random.random() < 0.25:
        return {"min": low, "max": high}, random.choice(REVERSED_BETWEEN_PHRASES).format(
            lo=numbers.render(low), hi=numbers.render(high)
        )
    return {"min": low, "max": high}, random.choice(BETWEEN_PHRASES).format(
        lo=numbers.render(low), hi=numbers.render(high)
    )


PRICE_NUMBERS = FieldNumbers(
    _fmt_money, _price_value,
    render_low=_fmt_money, render_solo=_fmt_money,
)
SQFT_NUMBERS = FieldNumbers(
    _fmt_sqft, _sqft_value,
    render_low=lambda v: f"{v:,}", render_solo=_fmt_sqft_solo,
)
