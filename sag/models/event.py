"""
Event data models
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from sag.models.base import SAGBaseModel, MetadataMixin, TimestampMixin


class EventCategory(str, Enum):
    """Event category"""

    TECHNICAL = "TECHNICAL"  # Technical
    BUSINESS = "BUSINESS"  # Business
    PERSONAL = "PERSONAL"  # Personal
    OTHER = "OTHER"  # Other


class EventPriority(str, Enum):
    """Priority"""

    HIGH = "HIGH"  # High
    MEDIUM = "MEDIUM"  # Medium
    LOW = "LOW"  # Low


class EventStatus(str, Enum):
    """Event status"""

    TODO = "TODO"  # Todo
    IN_PROGRESS = "IN_PROGRESS"  # In progress
    DONE = "DONE"  # Done
    UNKNOWN = "UNKNOWN"  # Unknown


class SourceEvent(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Source event model"""

    id: str = Field(..., description="Event ID (UUID)")
    source_config_id: str = Field(..., description="Source configuration ID")
    article_id: str = Field(..., description="Article ID")
    title: str = Field(..., min_length=1, max_length=255, description="Title")
    summary: str = Field(..., description="Summary")
    content: str = Field(..., description="Content (event body)")
    category: Optional[str] = Field(default="", max_length=50, description="Event category (technical, product, market, research, management, etc.)")
    rank: int = Field(default=0, ge=0, description="Event sequence number (sorted within same source, starting from 0)")
    start_time: Optional[datetime] = Field(default=None, description="Start time")
    end_time: Optional[datetime] = Field(default=None, description="End time")
    references: Optional[List[str]] = Field(default=None, description="Original fragment references (copied from SourceChunk.references)")
    chunk_id: Optional[str] = Field(default=None, description="Source chunk ID (points to SourceChunk)")

    def get_category(self) -> Optional[str]:
        """Get category"""
        if self.extra_data and "category" in self.extra_data:
            return self.extra_data["category"]
        return None

    def get_priority(self) -> Optional[str]:
        """Get priority"""
        if self.extra_data and "priority" in self.extra_data:
            return self.extra_data["priority"]
        return None

    def get_status(self) -> Optional[str]:
        """Get status"""
        if self.extra_data and "status" in self.extra_data:
            return self.extra_data["status"]
        return None

    def get_keywords(self) -> List[str]:
        """Get keywords"""
        if self.extra_data and "keywords" in self.extra_data:
            return self.extra_data["keywords"]
        return []

    def get_tags(self) -> List[str]:
        """Get tags"""
        if self.extra_data and "tags" in self.extra_data:
            return self.extra_data["tags"]
        return []

    def get_references(self) -> List[str]:
        """Get original fragment references"""
        if self.references:
            return self.references
        return []


class EventWithEntities(SAGBaseModel):
    """Event model with entities (for search results)"""

    event: SourceEvent
    entities: List[Dict[str, Any]] = Field(
        ...,
        description="Entity list: [{type, name, weight, ...}]"
    )
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="相关度分数")

    def get_entities_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """按类型获取实体"""
        return [e for e in self.entities if e.get("type") == entity_type]

    def get_entity_names_by_type(self, entity_type: str) -> List[str]:
        """按类型获取实体名称列表"""
        return [e.get("name", "") for e in self.entities if e.get("type") == entity_type]
