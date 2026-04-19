-- Legacy name was ``questionnaire_sessions``; app uses ``intake_sessions``.

do $$
begin
    if to_regclass('public.questionnaire_sessions') is not null
       and to_regclass('public.intake_sessions') is null then
        alter table public.questionnaire_sessions rename to intake_sessions;
    end if;
end
$$;

do $$
begin
    if exists (
        select 1
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'public'
          and c.relname = 'questionnaire_sessions_search_profile_id_idx'
    ) then
        execute
            'alter index public.questionnaire_sessions_search_profile_id_idx '
            || 'rename to intake_sessions_search_profile_id_idx';
    end if;
end
$$;

do $$
begin
    if exists (
        select 1
        from pg_constraint
        where conname = 'questionnaire_sessions_pkey'
          and conrelid = 'public.intake_sessions'::regclass
    ) then
        alter table public.intake_sessions
            rename constraint questionnaire_sessions_pkey to intake_sessions_pkey;
    end if;
end
$$;

notify pgrst, 'reload schema';
