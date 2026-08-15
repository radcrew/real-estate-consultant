"""Vocabulary tables for checking an extracted value against the message that produced it.

These are lookup data, kept apart from the filters in ``intake_criteria`` so a wording
added here is a visible one-line diff rather than a change inside a function.
"""

from __future__ import annotations

# How a client names each property type, mirroring
# ``services/intake-model/pipeline/data/property_type_phrasings.json`` — the table the
# training set is generated from, so this is the vocabulary the model was actually taught.
#
# It is deliberately **not** extended with synonyms of our own. The model generalises well
# past this list ("depot", "boutique", "cold storage facility" and "twelve flats" are all
# extracted correctly and none of them appear here), and a word added on a hunch would
# start ruling *out* the type it was guessed against. Measured on the eval set, treating
# this table as the set of things a client may say costs 7 of 35 correct type values.
TYPE_PHRASINGS: dict[str, tuple[str, ...]] = {
    "industrial": (
        "warehouse", "factory", "distribution center", "logistics facility",
        "manufacturing space", "metal building", "heavy machinery space",
        "assembly area", "cargo bay", "production site", "raw material storage",
        "equipment shed", "manufactured goods facility",
    ),
    "retail": (
        "mall", "shop", "storefront", "commercial street", "strip center",
        "pedestrian zone", "marketplace", "shopping center", "consumer hub",
        "commerce location", "trade area", "commerce space", "convenience store",
        "mall entrance", "frontage", "shopping district", "commerce zone",
        "business lane", "commerce block", "commerce mall",
    ),
    "flex": (
        "loft", "garage", "workshop", "multifunctional space", "modular facility",
        "creative workspace", "storage unit", "adaptive space", "project space",
    ),
    "land": (
        "site", "acreage", "property", "ground", "lot", "homestead", "farm",
        "estate", "ranch", "meadow", "garden", "pasture",
    ),
    "office": (
        "suite", "downtown", "corporate", "headquarters", "tower", "workspace",
    ),
    "multifamily": (
        "apartment building", "condo complex", "high-rise residence",
        "residential tower", "townhouse community", "multi-unit property",
        "dormitory-style living", "group housing", "mixed-use development",
        "family housing", "low-income housing", "student housing", "rental property",
        "housing complex", "residential buildings", "residential complex",
        "apartment complex", "condominiums", "residential apartment buildings",
        "senior living community",
    ),
    "specialty": (),
}

# Phrasings that name a structure or a place rather than a use. They still *support* the
# type they are listed under — a client saying "estate" may well mean land — but they do
# not count as the message naming a type, because almost every commercial enquiry contains
# one. "I need a commercial property for my bakery" says nothing about industrial versus
# retail, and without this exclusion the bare word "property" would rule out both.
#
# ``ground`` is already treated as ambiguous by the generator's own
# ``AMBIGUOUS_TYPE_PHRASINGS``, for the same reason: "ground floor" is a storey.
GENERIC_PHRASINGS = frozenset({
    "property", "site", "estate", "ground", "lot", "downtown", "corporate",
    "frontage", "commercial street", "pedestrian zone", "commerce location",
    "trade area", "commerce zone", "business lane", "commerce block",
    "shopping district", "mall entrance", "workspace",
})

# Every area unit a client uses, as (square feet per unit, what to call it back to them).
# Keyed by their wording with punctuation and spacing removed, so "sq. km", "sq km" and
# "sqkm" are one entry.
#
# Two jobs. The model is meant to convert and mostly does, but it drops the unit on
# wordings it has seen less of — "3sq kilometers" came back as 3 — so this is the
# arithmetic. And it is what lets the answer be explained: someone shown 32,291,731 sq ft
# after typing "3sq kilometers" has no way to tell a correct conversion from a bug.
#
# Factors are exact where the definition is exact (9, 43560, 27878400) and full precision
# where it is not, because rounding the *factor* is a real error even though rounding the
# result is not: 10.76 instead of 10.763910 loses 36 sq ft on a 10,000 sq m site.
#
# Square feet map to 1.0 and are listed rather than omitted. A missing key would be
# indistinguishable from an unrecognised unit, and the two need different answers: one is
# "nothing to do", the other is "say nothing, you do not know what this is".
_SQ_METRE = 10.763910416709722

AREA_UNITS: dict[str, tuple[float, str]] = {
    "sqft": (1.0, "square foot"), "sqfeet": (1.0, "square foot"),
    "sqfoot": (1.0, "square foot"), "squarefeet": (1.0, "square foot"),
    "squarefoot": (1.0, "square foot"), "squareft": (1.0, "square foot"),
    "sf": (1.0, "square foot"),

    "yard": (9.0, "square yard"), "yards": (9.0, "square yard"),
    "yd": (9.0, "square yard"), "yds": (9.0, "square yard"),
    "sqyard": (9.0, "square yard"), "sqyards": (9.0, "square yard"),
    "sqyd": (9.0, "square yard"), "sqyds": (9.0, "square yard"),
    "squareyard": (9.0, "square yard"), "squareyards": (9.0, "square yard"),

    "sqm": (_SQ_METRE, "square metre"), "sqmetre": (_SQ_METRE, "square metre"),
    "sqmetres": (_SQ_METRE, "square metre"), "sqmeter": (_SQ_METRE, "square metre"),
    "sqmeters": (_SQ_METRE, "square metre"), "squarem": (_SQ_METRE, "square metre"),
    "squaremetre": (_SQ_METRE, "square metre"), "squaremetres": (_SQ_METRE, "square metre"),
    "squaremeter": (_SQ_METRE, "square metre"), "squaremeters": (_SQ_METRE, "square metre"),

    "sqkm": (_SQ_METRE * 1e6, "square kilometre"),
    "sqkms": (_SQ_METRE * 1e6, "square kilometre"),
    "sqkilometre": (_SQ_METRE * 1e6, "square kilometre"),
    "sqkilometres": (_SQ_METRE * 1e6, "square kilometre"),
    "sqkilometer": (_SQ_METRE * 1e6, "square kilometre"),
    "sqkilometers": (_SQ_METRE * 1e6, "square kilometre"),
    "squarekilometre": (_SQ_METRE * 1e6, "square kilometre"),
    "squarekilometres": (_SQ_METRE * 1e6, "square kilometre"),
    "squarekilometer": (_SQ_METRE * 1e6, "square kilometre"),
    "squarekilometers": (_SQ_METRE * 1e6, "square kilometre"),
    "km2": (_SQ_METRE * 1e6, "square kilometre"),

    "hectare": (_SQ_METRE * 1e4, "hectare"), "hectares": (_SQ_METRE * 1e4, "hectare"),
    "ha": (_SQ_METRE * 1e4, "hectare"),

    "acre": (43560.0, "acre"), "acres": (43560.0, "acre"),

    "sqmile": (27878400.0, "square mile"), "sqmiles": (27878400.0, "square mile"),
    "sqmi": (27878400.0, "square mile"),
    "squaremile": (27878400.0, "square mile"), "squaremiles": (27878400.0, "square mile"),
}

# Postal abbreviations, so "TX" in the message supports "Texas" in the answer and the
# other way round. The model expands an abbreviation it was given far more often than it
# contracts a name, but both directions cost the same to allow.
STATE_ABBREVIATIONS: dict[str, str] = {
    "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
    "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
    "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
    "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
    "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
    "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
    "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
    "new hampshire": "nh", "new jersey": "nj", "new mexico": "nm", "new york": "ny",
    "north carolina": "nc", "north dakota": "nd", "ohio": "oh", "oklahoma": "ok",
    "oregon": "or", "pennsylvania": "pa", "rhode island": "ri",
    "south carolina": "sc", "south dakota": "sd", "tennessee": "tn", "texas": "tx",
    "utah": "ut", "vermont": "vt", "virginia": "va", "washington": "wa",
    "west virginia": "wv", "wisconsin": "wi", "wyoming": "wy",
    "district of columbia": "dc",
}

# Words a place name is built from that carry no identity of their own. "Lake City" is
# supported by "lake" only in the sense that any lake would do, so these are ignored when
# falling back to word-level matching.
GEO_STOPWORDS = frozenset({
    "the", "and", "city", "town", "county", "state", "area", "metro", "greater",
    "north", "south", "east", "west", "central", "upper", "lower", "new", "old",
    "downtown", "uptown", "midtown", "district", "region", "borough", "village",
})
