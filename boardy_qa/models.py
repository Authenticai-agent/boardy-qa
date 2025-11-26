"""Data models for Boardy QA."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator


class MessageMeta(BaseModel):
    """Metadata for a message."""
    channel: str = Field(..., description="Channel: whatsapp, sms, web")
    conversation_id: str = Field(..., description="Conversation identifier")

    @validator('channel')
    @classmethod
    def validate_channel(cls, v):
        if v not in ['whatsapp', 'sms', 'web']:
            raise ValueError('Channel must be one of: whatsapp, sms, web')
        return v


class Message(BaseModel):
    """A single message in the conversation log."""
    id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(..., description="ISO8601 timestamp")
    role: str = Field(..., description="Role: user or assistant")
    text: str = Field(..., description="Message text content")
    meta: MessageMeta = Field(..., description="Message metadata")

    @validator('role')
    @classmethod
    def validate_role(cls, v):
        if v not in ['user', 'assistant']:
            raise ValueError('Role must be either "user" or "assistant"')
        return v


class Conversation(BaseModel):
    """A conversation containing multiple messages."""
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    
    def get_messages_by_role(self, role: str) -> List[Message]:
        """Get all messages by a specific role."""
        return [msg for msg in self.messages if msg.role == role]

    def get_conversation_id(self) -> Optional[str]:
        """Get the conversation ID from the first message."""
        if self.messages:
            return self.messages[0].meta.conversation_id
        return None


class RuleResult(BaseModel):
    """Result of applying a rule."""
    rule_name: str = Field(..., description="Name of the rule")
    status: str = Field(..., description="pass or fail")
    message: str = Field(..., description="Human-readable result message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    severity: str = Field(default="medium", description="Severity level: low, medium, high")

    @validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['pass', 'fail']:
            raise ValueError('Status must be either "pass" or "fail"')
        return v

    @validator('severity')
    @classmethod
    def validate_severity(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('Severity must be one of: low, medium, high')
        return v


class ConversationAnalysis(BaseModel):
    """Analysis results for a conversation."""
    conversation_id: Optional[str] = None
    rule_results: List[RuleResult] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)
    
    def get_failures(self) -> List[RuleResult]:
        """Get all failed rule results."""
        return [result for result in self.rule_results if result.status == 'fail']
    
    def get_failures_by_severity(self, severity: str) -> List[RuleResult]:
        """Get failures by severity level."""
        return [result for result in self.get_failures() if result.severity == severity]


class ReportStats(BaseModel):
    """Overall statistics for the QA report."""
    total_conversations: int = 0
    total_messages: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    total_failures: int = 0
    high_severity_failures: int = 0
    medium_severity_failures: int = 0
    low_severity_failures: int = 0
    failure_rate: float = 0.0
    rules_run: int = 0
