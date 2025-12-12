"""
Article data models
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import Field

from sag.models.base import SAGBaseModel, MetadataMixin, TimestampMixin


class ArticleStatus(str, Enum):
    """Article status"""

    PENDING = "PENDING"  # Pending
    COMPLETED = "COMPLETED"  # Completed
    FAILED = "FAILED"  # Failed


class Article(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Article model"""

    id: Optional[str] = Field(default=None, description="Article ID (UUID)")
    source_config_id: str = Field(..., description="Source ID")
    title: str = Field(..., max_length=500, description="Article title")
    summary: Optional[str] = Field(default=None, description="Article summary (LLM generated)")
    content: Optional[str] = Field(default=None, description="Article body")
    status: ArticleStatus = Field(
        default=ArticleStatus.PENDING, description="Processing status")
    category: Optional[str] = Field(
        default=None, max_length=50, description="Category")
    tags: Optional[List[str]] = Field(default=None, description="Tag list")

    def get_category(self) -> Optional[str]:
        """Get article category"""
        if self.extra_data and "category" in self.extra_data:
            return self.extra_data["category"]
        return self.category

    def get_tags(self) -> List[str]:
        """Get article tags"""
        if self.tags:
            return self.tags
        if self.extra_data and "tags" in self.extra_data:
            return self.extra_data["tags"]
        return []

    def get_headings(self) -> List[str]:
        """Get article heading list"""
        if self.extra_data and "headings" in self.extra_data:
            return self.extra_data["headings"]
        return []


class ArticleSection(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Article section model"""

    id: Optional[str] = Field(default=None, description="Section ID (UUID)")
    article_id: str = Field(..., description="Article ID")
    rank: int = Field(..., ge=0, description="Section sequence number (starting from 0)")
    heading: str = Field(..., max_length=500, description="Heading/subheading")
    content: str = Field(..., description="Content (plain text)")

    def get_type(self) -> str:
        """Get section type"""
        if self.extra_data and "type" in self.extra_data:
            return self.extra_data["type"]
        return "TEXT"

    def get_length(self) -> int:
        """Get content length"""
        if self.extra_data and "length" in self.extra_data:
            return self.extra_data["length"]
        return len(self.content)


class ArticleCreate(SAGBaseModel):
    """Create article request"""

    source_config_id: str = Field(..., description="Source ID")
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    content: Optional[str] = Field(default=None, description="Article body")
    summary: Optional[str] = Field(default=None, description="Article summary")
    category: Optional[str] = Field(default=None, description="Category")
    tags: Optional[List[str]] = Field(default=None, description="Tags")
    extra_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Extended data")
