"""
User data models
"""

from typing import Any, Dict, List, Optional

from pydantic import EmailStr, Field

from sag.models.base import SAGBaseModel, MetadataMixin, TimestampMixin


class UserPreferences(SAGBaseModel):
    """User preference settings"""

    focus: List[str] = Field(default_factory=list, description="Focus areas")
    language: str = Field(default="zh", description="Language preference")
    # entity_weights: Optional[Dict[str, float]] = Field(
    #     default=None, description="Custom entity weights"
    # )


class User(SAGBaseModel, MetadataMixin, TimestampMixin):
    """User model"""

    id: str = Field(..., description="User ID (UUID)")
    username: str = Field(..., min_length=1, max_length=100, description="Username")
    email: Optional[EmailStr] = Field(default=None, description="Email")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences")

    def get_focus(self) -> List[str]:
        """Get focus areas"""
        if self.preferences and "focus" in self.preferences:
            return self.preferences["focus"]
        return []

    def get_language(self) -> str:
        """Get language preference"""
        if self.preferences and "language" in self.preferences:
            return self.preferences["language"]
        return "zh"


class UserCreate(SAGBaseModel):
    """Create user request"""

    username: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None


class UserUpdate(SAGBaseModel):
    """Update user request"""

    username: Optional[str] = Field(default=None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    preferences: Optional[Dict[str, Any]] = None
