"""Tests for QA rules."""

import pytest
from datetime import datetime

from boardy_qa.models import Message, Conversation
from boardy_qa.rules import (
    LengthRule, QuestionFollowupRule, StyleRule, 
    TurnEndingRule, ConversationHealthRule
)


class TestLengthRule:
    """Test the LengthRule."""
    
    def test_short_message_passes(self):
        """Test that short messages pass."""
        rule = LengthRule({"max_length_chars": 100})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a short message.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"
    
    def test_long_message_fails(self):
        """Test that long messages fail."""
        rule = LengthRule({"max_length_chars": 50})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a very long message that exceeds the maximum length limit of fifty characters.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "too long" in results[0].message.lower()
        assert results[0].details["actual_length"] > 50
    
    def test_user_messages_ignored(self):
        """Test that user messages are ignored."""
        rule = LengthRule({"max_length_chars": 10})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="This is a very long user message that should be ignored.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"


class TestQuestionFollowupRule:
    """Test the QuestionFollowupRule."""
    
    def test_question_with_good_response_passes(self):
        """Test that questions with good responses pass."""
        rule = QuestionFollowupRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="What is your return policy?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="Our return policy allows returns within 30 days of purchase.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"
    
    def test_question_with_bad_response_fails(self):
        """Test that questions with bad responses fail."""
        rule = QuestionFollowupRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="What is your return policy?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="I can help you with something else?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "not responding" in results[0].message.lower()
    
    def test_question_with_keyword_match_passes(self):
        """Test that questions with keyword matches pass."""
        rule = QuestionFollowupRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="Tell me about shipping options?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="We offer standard and express shipping for all orders.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"


class TestStyleRule:
    """Test the StyleRule."""
    
    def test_clean_message_passes(self):
        """Test that clean messages pass."""
        rule = StyleRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a clean message with proper formatting.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"
    
    def test_forbidden_phrase_fails(self):
        """Test that forbidden phrases fail."""
        rule = StyleRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="I am an AI assistant and I cannot help with that.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) >= 1
        failure_results = [r for r in results if r.status == "fail"]
        assert any("forbidden phrase" in fr.message.lower() for fr in failure_results)
    
    def test_too_many_exclamation_marks_fails(self):
        """Test that too many exclamation marks fail."""
        rule = StyleRule({"max_exclamation_marks": 2})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is exciting!!! I love helping you!!!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        failure_results = [r for r in results if r.status == "fail"]
        assert any("exclamation" in fr.message.lower() for fr in failure_results)
    
    def test_no_capitalization_fails(self):
        """Test that messages without capitalization fail."""
        rule = StyleRule({"require_capitalization": True})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="this message starts with lowercase.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        failure_results = [r for r in results if r.status == "fail"]
        assert any("capital" in fr.message.lower() for fr in failure_results)


class TestTurnEndingRule:
    """Test the TurnEndingRule."""
    
    def test_short_question_passes(self):
        """Test that short questions pass."""
        rule = TurnEndingRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="How can I help you today?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"
    
    def test_long_question_fails(self):
        """Test that overly long questions fail."""
        rule = TurnEndingRule({"max_question_length": 100})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a very long question that goes on and on and exceeds the maximum length limit for questions because it contains way too many characters and should definitely fail this rule check?" * 2,
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "too long" in results[0].message.lower()
    
    def test_complex_question_fails(self):
        """Test that questions with too many sentences fail."""
        rule = TurnEndingRule({"max_question_sentences": 3})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a complex question. It has multiple sentences. Each sentence adds complexity. This makes it hard to follow. Can you help me understand?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "too many sentences" in results[0].message.lower()
    
    def test_non_question_ignored(self):
        """Test that non-questions are ignored."""
        rule = TurnEndingRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a statement, not a question.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"


class TestConversationHealthRule:
    """Test the ConversationHealthRule."""
    
    def test_balanced_conversation_passes(self):
        """Test that balanced conversations pass."""
        rule = ConversationHealthRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="Hello!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="Hi! How can I help you?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_3",
                timestamp=datetime.now(),
                role="user",
                text="I need help with my order.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_4",
                timestamp=datetime.now(),
                role="assistant",
                text="I'd be happy to help with your order!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "pass"
    
    def test_no_user_messages_fails(self):
        """Test that conversations with no user messages fail."""
        rule = ConversationHealthRule()
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="Welcome to our service!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="How can I help you today?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "no user messages" in results[0].message.lower()
    
    def test_too_many_consecutive_assistant_fails(self):
        """Test that too many consecutive assistant messages fail."""
        rule = ConversationHealthRule({"max_consecutive_assistant": 2})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="Hello!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="Hi there!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_3",
                timestamp=datetime.now(),
                role="assistant",
                text="How can I help you?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_4",
                timestamp=datetime.now(),
                role="assistant",
                text="I'm here to assist!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "consecutive" in results[0].message.lower()
    
    def test_high_assistant_to_user_ratio_fails(self):
        """Test that high assistant-to-user message ratios fail."""
        rule = ConversationHealthRule({"max_message_ratio": 2.0})
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="Help!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="I can help!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_3",
                timestamp=datetime.now(),
                role="assistant",
                text="What do you need?",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_4",
                timestamp=datetime.now(),
                role="assistant",
                text="I'm ready to assist!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        results = rule.evaluate(conversation)
        assert len(results) == 1
        assert results[0].status == "fail"
        assert "ratio" in results[0].message.lower()


if __name__ == "__main__":
    pytest.main([__file__])
