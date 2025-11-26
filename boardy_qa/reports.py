"""Report generation for Boardy QA."""

from typing import List
from datetime import datetime

from .models import ConversationAnalysis, ReportStats


class ReportGenerator:
    """Generate reports from conversation analyses."""
    
    def generate_markdown_report(self, analyses: List[ConversationAnalysis], stats: ReportStats) -> str:
        """Generate a Markdown report."""
        lines = []
        
        # Header
        lines.append("# Boardy QA Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Conversations:** {stats.total_conversations}")
        lines.append(f"- **Total Messages:** {stats.total_messages}")
        lines.append(f"- **User Messages:** {stats.user_messages}")
        lines.append(f"- **Assistant Messages:** {stats.assistant_messages}")
        lines.append(f"- **Total Failures:** {stats.total_failures}")
        lines.append(f"- **High Severity:** {stats.high_severity_failures}")
        lines.append(f"- **Medium Severity:** {stats.medium_severity_failures}")
        lines.append(f"- **Low Severity:** {stats.low_severity_failures}")
        lines.append(f"- **Failure Rate:** {stats.failure_rate:.1%}")
        lines.append("")
        
        # Failure breakdown by rule
        lines.append("## Failures by Rule")
        lines.append("")
        rule_failures = {}
        for analysis in analyses:
            for failure in analysis.get_failures():
                rule_name = failure.rule_name
                if rule_name not in rule_failures:
                    rule_failures[rule_name] = []
                rule_failures[rule_name].append(failure)
        
        if rule_failures:
            for rule_name, failures in sorted(rule_failures.items()):
                lines.append(f"### {rule_name}")
                lines.append(f"**Count:** {len(failures)}")
                lines.append("")
                
                # Show severity breakdown
                severity_counts = {}
                for failure in failures:
                    severity = failure.severity
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                for severity in ['high', 'medium', 'low']:
                    count = severity_counts.get(severity, 0)
                    if count > 0:
                        lines.append(f"- {severity.capitalize()}: {count}")
                lines.append("")
                
                # Show first few failures as examples
                for i, failure in enumerate(failures[:3]):
                    lines.append(f"**{i+1}.** {failure.message}")
                    if failure.details:
                        lines.append(f"   - Details: {self._format_details(failure.details)}")
                    lines.append("")
                
                if len(failures) > 3:
                    lines.append(f"... and {len(failures) - 3} more")
                    lines.append("")
        else:
            lines.append("✅ No failures found!")
            lines.append("")
        
        # Conversation details
        lines.append("## Conversation Details")
        lines.append("")
        
        for analysis in analyses:
            conversation_id = analysis.conversation_id or "Unknown"
            failures = analysis.get_failures()
            
            lines.append(f"### Conversation: {conversation_id}")
            lines.append(f"- **Messages:** {analysis.stats.get('total_messages', 0)}")
            lines.append(f"- **Failures:** {len(failures)}")
            
            if failures:
                lines.append("")
                lines.append("**Issues:**")
                for failure in failures:
                    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(failure.severity, "⚪")
                    lines.append(f"- {severity_emoji} **{failure.rule_name}:** {failure.message}")
            else:
                lines.append("- ✅ No issues")
            
            lines.append("")
        
        return "\\n".join(lines)
    
    def generate_html_report(self, analyses: List[ConversationAnalysis], stats: ReportStats) -> str:
        """Generate an HTML report."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boardy QA Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            border-bottom: 2px solid #e1e5e9;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .metric {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2563eb;
        }}
        .metric-label {{
            color: #6b7280;
            font-size: 0.9em;
        }}
        .failure-high {{ color: #dc2626; }}
        .failure-medium {{ color: #f59e0b; }}
        .failure-low {{ color: #10b981; }}
        .conversation {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .conversation-header {{
            background: #f9fafb;
            padding: 15px;
            border-bottom: 1px solid #e5e7eb;
            font-weight: bold;
        }}
        .conversation-body {{
            padding: 15px;
        }}
        .failure-item {{
            margin: 10px 0;
            padding: 10px;
            border-left: 4px solid;
            background: #f9fafb;
        }}
        .failure-high {{ border-color: #dc2626; }}
        .failure-medium {{ border-color: #f59e0b; }}
        .failure-low {{ border-color: #10b981; }}
        .rule-section {{
            margin-bottom: 30px;
        }}
        .rule-header {{
            background: #f3f4f6;
            padding: 15px;
            border-radius: 6px;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        .details {{
            font-size: 0.9em;
            color: #6b7280;
            margin-top: 5px;
        }}
        .severity-badge {{
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            color: white;
        }}
        .severity-high {{ background: #dc2626; }}
        .severity-medium {{ background: #f59e0b; }}
        .severity-low {{ background: #10b981; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Boardy QA Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="metric">
                <div class="metric-value">{stats.total_conversations}</div>
                <div class="metric-label">Total Conversations</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.total_messages}</div>
                <div class="metric-label">Total Messages</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.total_failures}</div>
                <div class="metric-label">Total Failures</div>
            </div>
            <div class="metric">
                <div class="metric-value">{stats.failure_rate:.1%}</div>
                <div class="metric-label">Failure Rate</div>
            </div>
        </div>
        <div class="summary-grid" style="margin-top: 15px;">
            <div class="metric">
                <div class="metric-value failure-high">{stats.high_severity_failures}</div>
                <div class="metric-label">High Severity</div>
            </div>
            <div class="metric">
                <div class="metric-value failure-medium">{stats.medium_severity_failures}</div>
                <div class="metric-label">Medium Severity</div>
            </div>
            <div class="metric">
                <div class="metric-value failure-low">{stats.low_severity_failures}</div>
                <div class="metric-label">Low Severity</div>
            </div>
        </div>
    </div>

    {self._generate_rule_sections_html(analyses)}

    <h2>Conversation Details</h2>
    {self._generate_conversation_sections_html(analyses)}
</body>
</html>
        """
    
    def _generate_rule_sections_html(self, analyses: List[ConversationAnalysis]) -> str:
        """Generate HTML sections for rule failures."""
        rule_failures = {}
        for analysis in analyses:
            for failure in analysis.get_failures():
                rule_name = failure.rule_name
                if rule_name not in rule_failures:
                    rule_failures[rule_name] = []
                rule_failures[rule_name].append(failure)
        
        if not rule_failures:
            return '<div class="rule-section"><div class="rule-header">✅ No failures found!</div></div>'
        
        sections = ""
        for rule_name, failures in sorted(rule_failures.items()):
            section = f'<div class="rule-section"><div class="rule-header">{rule_name} ({len(failures)} failures)</div>'
            
            for failure in failures[:5]:  # Show first 5 failures
                section += f'''
                <div class="failure-item failure-{failure.severity}">
                    <div>{failure.message}</div>
                    <div class="details">{self._format_details(failure.details)}</div>
                </div>
                '''
            
            if len(failures) > 5:
                section += f"<p>... and {len(failures) - 5} more</p>"
            
            section += "</div>"
            sections += section
        
        return sections
    
    def _generate_conversation_sections_html(self, analyses: List[ConversationAnalysis]) -> str:
        """Generate HTML sections for conversation details."""
        sections = ""
        
        for analysis in analyses:
            conversation_id = analysis.conversation_id or "Unknown"
            failures = analysis.get_failures()
            
            section = f'''
            <div class="conversation">
                <div class="conversation-header">
                    Conversation: {conversation_id}
                    <span style="float: right;">
                        {analysis.stats.get('total_messages', 0)} messages | 
                        {len(failures)} failures
                    </span>
                </div>
                <div class="conversation-body">
            '''
            
            if failures:
                for failure in failures:
                    section += f'''
                    <div class="failure-item failure-{failure.severity}">
                        <span class="severity-badge severity-{failure.severity}">{failure.severity.upper()}</span>
                        <strong>{failure.rule_name}:</strong> {failure.message}
                        <div class="details">{self._format_details(failure.details)}</div>
                    </div>
                    '''
            else:
                section += "<p>✅ No issues found</p>"
            
            section += "</div></div>"
            sections += section
        
        return sections
    
    def _format_details(self, details: dict) -> str:
        """Format details for display."""
        if not details:
            return ""
        
        formatted_parts = []
        for key, value in details.items():
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            formatted_parts.append(f"{key}: {value}")
        
        return " | ".join(formatted_parts)
