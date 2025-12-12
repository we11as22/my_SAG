"""
Data model base classes

Base classes for all Pydantic models
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class SAGBaseModel(BaseModel):
    """SAG base model"""

    model_config = ConfigDict(
        # Allow ORM mode (create from SQLAlchemy objects)
        from_attributes=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Validate assignment
        validate_assignment=True,
        # Populate None default values
        populate_by_name=True,
    )


class TimestampMixin(BaseModel):
    """Timestamp mixin class"""

    created_time: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_time: Optional[datetime] = Field(default=None, description="Update time")

    model_config = ConfigDict(from_attributes=True)


class MetadataMixin(BaseModel):
    """Extended data mixin class"""

    extra_data: Optional[Dict[str, Any]] = Field(default=None, description="Extended data (JSON)")

    model_config = ConfigDict(from_attributes=True)
