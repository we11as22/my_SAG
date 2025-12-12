"""
Chat conversation and message data models
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field

from sag.models.base import SAGBaseModel, MetadataMixin, TimestampMixin


class MessageType(str, Enum):
    """Message type"""

    TEXT = "TEXT"  # Text message
    IMAGE = "IMAGE"  # Image message
    FILE = "FILE"  # File message
    SYSTEM = "SYSTEM"  # System message


class SenderRole(str, Enum):
    """Sender role"""

    USER = "USER"  # User
    ASSISTANT = "ASSISTANT"  # Assistant/Bot
    SYSTEM = "SYSTEM"  # System


class ChatConversation(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Chat conversation model"""

    id: Optional[str] = Field(default=None, description="Conversation ID (UUID)")
    source_config_id: str = Field(..., description="Source ID")
    title: Optional[str] = Field(
        default=None, max_length=255, description="Conversation title")
    last_message_time: Optional[datetime] = Field(
        default=None, description="Last message time")
    messages_count: int = Field(default=0, description="Message count")


class ChatMessage(SAGBaseModel, MetadataMixin, TimestampMixin):
    """Chat message model"""

    id: Optional[str] = Field(default=None, description="Message ID (UUID)")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(..., description="Message timestamp")
    content: Optional[str] = Field(default=None, description="Message content")
    sender_id: Optional[str] = Field(
        default=None, max_length=100, description="Sender ID")
    sender_name: Optional[str] = Field(
        default=None, max_length=100, description="Sender name")
    sender_avatar: Optional[str] = Field(
        default=None, max_length=255, description="Sender avatar URL")
    sender_title: Optional[str] = Field(
        default=None, max_length=50, description="Sender title")
    type: MessageType = Field(default=MessageType.TEXT, description="Message type")
    sender_role: SenderRole = Field(
        default=SenderRole.USER, description="Sender role")
