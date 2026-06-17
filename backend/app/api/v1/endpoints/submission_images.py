"""Public image upload for 'list your property' submissions (Supabase Storage)."""

from __future__ import annotations

import logging
import secrets
from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.core.deps import SupabaseSdkDep
from app.schemas.listings import ListingSubmissionImagesResponse
from app.utils.exceptions import raise_bad_gateway, raise_bad_request

logger = logging.getLogger(__name__)

router = APIRouter()

_LISTING_BUCKET = "listing-images"
_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB each
_MAX_IMAGES = 10
_CONTENT_TYPE_EXT: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@router.post("/images", response_model=ListingSubmissionImagesResponse)
async def upload_submission_images(
    client: SupabaseSdkDep,
    files: Annotated[list[UploadFile], File()],
) -> ListingSubmissionImagesResponse:
    """Upload listing photos to Supabase Storage and return their public URLs.

    Public (unauthenticated), matching the listing-submission form. Guarded by
    per-file type/size checks and a max image count to limit abuse.
    """
    if not files:
        raise_bad_request("No images were uploaded.")
    if len(files) > _MAX_IMAGES:
        raise_bad_request(f"You can upload at most {_MAX_IMAGES} images.")

    storage = client.storage.from_(_LISTING_BUCKET)
    urls: list[str] = []

    for file in files:
        content_type = (file.content_type or "").lower()
        ext = _CONTENT_TYPE_EXT.get(content_type)
        if ext is None:
            raise_bad_request("Images must be JPEG, PNG, or WebP.")

        data = await file.read()
        if not data:
            raise_bad_request("One of the uploaded files is empty.")
        if len(data) > _MAX_IMAGE_BYTES:
            raise_bad_request("Each image must be 5 MB or smaller.")

        path = f"{secrets.token_hex(16)}.{ext}"
        try:
            await storage.upload(path, data, {"content-type": content_type})
        except Exception as exc:  # noqa: BLE001 - surface any storage failure as 502
            logger.error("Supabase Storage upload to %r failed: %s", _LISTING_BUCKET, exc)
            raise_bad_gateway("Failed to upload images.", cause=exc)

        public_url = await storage.get_public_url(path)
        if not isinstance(public_url, str) or not public_url:
            raise_bad_gateway("Failed to resolve an image URL.")
        urls.append(public_url)

    return ListingSubmissionImagesResponse(urls=urls)
