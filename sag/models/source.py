"""
Source configuration data models
"""

from typing import Any, Dict, List, Optional

from pydantic import Field

from sag.models.base import SAGBaseModel, MetadataMixin, TimestampMixin


class SourceConfig(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Source configuration model"""

    id: str = Field(..., description="Source configuration ID (UUID)")
    name: str = Field(..., min_length=1, max_length=100, description="Source configuration name")
    description: Optional[str] = Field(
        default=None, max_length=255, description="Source configuration description"
    )
    config: Optional[Dict[str, Any]] = Field(
        default=None, description='Preference settings, format: {"focus": ["AI"], "language": "zh"}'
    )

    def get_focus(self) -> List[str]:
        """Get focus areas"""
        if self.config and "focus" in self.config:
            return self.config["focus"]
        return []

    def get_language(self) -> str:
        """Get language preference"""
        if self.config and "language" in self.config:
            return self.config["language"]
        return "zh"


class SourceConfigCreate(SAGBaseModel):
    """Create source configuration request"""

    name: str = Field(..., min_length=1, max_length=100, description="Source configuration name")
    description: Optional[str] = Field(default=None, max_length=255, description="Source configuration description")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Preference settings")


class SourceConfigUpdate(SAGBaseModel):
    """Update source configuration request"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Source configuration name")
    description: Optional[str] = Field(default=None, max_length=255, description="Source configuration description")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Preference settings")
