-- PostgREST does not reliably expose a column named ``position`` (reserved); use ``sort_order``.
do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'property_images'
      and column_name = 'position'
  ) then
    execute 'alter table public.property_images rename column "position" to sort_order';
  end if;
end;
$$;

notify pgrst, 'reload schema';
