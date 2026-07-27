from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AccountProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    avatar_url: str | None = None


class AccountProfileUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    zip_code: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=120)


class AccountPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=72)


class SavedListingsResponse(BaseModel):
    property_ids: list[str]


class SavedListingCreate(BaseModel):
    property_id: UUID


class McpApiKeyCreateRequest(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=120)
    scopes: list[str] | None = Field(
        default=None,
        description="Optional scopes; default ['*']. Allowed: *, mcp:read, mcp:write, mcp:admin",
    )
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        le=3650,
        description="Optional TTL from now; omit for non-expiring keys",
    )


class McpApiKeyCreatedResponse(BaseModel):
    """Returned only from create — includes plaintext ``api_key`` once."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    api_key: str
    scopes: list[str]
    created_at: str | None = None
    expires_at: str | None = None


class McpApiKeyResponse(BaseModel):
    """List/revoke metadata — never includes plaintext or hash."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    created_at: str | None = None
    last_used_at: str | None = None
    revoked_at: str | None = None
    expires_at: str | None = None


class McpApiKeyListResponse(BaseModel):
    keys: list[McpApiKeyResponse]
