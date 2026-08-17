# chat-intake-worker: runs queued intake turns off chat-intake.fifo.
#
# Build from the backend directory, which is the context:
#   docker build -f infra/chat-intake-worker/Dockerfile -t chat-intake-worker backend
#
# The whole app package ships, not a curated subset. The worker calls the same services,
# repositories and providers the API does, and a hand-picked file list would be a second
# thing to keep in step — the drift §14.1 warns about. Image size is not the constraint
# here; a turn that behaves differently on the worker than inline would be.
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY app/ ${LAMBDA_TASK_ROOT}/app/

CMD ["app.workers.chat_job_worker.handler"]
