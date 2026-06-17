"""Set required env vars before any app module is imported."""
import os

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("TRIGGER_TOKEN", "test-trigger-token")
os.environ.setdefault("SERVICE_AUTH_TOKEN", "test-service-token")
