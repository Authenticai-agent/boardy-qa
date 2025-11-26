"""Export analysis results for UI consumption."""

import json
from typing import List, Dict, Any
from datetime import datetime

from .models import ConversationAnalysis, ReportStats


def export_for_ui(analyses: List[ConversationAnalysis], stats: ReportStats) -> Dict[str, Any]:
    """Export analysis results in UI-friendly format."""
    
    # Collect rule failures
    rule_failures = {}
    for analysis in analyses:
        for failure in analysis.get_failures():
            rule_name = failure.rule_name
            if rule_name not in rule_failures:
                rule_failures[rule_name] = []
            rule_failures[rule_name].append({
                "rule_name": failure.rule_name,
                "severity": failure.severity,
                "message": failure.message,
                "details": failure.details
            })
    
    # Format conversation data
    conversations = []
    for analysis in analyses:
        conv_data = {
            "conversation_id": analysis.conversation_id or "Unknown",
            "stats": analysis.stats,
            "failures": [
                {
                    "rule_name": failure.rule_name,
                    "severity": failure.severity,
                    "message": failure.message,
                    "details": failure.details
                }
                for failure in analysis.get_failures()
            ]
        }
        conversations.append(conv_data)
    
    return {
        "total_conversations": stats.total_conversations,
        "total_messages": stats.total_messages,
        "user_messages": stats.user_messages,
        "assistant_messages": stats.assistant_messages,
        "total_failures": stats.total_failures,
        "high_severity_failures": stats.high_severity_failures,
        "medium_severity_failures": stats.medium_severity_failures,
        "low_severity_failures": stats.low_severity_failures,
        "failure_rate": stats.failure_rate,
        "rules_run": stats.rules_run,
        "rule_failures": rule_failures,
        "conversations": conversations,
        "generated_at": datetime.now().isoformat()
    }


def save_ui_report(analyses: List[ConversationAnalysis], stats: ReportStats, output_file: str):
    """Save analysis results for UI consumption."""
    ui_data = export_for_ui(analyses, stats)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ui_data, f, indent=2, ensure_ascii=False)
    
    return ui_data
