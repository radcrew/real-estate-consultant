"""SQS publisher for queued intake turns.

The queue carries **references, not content**: a message is just the job id and its
session. The row written before the publish already holds the user's text, so putting it
in the body too would copy free-text personal circumstances into a second store with its
own retention — for no gain, since the consumer has to load the row regardless.

An empty ``SQS_CHAT_QUEUE_URL`` disables publishing, which is how local development and
the test suite run the turn inline without anyone standing up a queue.
"""

from __future__ import annotations

import json
import logging
from functools import partial
from typing import Any
from uuid import UUID

import anyio.to_thread
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings, settings
from app.utils.exceptions import raise_service_unavailable

SQS_CONNECT_TIMEOUT = 10.0
SQS_READ_TIMEOUT = 15.0
SQS_TRANSIENT_RETRIES = 3

logger = logging.getLogger(__name__)


class ChatJobQueue:
    """Publishes one message per intake turn onto the FIFO queue."""

    def __init__(self, *, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def enabled(self) -> bool:
        """Whether turns are dispatched to the queue rather than run inline."""
        return bool(self.settings.sqs_chat_queue_url.strip())

    @property
    def client(self) -> Any:
        """Build the boto3 client on first use.

        boto3 raises on a blank region, so an eagerly-built module-level client would
        fail at import wherever ``AWS_REGION`` is unset — including CI, which never
        publishes anything.
        """
        if self._client is None:
            self._client = boto3.client(
                "sqs",
                region_name=self.settings.aws_region,
                config=Config(
                    connect_timeout=SQS_CONNECT_TIMEOUT,
                    read_timeout=SQS_READ_TIMEOUT,
                    retries={"max_attempts": SQS_TRANSIENT_RETRIES, "mode": "standard"},
                ),
            )
        return self._client

    def _send(self, *, job_id: UUID, session_id: UUID) -> dict[str, Any]:
        """Blocking ``SendMessage`` — always run via ``anyio.to_thread``."""
        return self.client.send_message(
            QueueUrl=self.settings.sqs_chat_queue_url,
            MessageBody=json.dumps({"job_id": str(job_id), "session_id": str(session_id)}),
            # Ordering is guaranteed within a group, and groups run in parallel. Grouping
            # by session is what stops two turns of one conversation from being processed
            # concurrently and overwriting each other's extracted criteria — the user
            # answers a question and watches the answer disappear.
            MessageGroupId=str(session_id),
            # A publish retried inside the 5-minute dedupe window is a no-op rather than
            # a second copy of the same turn.
            MessageDeduplicationId=str(job_id),
        )

    async def publish(self, *, job_id: UUID, session_id: UUID) -> str | None:
        """Enqueue one turn. Returns the SQS message id.

        A failure here leaves the job row ``queued`` on purpose: the row is visible and
        can be redriven, whereas deleting it would discard the user's text — the very
        thing the queue exists to protect.
        """
        if not self.enabled:
            return None
        try:
            response = await anyio.to_thread.run_sync(
                partial(self._send, job_id=job_id, session_id=session_id)
            )
        except (ClientError, BotoCoreError) as exc:
            logger.warning(
                "chat_job_publish_failed",
                extra={"job_id": str(job_id), "session_id": str(session_id)},
            )
            raise_service_unavailable(
                "We couldn't queue your message. Please try again in a moment.",
                cause=exc,
            )
        message_id = response.get("MessageId") if isinstance(response, dict) else None
        logger.info(
            "chat_job_published",
            extra={
                "job_id": str(job_id),
                "session_id": str(session_id),
                "message_id": message_id,
            },
        )
        return message_id


chat_job_queue = ChatJobQueue(settings=settings)
