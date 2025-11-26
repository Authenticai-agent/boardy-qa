"""Tests for the rule engine."""

import pytest
from datetime import datetime

from boardy_qa.models import Message, Conversation
from boardy_qa.engine import RuleEngine
from boardy_qa.rules import LengthRule, StyleRule


class TestRuleEngine:
    """Test the RuleEngine."""
    
    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = RuleEngine()
        assert len(engine.rule_classes) == 5  # 5 default rules
        assert len(engine.rules) == 0  # No rules configured yet
    
    def test_add_rule(self):
        """Test adding a rule to the engine."""
        engine = RuleEngine()
        engine.add_rule(LengthRule, {"max_length_chars": 100})
        
        assert len(engine.rules) == 1
        assert isinstance(engine.rules[0], LengthRule)
        assert engine.rules[0].config["max_length_chars"] == 100
    
    def test_add_rule_by_name(self):
        """Test adding a rule by name."""
        engine = RuleEngine()
        engine.add_rule_by_name("LengthRule", {"max_length_chars": 50})
        
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "LengthRule"
        assert engine.rules[0].config["max_length_chars"] == 50
    
    def test_add_unknown_rule_fails(self):
        """Test that adding an unknown rule fails."""
        engine = RuleEngine()
        with pytest.raises(ValueError, match="Unknown rule"):
            engine.add_rule_by_name("UnknownRule")
    
    def test_configure_rules(self):
        """Test configuring multiple rules."""
        engine = RuleEngine()
        rules_config = [
            {
                "name": "LengthRule",
                "enabled": True,
                "config": {"max_length_chars": 200}
            },
            {
                "name": "StyleRule", 
                "enabled": True,
                "config": {"max_exclamation_marks": 5}
            },
            {
                "name": "QuestionFollowupRule",
                "enabled": False
            }
        ]
        
        engine.configure_rules(rules_config)
        
        assert len(engine.rules) == 2  # Only enabled rules
        assert engine.rules[0].name == "LengthRule"
        assert engine.rules[1].name == "StyleRule"
    
    def test_analyze_conversation(self):
        """Test analyzing a single conversation."""
        engine = RuleEngine()
        engine.add_rule(LengthRule, {"max_length_chars": 50})
        
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a short message.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            ),
            Message(
                id="msg_2",
                timestamp=datetime.now(),
                role="assistant",
                text="This is a very long message that exceeds the maximum length limit and should definitely fail the rule check.",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        analysis = engine.analyze_conversation(conversation)
        
        assert analysis.conversation_id == "conv_1"
        assert len(analysis.rule_results) == 1
        assert analysis.rule_results[0].rule_name == "LengthRule"
        assert analysis.rule_results[0].status == "fail"
        assert analysis.stats["total_messages"] == 2
        assert analysis.stats["assistant_messages"] == 2
        assert analysis.stats["total_failures"] == 1
    
    def test_analyze_conversations(self):
        """Test analyzing multiple conversations."""
        engine = RuleEngine()
        engine.add_rule(LengthRule, {"max_length_chars": 50})
        
        conversations = [
            Conversation(messages=[
                Message(
                    id="msg_1",
                    timestamp=datetime.now(),
                    role="assistant",
                    text="Short message.",
                    meta={"channel": "web", "conversation_id": "conv_1"}
                )
            ]),
            Conversation(messages=[
                Message(
                    id="msg_2",
                    timestamp=datetime.now(),
                    role="assistant",
                    text="This is a very long message that exceeds the maximum length limit.",
                    meta={"channel": "web", "conversation_id": "conv_2"}
                )
            ])
        ]
        
        analyses = engine.analyze_conversations(conversations)
        
        assert len(analyses) == 2
        assert analyses[0].conversation_id == "conv_1"
        assert analyses[1].conversation_id == "conv_2"
        assert analyses[0].stats["total_failures"] == 0
        assert analyses[1].stats["total_failures"] == 1
    
    def test_generate_report_stats(self):
        """Test generating overall statistics."""
        engine = RuleEngine()
        engine.add_rule(LengthRule, {"max_length_chars": 50})
        
        # Create mock analyses
        from boardy_qa.models import ConversationAnalysis, RuleResult
        
        analyses = [
            ConversationAnalysis(
                conversation_id="conv_1",
                rule_results=[
                    RuleResult(
                        rule_name="LengthRule",
                        status="pass",
                        message="All good",
                        severity="low"
                    )
                ],
                stats={"total_messages": 2, "user_messages": 1, "assistant_messages": 1}
            ),
            ConversationAnalysis(
                conversation_id="conv_2", 
                rule_results=[
                    RuleResult(
                        rule_name="LengthRule",
                        status="fail",
                        message="Too long",
                        severity="medium"
                    )
                ],
                stats={"total_messages": 1, "user_messages": 0, "assistant_messages": 1}
            )
        ]
        
        stats = engine.generate_report_stats(analyses)
        
        assert stats.total_conversations == 2
        assert stats.total_messages == 3
        assert stats.user_messages == 1
        assert stats.assistant_messages == 2
        assert stats.total_failures == 1
        assert stats.medium_severity_failures == 1
        assert stats.rules_run == 1
        assert stats.failure_rate == 0.5  # 1 failure out of 2 results
    
    def test_rule_execution_error_handling(self):
        """Test that rule execution errors are handled gracefully."""
        class BrokenRule:
            def __init__(self, config=None):
                self.config = config or {}
                self.name = "BrokenRule"
            
            def evaluate(self, conversation):
                raise Exception("Something went wrong")
        
        engine = RuleEngine()
        engine.add_rule(BrokenRule)
        
        conversation = Conversation(messages=[
            Message(
                id="msg_1",
                timestamp=datetime.now(),
                role="user",
                text="Hello!",
                meta={"channel": "web", "conversation_id": "conv_1"}
            )
        ])
        
        analysis = engine.analyze_conversation(conversation)
        
        assert len(analysis.rule_results) == 1
        assert analysis.rule_results[0].rule_name == "BrokenRule"
        assert analysis.rule_results[0].status == "fail"
        assert "execution error" in analysis.rule_results[0].message.lower()
        assert analysis.rule_results[0].severity == "high"


if __name__ == "__main__":
    pytest.main([__file__])
