"""Rule engine for conversation analysis."""

from typing import List, Dict, Any, Type
import importlib

from .models import Conversation, ConversationAnalysis, RuleResult, ReportStats
from .rules import BaseRule


class RuleEngine:
    """Engine for running QA rules on conversations."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.rules: List[BaseRule] = []
        self.rule_classes: Dict[str, Type[BaseRule]] = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default rule classes."""
        from .rules import (
            LengthRule, QuestionFollowupRule, StyleRule, 
            TurnEndingRule, ConversationHealthRule
        )
        
        self.rule_classes = {
            'LengthRule': LengthRule,
            'QuestionFollowupRule': QuestionFollowupRule,
            'StyleRule': StyleRule,
            'TurnEndingRule': TurnEndingRule,
            'ConversationHealthRule': ConversationHealthRule
        }
    
    def add_rule(self, rule_class: Type[BaseRule], config: Dict[str, Any] = None):
        """Add a rule to the engine."""
        rule = rule_class(config or {})
        self.rules.append(rule)
    
    def add_rule_by_name(self, rule_name: str, config: Dict[str, Any] = None):
        """Add a rule by name."""
        if rule_name not in self.rule_classes:
            raise ValueError(f"Unknown rule: {rule_name}")
        
        rule_class = self.rule_classes[rule_name]
        self.add_rule(rule_class, config)
    
    def configure_rules(self, rules_config: List[Dict[str, Any]]):
        """Configure rules from a list of rule configurations."""
        self.rules.clear()
        
        for rule_config in rules_config:
            rule_name = rule_config.get('name')
            rule_config_data = rule_config.get('config', {})
            enabled = rule_config.get('enabled', True)
            
            if enabled and rule_name in self.rule_classes:
                self.add_rule_by_name(rule_name, rule_config_data)
    
    def analyze_conversation(self, conversation: Conversation) -> ConversationAnalysis:
        """Analyze a single conversation."""
        analysis = ConversationAnalysis(
            conversation_id=conversation.get_conversation_id()
        )
        
        all_results = []
        
        for rule in self.rules:
            try:
                rule_results = rule.evaluate(conversation)
                all_results.extend(rule_results)
            except Exception as e:
                # Add a failure result for the rule itself
                all_results.append(RuleResult(
                    rule_name=rule.name,
                    status="fail",
                    message=f"Rule execution error: {str(e)}",
                    details={"error": str(e)},
                    severity="high"
                ))
        
        analysis.rule_results = all_results
        
        # Calculate stats for this conversation
        analysis.stats = {
            'total_messages': len(conversation.messages),
            'user_messages': len(conversation.get_messages_by_role('user')),
            'assistant_messages': len(conversation.get_messages_by_role('assistant')),
            'total_failures': len(analysis.get_failures()),
            'high_severity_failures': len(analysis.get_failures_by_severity('high')),
            'medium_severity_failures': len(analysis.get_failures_by_severity('medium')),
            'low_severity_failures': len(analysis.get_failures_by_severity('low')),
            'failure_rate': len(analysis.get_failures()) / len(all_results) if all_results else 0.0
        }
        
        return analysis
    
    def analyze_conversations(self, conversations: List[Conversation]) -> List[ConversationAnalysis]:
        """Analyze multiple conversations."""
        return [self.analyze_conversation(conv) for conv in conversations]
    
    def generate_report_stats(self, analyses: List[ConversationAnalysis]) -> ReportStats:
        """Generate overall statistics from multiple analyses."""
        stats = ReportStats()
        
        total_rule_results = 0
        total_failures = 0
        
        for analysis in analyses:
            stats.total_conversations += 1
            stats.total_messages += analysis.stats.get('total_messages', 0)
            stats.user_messages += analysis.stats.get('user_messages', 0)
            stats.assistant_messages += analysis.stats.get('assistant_messages', 0)
            
            failures = analysis.get_failures()
            total_failures += len(failures)
            total_rule_results += len(analysis.rule_results)
            
            stats.high_severity_failures += len(analysis.get_failures_by_severity('high'))
            stats.medium_severity_failures += len(analysis.get_failures_by_severity('medium'))
            stats.low_severity_failures += len(analysis.get_failures_by_severity('low'))
        
        stats.total_failures = total_failures
        stats.rules_run = len(self.rules)
        stats.failure_rate = total_failures / total_rule_results if total_rule_results > 0 else 0.0
        
        return stats
