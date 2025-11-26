"""QA rules for conversation analysis."""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set
from collections import defaultdict

from .models import Message, Conversation, RuleResult


class BaseRule(ABC):
    """Base class for all QA rules."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Evaluate the rule against a conversation."""
        pass
    
    def _create_result(self, status: str, message: str, details: Dict[str, Any] = None, severity: str = "medium") -> RuleResult:
        """Create a rule result."""
        return RuleResult(
            rule_name=self.name,
            status=status,
            message=message,
            details=details or {},
            severity=severity
        )


class LengthRule(BaseRule):
    """Check if assistant messages exceed maximum length."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_length_chars = self.config.get('max_length_chars', 1200)
    
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Check length of assistant messages."""
        results = []
        assistant_messages = conversation.get_messages_by_role('assistant')
        
        for msg in assistant_messages:
            length = len(msg.text)
            if length > self.max_length_chars:
                results.append(self._create_result(
                    status="fail",
                    message=f"Assistant message too long: {length} chars (max: {self.max_length_chars})",
                    details={
                        "message_id": msg.id,
                        "actual_length": length,
                        "max_length": self.max_length_chars,
                        "text_preview": msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    },
                    severity="medium"
                ))
        
        if not results:
            results.append(self._create_result(
                status="pass",
                message=f"All assistant messages within length limit ({self.max_length_chars} chars)"
            ))
        
        return results


class QuestionFollowupRule(BaseRule):
    """Ensure assistant responds to user questions."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'must', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its',
            'our', 'their', 'this', 'that', 'these', 'those', 'what', 'when', 'where',
            'why', 'how', 'who', 'which', 'whose', 'if', 'because', 'so', 'then'
        }
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract significant keywords from text."""
        words = re.findall(r'\b\w+\b', text.lower())
        return {word for word in words if word not in self.stopwords and len(word) > 2}
    
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Check if assistant responds to user questions."""
        results = []
        messages = conversation.messages
        
        for i, msg in enumerate(messages):
            if msg.role == 'user' and '?' in msg.text:
                # Find next assistant message
                next_assistant_msg = None
                for j in range(i + 1, len(messages)):
                    if messages[j].role == 'assistant':
                        next_assistant_msg = messages[j]
                        break
                
                if next_assistant_msg:
                    user_keywords = self._extract_keywords(msg.text)
                    assistant_keywords = self._extract_keywords(next_assistant_msg.text)
                    
                    # Check if assistant responds with relevant content
                    has_question = '?' in next_assistant_msg.text
                    has_shared_keywords = len(user_keywords & assistant_keywords) >= 1
                    
                    if not has_question and not has_shared_keywords:
                        results.append(self._create_result(
                            status="fail",
                            message=f"Assistant may not be responding to user question",
                            details={
                                "user_message_id": msg.id,
                                "assistant_message_id": next_assistant_msg.id,
                                "user_question": msg.text,
                                "assistant_response": next_assistant_msg.text[:200] + "..." if len(next_assistant_msg.text) > 200 else next_assistant_msg.text,
                                "user_keywords": list(user_keywords),
                                "assistant_keywords": list(assistant_keywords)
                            },
                            severity="high"
                        ))
        
        if not results:
            results.append(self._create_result(
                status="pass",
                message="All user questions appear to be addressed"
            ))
        
        return results


class StyleRule(BaseRule):
    """Check for style violations in assistant messages."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.forbidden_phrases = self.config.get('forbidden_phrases', [
            'i am an ai', 'as an ai', 'as a language model', 'i cannot',
            'i am not able', 'i am unable', 'i don\'t have', 'i do not have'
        ])
        self.max_exclamation_marks = self.config.get('max_exclamation_marks', 3)
        self.require_capitalization = self.config.get('require_capitalization', True)
    
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Check assistant message style."""
        results = []
        assistant_messages = conversation.get_messages_by_role('assistant')
        
        for msg in assistant_messages:
            text_lower = msg.text.lower()
            
            # Check forbidden phrases
            for phrase in self.forbidden_phrases:
                if phrase in text_lower:
                    results.append(self._create_result(
                        status="fail",
                        message=f"Assistant message contains forbidden phrase: '{phrase}'",
                        details={
                            "message_id": msg.id,
                            "forbidden_phrase": phrase,
                            "text_preview": msg.text[:200] + "..." if len(msg.text) > 200 else msg.text
                        },
                        severity="medium"
                    ))
            
            # Check excessive exclamation marks
            exclamation_count = msg.text.count('!')
            if exclamation_count > self.max_exclamation_marks:
                results.append(self._create_result(
                    status="fail",
                    message=f"Too many exclamation marks: {exclamation_count} (max: {self.max_exclamation_marks})",
                    details={
                        "message_id": msg.id,
                        "exclamation_count": exclamation_count,
                        "max_allowed": self.max_exclamation_marks
                    },
                    severity="low"
                ))
            
            # Check capitalization
            if self.require_capitalization and msg.text and not msg.text[0].isupper():
                results.append(self._create_result(
                    status="fail",
                    message="Assistant message doesn't start with capital letter",
                    details={
                        "message_id": msg.id,
                        "text_start": msg.text[:50]
                    },
                    severity="low"
                ))
        
        if not results:
            results.append(self._create_result(
                status="pass",
                message="All assistant messages follow style guidelines"
            ))
        
        return results


class TurnEndingRule(BaseRule):
    """Check for rambly questions from assistant."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_question_length = self.config.get('max_question_length', 800)
        self.max_question_sentences = self.config.get('max_question_sentences', 5)
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        sentences = re.split(r'[.!?]+', text)
        return len([s.strip() for s in sentences if s.strip()])
    
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Check assistant questions for being too long or complex."""
        results = []
        assistant_messages = conversation.get_messages_by_role('assistant')
        
        for msg in assistant_messages:
            if '?' in msg.text:
                text_length = len(msg.text)
                sentence_count = self._count_sentences(msg.text)
                
                issues = []
                if text_length > self.max_question_length:
                    issues.append(f"too long ({text_length} chars)")
                if sentence_count > self.max_question_sentences:
                    issues.append(f"too many sentences ({sentence_count})")
                
                if issues:
                    results.append(self._create_result(
                        status="fail",
                        message=f"Assistant question is {', '.join(issues)}",
                        details={
                            "message_id": msg.id,
                            "text_length": text_length,
                            "sentence_count": sentence_count,
                            "max_length": self.max_question_length,
                            "max_sentences": self.max_question_sentences,
                            "question_preview": msg.text[:300] + "..." if len(msg.text) > 300 else msg.text
                        },
                        severity="medium"
                    ))
        
        if not results:
            results.append(self._create_result(
                status="pass",
                message="All assistant questions are appropriately concise"
            ))
        
        return results


class ConversationHealthRule(BaseRule):
    """Check overall conversation health."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_consecutive_assistant = self.config.get('max_consecutive_assistant', 3)
        self.max_message_ratio = self.config.get('max_message_ratio', 3.0)
    
    def evaluate(self, conversation: Conversation) -> List[RuleResult]:
        """Check conversation-level health metrics."""
        results = []
        
        user_messages = conversation.get_messages_by_role('user')
        assistant_messages = conversation.get_messages_by_role('assistant')
        
        # Check message balance
        if len(user_messages) == 0:
            results.append(self._create_result(
                status="fail",
                message="Conversation has no user messages",
                details={
                    "user_count": 0,
                    "assistant_count": len(assistant_messages)
                },
                severity="high"
            ))
        else:
            ratio = len(assistant_messages) / len(user_messages)
            if ratio > self.max_message_ratio:
                results.append(self._create_result(
                    status="fail",
                    message=f"Assistant messages ratio too high: {ratio:.1f}:1 (max: {self.max_message_ratio}:1)",
                    details={
                        "user_count": len(user_messages),
                        "assistant_count": len(assistant_messages),
                        "ratio": ratio
                    },
                    severity="medium"
                ))
        
        # Check consecutive assistant messages
        consecutive_count = 0
        max_consecutive = 0
        
        for msg in conversation.messages:
            if msg.role == 'assistant':
                consecutive_count += 1
                max_consecutive = max(max_consecutive, consecutive_count)
            else:
                consecutive_count = 0
        
        if max_consecutive > self.max_consecutive_assistant:
            results.append(self._create_result(
                status="fail",
                message=f"Too many consecutive assistant messages: {max_consecutive} (max: {self.max_consecutive_assistant})",
                details={
                    "max_consecutive": max_consecutive,
                    "max_allowed": self.max_consecutive_assistant
                },
                severity="medium"
            ))
        
        if not results:
            results.append(self._create_result(
                status="pass",
                message="Conversation health metrics are within acceptable ranges"
            ))
        
        return results
