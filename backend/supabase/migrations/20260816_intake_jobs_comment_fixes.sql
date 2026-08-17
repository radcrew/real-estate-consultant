-- Corrects the record left by 20260814_intake_jobs.sql.
--
-- That file is applied, and editing it would print "CHANGED SINCE APPLIED" on every
-- migrate run forever — a warning people learn to scroll past is worse than a stale
-- comment. So the truth goes here, in the database's own comments, where anyone
-- inspecting the table sees it whether or not they read the migrations directory.
--
-- Two claims in that file are now wrong:
--
-- 1. "handed to the client over SSE" — streaming was removed. These routes require a
--    bearer token and EventSource cannot send one, so the client polls
--    GET /intake-sessions/{id}/jobs/{job_id} instead. The result column is read, not
--    pushed.
--
-- 2. "intake itself is anonymous" — 20260815_intake_sessions_user_id.sql gave sessions
--    an owner and scoped their policies to auth.uid(). The `authenticated`-only grant
--    below is now simply correct rather than a compromise, and the argument that
--    Supabase Realtime would deliver nothing to an anonymous visitor no longer applies
--    to anything.
--
-- 3. The policy it names, "Users can read intake jobs for visible sessions", no longer
--    exists: 20260815 replaced it with "Users can read intake jobs for own sessions".
--    Commenting on the old name is what caught this — the statement failed outright.
--
-- The rule itself is unchanged and still right: a job is readable exactly when its
-- session is.

comment on column public.intake_jobs.result is
  'SubmitLlmIntakeInputResponse payload. Polled by the client via the jobs endpoint; '
  'there is no streaming delivery.';

comment on column public.intake_jobs.input is
  'The user text for this turn, already guardrail-screened. Stored so a redrive replays '
  'the turn rather than losing it.';

comment on column public.intake_jobs.status is
  'queued -> running -> succeeded | failed. The queued -> running transition is the '
  'claim gate that makes SQS at-least-once delivery safe.';

comment on policy "Users can read intake jobs for own sessions" on public.intake_jobs is
  'Defence in depth: the API and worker use the service role and bypass RLS. Sessions '
  'are owned as of 20260815, so authenticated-only is the correct grant.';
