"""The words the generator draws from. Data only -- nothing here executes.

Separated because breadth *is* the training signal for several of these, and a list that
has to earn its length is easier to judge on its own. The first pass used 14 refusal
strings and the model learned the strings rather than the concept: it answered four of ten
eval refusals by re-asking the field being refused. ``SKIP_PHRASES`` is long on purpose.

Two rules hold across the file. Nothing here may name a property type the questionnaire
does not offer -- ``property_type_values`` reads those from the database dump, never from a
constant. And every entry is something a person would actually type; a wording invented to
pad a list teaches a distribution production never sends.
"""

from __future__ import annotations

# Drawn from backend/dataset/raw-data.json so the distribution matches real listings.
CITIES = [
    ("Austin", "TX"), ("Dallas", "TX"), ("Houston", "TX"), ("Denver", "CO"),
    ("Phoenix", "AZ"), ("Miami", "FL"), ("Seattle", "WA"), ("Chicago", "IL"),
    ("Atlanta", "GA"), ("Portland", "OR"), ("Nashville", "TN"), ("Charlotte", "NC"),
    ("Wailuku", "HI"), ("Boise", "ID"), ("Reno", "NV"), ("Tampa", "FL"),
    ("San Francisco", "CA"), ("Los Angeles", "CA"), ("San Diego", "CA"),
    ("Sacramento", "CA"), ("Las Vegas", "NV"), ("Salt Lake City", "UT"),
    ("Kansas City", "MO"), ("St. Louis", "MO"), ("Columbus", "OH"),
    ("Indianapolis", "IN"), ("Raleigh", "NC"), ("Orlando", "FL"),
    ("Jacksonville", "FL"), ("San Antonio", "TX"), ("Fort Worth", "TX"),
    ("Oklahoma City", "OK"), ("Memphis", "TN"), ("Louisville", "KY"),
    ("Milwaukee", "WI"), ("Minneapolis", "MN"), ("Pittsburgh", "PA"),
    ("Philadelphia", "PA"), ("Baltimore", "MD"), ("Richmond", "VA"),
    ("Albuquerque", "NM"), ("Tucson", "AZ"), ("Omaha", "NE"), ("Tulsa", "OK"),
]

# How clients actually type a city, mapped to the name that goes in gold. Unlike the
# "never add a region it omits" rule -- which stops "Tampa" being labelled "Tampa, FL" --
# these are the *same* place under a shorter name, so normalizing is not inventing.
#
# "located in SF" returned nothing at all: no message in the v3 set contained a nickname,
# so the model had never been shown that one resolves to a city.
CITY_ALIASES = {
    "SF": "San Francisco", "San Fran": "San Francisco", "the Bay Area": "San Francisco",
    "LA": "Los Angeles", "L.A.": "Los Angeles",
    "NYC": "New York", "New York City": "New York", "Manhattan": "New York",
    "Vegas": "Las Vegas", "Philly": "Philadelphia", "ATX": "Austin",
    "DFW": "Dallas", "H-town": "Houston", "SLC": "Salt Lake City",
    "KC": "Kansas City", "OKC": "Oklahoma City", "NOLA": "New Orleans",
    "PDX": "Portland", "ABQ": "Albuquerque", "the Twin Cities": "Minneapolis",
    "SoCal": "Los Angeles", "the Valley": "Phoenix",
}

# A state on its own is a legitimate answer -- "shopping mall in California" -- and the v3
# set never produced one, so every location it saw was a city. Gold is the state as
# written; there is no city to resolve it to.
STATES = [
    "California", "Texas", "Florida", "Colorado", "Arizona", "Washington",
    "Oregon", "Nevada", "Georgia", "Tennessee", "North Carolina", "South Carolina",
    "Illinois", "Ohio", "Michigan", "Pennsylvania", "New York", "New Jersey",
    "Massachusetts", "Virginia", "Maryland", "Missouri", "Minnesota", "Utah",
    "Idaho", "Oklahoma", "Kansas", "Indiana", "Wisconsin", "Kentucky",
]

# Standalone location clauses. ``_place`` decides what the place is called and what gold
# it carries, so these only wrap it -- otherwise a template naming {city}, {state} could
# not express "SF" or "California" at all.
LOCATION_TEMPLATES = [
    "I'm looking in {place}", "we need something in {place}", "{place}",
    "somewhere around {place}", "{place} area please", "looking at {place}",
    "located in {place}", "in {place}", "{place} market", "around {place}",
]
TYPE_TEMPLATES = [
    "we need {types} space", "{types} please", "looking for {types}",
    "something {types}", "{types} would work",
]

# Article forms. Nothing used to put an article in front of the type noun, so "I am
# finding a shop which is located in Amsterdam" was structurally unseen: v6 read "shop"
# correctly on its own and dropped the field entirely once the same word sat in a longer
# sentence. The relative clause matters as much as the article -- a type followed by
# "which"/"that" never occurred either.
TYPE_TEMPLATES_ARTICLE = [
    "{a} {types}", "I am finding {a} {types}", "we want {a} {types}",
    "{a} {types} which suits us", "{a} {types} that would work",
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

# Requirements the questionnaire does not ask about. They belong in no field, so gold
# ignores them entirely -- which is the behaviour being taught.
#
# "costs more than 100K, located in SF, 3 floor, industrial property! need to have good
# view!" states two of these. v3 had seen almost none, and a model trained only on
# messages where every clause maps to a field has no example of leaving one out. Several
# carry numbers on purpose ("3 floors", "12 ft ceilings"), because the live failure is a
# stray figure being read as size or price.
DISTRACTORS = [
    "3 floors", "two storeys", "single storey", "ground floor only", "top floor",
    "need a good view", "good natural light", "corner lot", "street frontage",
    "must have parking", "parking for 20 cars", "close to the highway",
    "near public transport", "walking distance to downtown",
    "12 ft ceilings", "high ceilings", "a loading dock would help",
    "three phase power", "air conditioned", "newly renovated", "move-in ready",
    "somewhere quiet", "no basement", "fenced yard", "24/7 access",
    "pet friendly", "wheelchair accessible", "fibre internet",
    "we'd like it modern", "nothing too old", "something with character",
    # Comparator-carrying requirements. Every entry above states its figure bare, so
    # "at least" and "no less than" had only ever introduced a real bound -- and the
    # figure they govern is the one thing that decides whether a clause is a field.
    #
    # INTAKE_OPENING_MESSAGE, the example the app suggests to every user, ends "with at
    # least 20 dock doors". That clause dragged its comparator onto the size: "100k sqft
    # industrial warehouse in Chicago" returns {"max": 100000}, correct under the bare-
    # figure convention, while the same message plus the dock clause returned {"min":
    # 100000} and copied the figure into `price` as well.
    #
    # The disambiguating signal is the noun the figure counts -- dock doors and parking
    # spaces are not square feet -- which is the same bet "SF" and "fenced yard" already
    # make. Both senses stay; only the ratio changes.
    "at least 20 dock doors", "with at least 4 loading bays",
    "no less than 10 parking spaces", "minimum 2 freight lifts",
    "more than 50 parking spaces", "at least 24 ft clear height",
    "32ft clear height", "at least 3 private offices",
    # Tenure. The questionnaire asks buy-or-lease nowhere, the opening message says "for
    # lease", and `multi-listing-price-docks` has scored "leasing," as ignorable since r2.
    "for lease", "for sale", "leasing only", "purchase only",
]

# Labels a user would plausibly use when naming a field they want to skip. Keyed by the
# questionnaire's required fields; ``_skip_label`` falls back for any key added later.
FIELD_LABELS = {
    "location": ["location", "city", "area"],
    "property_type": ["property type", "space type", "building type"],
    "price": ["budget", "price", "price range"],
    "size_sqft": ["size", "square footage", "size question"],
}


# Figures written out rather than digitised. The eval has scored "half a million", "a
# quarter of a million" and "one and a half million tops" since r1, and the generator has
# never produced one -- those turns tested a wording training never taught.
MONEY_IN_WORDS = {
    250_000: ["a quarter of a million", "quarter of a million", "250 thousand"],
    500_000: ["half a million", "a half million", "500 thousand"],
    750_000: ["three quarters of a million", "750 thousand"],
    1_000_000: ["a million", "one million", "1 mil"],
    1_500_000: ["one and a half million", "a million and a half", "1.5 mil"],
    2_000_000: ["two million", "a couple million", "2 mil"],
    3_000_000: ["three million", "3 mil"],
    5_000_000: ["five million", "5 mil"],
}
SQFT_IN_WORDS = {
    5_000: ["five thousand square feet"],
    10_000: ["ten thousand square feet"],
    20_000: ["twenty thousand square feet"],
    50_000: ["fifty thousand square feet"],
}

# "about 5,000 sqft" is still a bound, not a new kind of value -- gold is unchanged. Only
# the wording softens, and v3 saw none of it.
APPROX_PREFIXES = ["around ", "about ", "roughly ", "approximately ", "~", "somewhere near "]


# Every way this industry writes square feet. v3 wrote only "sqft" and "square feet", so
# "sq ft", "sq. ft." and the ubiquitous "SF" were all unseen.
#
# "SF" is deliberately included even though CITY_ALIASES maps it to San Francisco: in
# commercial real estate it means square feet far more often, and the disambiguating
# signal -- a figure immediately before it -- is exactly what training should teach. Both
# senses appear in the set so context has to do the work.
SQFT_UNITS = ["sqft", "sq ft", "sq. ft.", "SF", "square feet", "square foot",
              "sf", "sq.ft.", "square footage"]


# Square yards. The everyday unit for a plot in South-Asian markets, where "1500 yard"
# means 1,500 square yards -- 13,500 sqft -- and the figure is never written in feet.
#
# This is the one unit in the set where the message figure and the gold figure differ, so
# it is the only place the model has to *convert* rather than copy. "1500 yard ground"
# came back from production with no size at all, and the reason was in the set: all 22
# occurrences of "yard" were `fenced yard`, a DISTRACTORS entry, so the only thing the
# word had ever been used for was noise. `fenced yard` stays -- the disambiguating signal
# is the figure in front of it, exactly as with "SF" -- but it is no longer alone.
SQYD_UNITS = ["yard", "yards", "sq yard", "sq yards", "square yard", "square yards",
              "sq yd", "sq. yd.", "gaj"]
SQFT_PER_SQYD = 9

# Square metres, the other unit a client states and the gold does not use. Same rule as
# yards -- gold is square feet, so the model converts rather than copies -- but the factor
# is not an integer, so a value cannot be tested for metre-compatibility with a modulo the
# way `value % SQFT_PER_SQYD` tests yards. Values are generated *from* a round metre
# figure instead, and `_sqm_figure` recovers it by round-trip.
#
# That round-trip also succeeds on roughly one ordinary sqft draw in eleven -- the image
# of `_sqm_to_sqft` covers about 1/10.76 of the integers, and a draw landing in it is
# indistinguishable from a generated one. That is harmless rather than a mislabel: the
# metre figure printed is a correct statement of that same area, so the example teaches
# the same conversion. It only means metre coverage is somewhat wider than the 15% draw
# rate below suggests.
SQM_UNITS = ["square meters", "square metres", "sq m", "sqm", "sq. m.", "m2",
             "square meter", "square metre"]
SQFT_PER_SQM = 10.7639


# The model has to read DIRECTION off the wording, so both sides need comparable breadth.
# v2 had 4 upper phrasings against 3 lower, and a 2:1 style weighting on top, producing
# 445 upper-bound examples against 199 lower. It generalised unseen *upper* wordings fine
# ("less than", "lower than") because the prior agreed, and inverted unseen *lower* ones:
# "higher than $500K" came back as {"max": 500000}.
# Kept symmetric on purpose. r6 scored `nothing over $2M` correct and `nothing below
# 5,000 sqft` wrong on v3, v4 f16 and v4 q4 alike, and the asymmetry below is why: the max
# list carried a negated form ("not over") and the min list carried none, so the model
# learned to negate in one direction only. Every negation added to one list now has a
# counterpart in the other.
#
# "floor" and "ceiling" are bound words the set never taught. Every occurrence of "floor"
# in the generated data was `ground floor` / `top floor` / `office floor` -- a storey,
# never a budget floor -- so `$400k floor on the budget` had nothing to attach to and came
# back as a ceiling. Both senses stay in the set, as with "SF" in SQFT_UNITS:
# the disambiguating signal is the figure beside it, and context has to do the work.
#
# None of these is an eval wording. `nothing over {v}` and `just shy of {v}` were both
# here for a draft, and both are a bound-direction turn verbatim -- adding them scores
# the turn without teaching anything the neighbouring phrasings do not. The neighbours
# are the honest form of the same lesson, and TestBoundWordingEvalSeparation pins it.
MAX_PHRASES = [
    "up to {v}", "no more than {v}", "under {v}", "less than {v}", "lower than {v}",
    "below {v}", "at most {v}", "not over {v}", "{v} or less", "{v} max", "maximum {v}",
    "nothing above {v}", "never more than {v}", "no higher than {v}",
    "{v} ceiling", "a ceiling of {v}", "capped at {v}", "just under {v}",
]
MIN_PHRASES = [
    "at least {v}", "no less than {v}", "more than {v}", "higher than {v}", "over {v}",
    "above {v}", "starting at {v}", "north of {v}", "{v} or more", "{v} and up",
    "minimum {v}",
    "nothing under {v}", "not below {v}", "never less than {v}",
    "{v} floor", "a floor of {v}", "no lower than {v}", "at minimum {v}",
]
BETWEEN_PHRASES = [
    "between {lo} and {hi}", "from {lo} to {hi}", "{lo} to {hi}",
    "more than {lo} but under {hi}", "at least {lo} and no more than {hi}",
    "in the {lo} to {hi} range", "anywhere from {lo} up to {hi}",
    "{lo} minimum, {hi} maximum", "no less than {lo}, no more than {hi}",
]
# The same range with the ceiling stated first. Every template above puts {lo} before
# {hi}, so position and direction never disagreed and the model learned to read the
# order instead of the comparator: given "lower than $2M, higher than $500K" all three
# r6 models returned min $2M / max $500K -- first figure to min, second to max, both
# comparators ignored. These are the counter-examples that make position uninformative.
# The comma-joined form deliberately uses different comparators than that turn does, so
# what it scores stays "reads the comparator", not "has seen this sentence".
REVERSED_BETWEEN_PHRASES = [
    "under {hi} but over {lo}", "no more than {hi} and no less than {lo}",
    "at most {hi}, at least {lo}", "{hi} ceiling, {lo} floor",
    "{hi} maximum, {lo} minimum", "below {hi} but above {lo}",
]
# Hyphenated ranges, which is how one is usually typed. Kept apart from BETWEEN_PHRASES
# because the low side drops its unit -- "10,000-15,000 sqft", never
# "10,000 sqft-15,000 sqft", which is what a shared template produces.
HYPHEN_PHRASES = ["{lo}-{hi}", "{lo} - {hi}", "{lo}–{hi}"]


# Type phrasings that also occur in the set with a meaning that is not a type, drawn
# extra often so the collision is decided by context rather than by frequency.
#
# `ground` is a configured `land` phrasing, and `ground floor` is a DISTRACTORS entry --
# a storey, extracted into nothing. A flat draw over land's phrasings put `ground` in ~8
# messages against 18 for `ground floor`, so the token's own statistics said "ignore me",
# and "warehouse, restaurant, shop, 1500 yard ground" came back from production with no
# `land` at all. Both senses stay, as with "SF" and with "floor" in MIN_PHRASES; only the
# ratio changes.
#
# Keyed by option, so a phrasing that stops being generated simply stops being weighted.
AMBIGUOUS_TYPE_PHRASINGS = {"land": ("ground",)}
# Measured, not guessed. At 4x the two senses land within noise of each other -- five
# seeds ran 16v19, 18v16, 25v7, 11v14, 17v16 -- so whether the type sense outnumbers the
# distractor came down to the draw. At 8x the worst of those five is 1.3:1, while `ground`
# still takes only about a quarter of land's mentions: a thumb on the scale, not a rewrite.
_AMBIGUOUS_WEIGHT = 8.0


# Openers for a woven sentence. Empty is included because "retail in Miami under $3M" is
# how people actually type.
SENTENCE_OPENERS = ["", "", "looking for ", "we want to buy ", "we need ", "I need ",
                    "after ", "trying to find ", "we're after "]
# Attached to the type when it reads naturally: "office space in Seattle".
TYPE_SUFFIXES = ["", "", " space", " property"]
