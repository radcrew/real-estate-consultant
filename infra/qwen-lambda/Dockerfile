# Qwen2.5-0.5B criteria extractor, CPU-only, for AWS Lambda.
#
# Weights ship inside the image: Lambda allows 10 GB, so there is no cold-start download
# and no EFS mount to manage. The image digest is therefore the model version, which
# makes rollback "redeploy the previous tag".
FROM public.ecr.aws/lambda/python:3.12

# llama-cpp-python builds a native extension, so the toolchain has to be present. It is
# only needed for pip install; the runtime image keeps it, which costs image size but
# avoids the complexity of a multi-stage build for a function this small.
RUN dnf install -y gcc gcc-c++ make cmake && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Grammars are compiled from the exported schemas here, not at runtime: a schema the
# image cannot express should fail this build, not the first request that needs it.
COPY schemas/ ${LAMBDA_TASK_ROOT}/schemas/
COPY build_grammars.py ${LAMBDA_TASK_ROOT}/
RUN python ${LAMBDA_TASK_ROOT}/build_grammars.py \
        --schemas ${LAMBDA_TASK_ROOT}/schemas \
        --out ${LAMBDA_TASK_ROOT}/grammars

# Place the GGUF at model/ before building — see README.md.
COPY model/ ${LAMBDA_TASK_ROOT}/model/
COPY handler.py ${LAMBDA_TASK_ROOT}/

ENV MODEL_PATH=${LAMBDA_TASK_ROOT}/model/qwen.gguf \
    GRAMMAR_DIR=${LAMBDA_TASK_ROOT}/grammars

CMD ["handler.handler"]
