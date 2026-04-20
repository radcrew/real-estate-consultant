-- Application creates ``search_profiles`` then sets ``search_profile_id``.
-- A bare ``gen_random_uuid()`` default does not create a parent row and breaks the FK.

alter table public.intake_sessions
    alter column search_profile_id drop default;

notify pgrst, 'reload schema';
