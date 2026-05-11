from fastapi import APIRouter

router = APIRouter(tags=["v1"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "pong"}
