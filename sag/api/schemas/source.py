"""Source configuration Schema"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from sag.api.schemas.base import TimestampMixin


class SourceConfigCreateRequest(BaseModel):
    """Create source configuration request"""

    name: str = Field(..., min_length=1, max_length=100, description="Source configuration name")
    description: Optional[str] = Field(
        default=None, max_length=255, description="Source configuration description"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None,
        description='Preference settings, format: {"focus": ["AI"], "language": "zh"}',
    )


class SourceConfigUpdateRequest(BaseModel):
    """Update source configuration request"""

    name: Optional[str] = Field(
        default=None, min_length=1, max_length=100, description="Source configuration name"
    )
    description: Optional[str] = Field(
        default=None, max_length=255, description="Source configuration description"
    )
    config: Optional[Dict[str, Any]] = Field(default=None, description="Preference settings")


class SourceConfigResponse(TimestampMixin):
    """Source configuration response"""

    id: str
    name: str
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    created_time: datetime
    updated_time: Optional[datetime] = None
    document_count: int = Field(default=0, description="Document count")
    entity_types_count: int = Field(default=0, description="Source-specific entity type count")

    class Config:
        from_attributes = True

