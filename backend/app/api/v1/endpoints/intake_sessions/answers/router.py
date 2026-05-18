from fastapi import APIRouter

from . import guided, llm

router = APIRouter(prefix="/{session_id}/answers", tags=["answers"])
router.include_router(guided.router)
router.include_router(llm.router)