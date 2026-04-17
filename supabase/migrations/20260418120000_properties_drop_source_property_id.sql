-- Remove external listing id; seed uses INSERT (re-run appends rows unless you TRUNCATE in dev).
drop index if exists public.properties_source_property_id_uidx;

alter table public.properties
  drop constraint if exists properties_source_property_id_key;

alter table public.properties
  drop column if exists source_property_id;

notify pgrst, 'reload schema';
