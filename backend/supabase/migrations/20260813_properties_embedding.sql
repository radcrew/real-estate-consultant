-- Ingest-time embeddings for similar-listings search.
--
-- Today find_similar_listings embeds the seed plus up to 100 candidate listings on
-- every request, re-embedding the same rows forever, and ranks a pre-filtered pool of
-- 40 in Python. Storing one vector per listing at ingest turns that into a single
-- embedding call plus an indexed k-NN query over the whole corpus.
--
-- Dimension is fixed at 1024 to match Cohere Embed v3 on Bedrock. That is deliberate:
-- HNSW requires a fixed width, and a stored vector is only useful if every row was
-- produced by the same model. Changing embedding model means a full re-index, so
-- embedding_model is recorded per row to make stale rows findable.

create extension if not exists vector;

alter table public.properties
  add column if not exists embedding vector(1024),
  add column if not exists embedding_model text,
  add column if not exists embedded_at timestamptz;

-- Cosine distance (<=>) matches the similarity the Python ranking used.
create index if not exists properties_embedding_hnsw_idx
  on public.properties using hnsw (embedding vector_cosine_ops);

-- Backfill and the ingest worker scan for rows still needing a vector; a partial
-- index keeps that cheap as the embedded share grows.
create index if not exists properties_embedding_pending_idx
  on public.properties (id)
  where embedding is null;

comment on column public.properties.embedding is
  'Cohere Embed v3 (1024-dim) listing embedding, written at ingest.';
comment on column public.properties.embedding_model is
  'Model that produced embedding; rows not matching the active model are stale.';
