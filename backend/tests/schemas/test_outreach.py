import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.outreach import (
    CreateOutreachDraftRequest,
    OutreachDraftResponse,
    PatchOutreachDraftRequest,
)


class TestCreateOutreachDraftRequest:
    def test_valid_uuid(self):
        pid = uuid.uuid4()
        obj = CreateOutreachDraftRequest(property_id=pid)
        assert obj.property_id == pid

    def test_invalid_uuid_raises(self):
        with pytest.raises(ValidationError):
            CreateOutreachDraftRequest(property_id="not-a-uuid")

    def test_missing_property_id_raises(self):
        with pytest.raises(ValidationError):
            CreateOutreachDraftRequest()


class TestOutreachDraftResponse:
    def test_all_optional_except_id(self):
        obj = OutreachDraftResponse(id=uuid.uuid4())
        assert obj.property_id is None
        assert obj.draft_email is None
        assert obj.created_at is None

    def test_full_fields(self):
        now = datetime(2024, 1, 1, tzinfo=timezone.utc)
        uid = uuid.uuid4()
        obj = OutreachDraftResponse(
            id=uid,
            property_id=uid,
            user_id=uid,
            draft_email="Hello broker,\n...",
            created_at=now,
        )
        assert obj.draft_email == "Hello broker,\n..."
        assert obj.created_at == now


class TestPatchOutreachDraftRequest:
    def test_valid(self):
        obj = PatchOutreachDraftRequest(draft_email="Hi there")
        assert obj.draft_email == "Hi there"

    def test_empty_raises(self):
        with pytest.raises(ValidationError):
            PatchOutreachDraftRequest(draft_email="")

    def test_too_long_raises(self):
        with pytest.raises(ValidationError):
            PatchOutreachDraftRequest(draft_email="A" * 32001)
