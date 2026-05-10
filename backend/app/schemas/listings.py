from pydantic import BaseModel, ConfigDict

from app.models.properties import Properties


class ListingDetailResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    property: Properties
    images: list[str]
