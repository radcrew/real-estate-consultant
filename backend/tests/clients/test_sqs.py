"""Tests for the intake-turn SQS publisher."""
from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import HTTPException

from app.clients.sqs import ChatJobQueue

_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/123456789012/chat-intake.fifo"


def _make_queue(*, queue_url: str = _QUEUE_URL, client: object | None = None) -> ChatJobQueue:
    mock_settings = MagicMock()
    mock_settings.aws_region = "us-east-1"
    mock_settings.sqs_chat_queue_url = queue_url
    return ChatJobQueue(
        settings=mock_settings,
        client=MagicMock() if client is None else client,
    )


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "SendMessage")


class TestEnabled:
    def test_enabled_when_a_queue_is_configured(self):
        assert _make_queue().enabled

    @pytest.mark.parametrize("url", ["", "   "])
    def test_disabled_without_one(self, url):
        """Local dev and CI run turns inline; neither needs a queue to exist."""
        assert not _make_queue(queue_url=url).enabled


class TestPublish:
    async def test_returns_the_message_id(self):
        queue = _make_queue()
        queue.client.send_message.return_value = {"MessageId": "msg-1"}
        assert await queue.publish(job_id=uuid4(), session_id=uuid4()) == "msg-1"

    async def test_disabled_queue_publishes_nothing(self):
        queue = _make_queue(queue_url="")
        assert await queue.publish(job_id=uuid4(), session_id=uuid4()) is None
        queue.client.send_message.assert_not_called()

    async def test_groups_by_session_so_turns_stay_ordered(self):
        """Load-bearing: two turns of one session processed concurrently would
        overwrite each other's criteria, and the user would watch an answer vanish.
        Ordering is a queue guarantee, so this assertion is the only thing that would
        notice it being lost."""
        queue = _make_queue()
        queue.client.send_message.return_value = {"MessageId": "msg-1"}
        session_id = uuid4()
        await queue.publish(job_id=uuid4(), session_id=session_id)
        kwargs = queue.client.send_message.call_args.kwargs
        assert kwargs["MessageGroupId"] == str(session_id)

    async def test_deduplicates_on_the_job_id(self):
        """A retried publish inside the dedupe window must not enqueue the turn twice."""
        queue = _make_queue()
        queue.client.send_message.return_value = {"MessageId": "msg-1"}
        job_id = uuid4()
        await queue.publish(job_id=job_id, session_id=uuid4())
        kwargs = queue.client.send_message.call_args.kwargs
        assert kwargs["MessageDeduplicationId"] == str(job_id)

    async def test_body_carries_references_not_the_users_text(self):
        """The row already holds the input; copying it here would duplicate free-text
        personal circumstances into a second store with its own retention."""
        queue = _make_queue()
        queue.client.send_message.return_value = {"MessageId": "msg-1"}
        job_id, session_id = uuid4(), uuid4()
        await queue.publish(job_id=job_id, session_id=session_id)
        body = json.loads(queue.client.send_message.call_args.kwargs["MessageBody"])
        assert body == {"job_id": str(job_id), "session_id": str(session_id)}

    async def test_targets_the_configured_queue(self):
        queue = _make_queue()
        queue.client.send_message.return_value = {"MessageId": "msg-1"}
        await queue.publish(job_id=uuid4(), session_id=uuid4())
        assert queue.client.send_message.call_args.kwargs["QueueUrl"] == _QUEUE_URL

    async def test_client_error_raises_503(self):
        queue = _make_queue()
        queue.client.send_message.side_effect = _client_error(
            "AWS.SimpleQueueService.NonExistentQueue"
        )
        with pytest.raises(HTTPException) as info:
            await queue.publish(job_id=uuid4(), session_id=uuid4())
        assert info.value.status_code == 503

    async def test_transport_failure_raises_503(self):
        queue = _make_queue()
        queue.client.send_message.side_effect = EndpointConnectionError(endpoint_url="https://sqs")
        with pytest.raises(HTTPException) as info:
            await queue.publish(job_id=uuid4(), session_id=uuid4())
        assert info.value.status_code == 503

    async def test_missing_message_id_is_tolerated(self):
        queue = _make_queue()
        queue.client.send_message.return_value = {}
        assert await queue.publish(job_id=uuid4(), session_id=uuid4()) is None


class TestLazyClient:
    async def test_a_disabled_queue_never_builds_a_client(self):
        """boto3 raises on a blank region, so CI must not construct one."""
        queue = _make_queue(queue_url="", client=None)
        queue._client = None
        await queue.publish(job_id=uuid4(), session_id=uuid4())
        assert queue._client is None
