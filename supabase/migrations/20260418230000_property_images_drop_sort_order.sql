alter table public.property_images drop column if exists sort_order;

notify pgrst, 'reload schema';
