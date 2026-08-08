-- Widen property_type so the questionnaire can express the catalogue.
--
-- where_criteria filters on property_type, and the configured options covered only
-- industrial / retail / flex -- 10 of the 50 listings. A user who named a type was
-- locked out of the other 80%, including Land, which is 44% of the catalogue on its own.
--
-- Warehouse is deliberately absent: no listing carries it, and an option that always
-- returns nothing is worse than no option. Add it when inventory does.
--
-- Values are lowercase to match the existing rows; search compares with ilike, so
-- casing does not affect matching.

update public.questions
set options = '[
  {"label": "Industrial",  "value": "industrial"},
  {"label": "Retail",      "value": "retail"},
  {"label": "Flex",        "value": "flex"},
  {"label": "Land",        "value": "land"},
  {"label": "Office",      "value": "office"},
  {"label": "Multifamily", "value": "multifamily"},
  {"label": "Specialty",   "value": "specialty"}
]'::jsonb
where key = 'property_type';
