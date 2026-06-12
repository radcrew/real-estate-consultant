from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.properties import Properties


class ListingDetailResponse(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    property: Properties
    images: list[str]


class ListingSubmissionCreate(BaseModel):
    """A property listing submitted via the public 'list your property' form."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property_type: str = Field(min_length=1, max_length=120)
    listing_type: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=5000)
    address: str | None = Field(default=None, max_length=500)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    size_sqft: float | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)
    clear_height: float | None = Field(default=None, ge=0)
    loading_docks: int | None = Field(default=None, ge=0)
    contact_name: str = Field(min_length=1, max_length=200)
    contact_email: EmailStr


class ListingSubmissionResponse(BaseModel):
    id: str
    status: str


class ListingSubmissionItem(BaseModel):
    """Admin view of a submitted listing (extra DB columns ignored)."""

    model_config = ConfigDict(extra="ignore")

    id: str
    status: str
    property_type: str | None = None
    listing_type: str | None = None
    title: str | None = None
    city: str | None = None
    state: str | None = None
    size_sqft: float | None = None
    price: float | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    created_at: str | None = None


class ListingSubmissionStatusUpdate(BaseModel):
    status: Literal["pending", "approved", "rejected"]


class AgentProfileResponse(BaseModel):
    """A listing broker/agent and the properties they have listed."""

    name: str
    email: str | None = None
    phone: str | None = None
    properties: list[Properties]
