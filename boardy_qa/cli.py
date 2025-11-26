"""Command-line interface for Boardy QA."""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .engine import RuleEngine
from .validator import ConversationValidator
from .reports import ReportGenerator
from .ui_export import save_ui_report


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option('--config', '-c', type=click.Path(exists=True, path_type=Path),
              help='Configuration file for rules')
@click.option('--output', '-o', type=click.Path(path_type=Path),
              help='Output file (default: stdout)')
@click.option('--format', '-f', type=click.Choice(['markdown', 'html', 'ui']),
              default='markdown', help='Report format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def main(input_file: Path, config: Optional[Path], output: Optional[Path], 
         format: str, verbose: bool):
    """Analyze conversation logs with Boardy QA.
    
    INPUT_FILE: JSON file containing conversation logs
    """
    
    # Load configuration
    rules_config = _load_default_config()
    if config:
        try:
            with open(config, 'r') as f:
                user_config = json.load(f)
            # Merge the user config with default config
            user_rules = user_config.get('rules', {})
            if 'enabled_rules' in user_rules:
                rules_config['enabled_rules'] = user_rules['enabled_rules']
        except Exception as e:
            click.echo(f"Error loading config file: {e}", err=True)
            sys.exit(1)
    
    # Validate and load conversations
    validator = ConversationValidator()
    conversations, validation_errors = validator.load_conversations(input_file)
    
    if validation_errors:
        click.echo("Validation errors:", err=True)
        for error in validation_errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)
    
    if verbose:
        click.echo(f"Loaded {len(conversations)} conversations")
    
    # Set up rule engine
    engine = RuleEngine()
    engine.configure_rules(rules_config.get('enabled_rules', []))
    
    if verbose:
        click.echo(f"Running {len(engine.rules)} rules")
    
    # Analyze conversations
    analyses = engine.analyze_conversations(conversations)
    stats = engine.generate_report_stats(analyses)
    
    # Generate report
    generator = ReportGenerator()
    
    if format == 'markdown':
        report = generator.generate_markdown_report(analyses, stats)
    elif format == 'html':
        report = generator.generate_html_report(analyses, stats)
    elif format == 'ui':
        # Generate UI-compatible JSON report
        ui_data = save_ui_report(analyses, stats, output or 'ui_report.json')
        report = json.dumps(ui_data, indent=2)
    else:
        raise ValueError(f"Unknown format: {format}")
    
    # Output report
    if output and format != 'ui':
        with open(output, 'w', encoding='utf-8') as f:
            f.write(report)
        if verbose:
            click.echo(f"Report written to {output}")
    elif format == 'ui' and output:
        if verbose:
            click.echo(f"UI report written to {output}")
    else:
        click.echo(report)
    
    # Exit with error code if there are high-severity failures
    high_severity_count = stats.high_severity_failures
    if high_severity_count > 0:
        if verbose:
            click.echo(f"Found {high_severity_count} high-severity failures", err=True)
        sys.exit(1)


@click.command()
@click.argument('output_file', type=click.Path(path_type=Path))
def init_config(output_file: Path):
    """Generate a default configuration file."""
    
    default_config = _load_default_config()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)
    
    click.echo(f"Default configuration written to {output_file}")


@click.command()
@click.argument('output_file', type=click.Path(path_type=Path))
def init_sample(output_file: Path):
    """Generate a sample conversation log file."""
    
    sample_data = {
        "conversations": [
            {
                "messages": [
                    {
                        "id": "msg_001",
                        "timestamp": "2025-11-26T20:10:00Z",
                        "role": "user",
                        "text": "Hi! How can I track my package?",
                        "meta": {
                            "channel": "web",
                            "conversation_id": "conv_001"
                        }
                    },
                    {
                        "id": "msg_002",
                        "timestamp": "2025-11-26T20:10:15Z",
                        "role": "assistant",
                        "text": "Hello! I can help you track your package. Could you please provide your tracking number?",
                        "meta": {
                            "channel": "web",
                            "conversation_id": "conv_001"
                        }
                    },
                    {
                        "id": "msg_003",
                        "timestamp": "2025-11-26T20:10:30Z",
                        "role": "user",
                        "text": "The tracking number is 12345-ABCDE",
                        "meta": {
                            "channel": "web",
                            "conversation_id": "conv_001"
                        }
                    },
                    {
                        "id": "msg_004",
                        "timestamp": "2025-11-26T20:10:45Z",
                        "role": "assistant",
                        "text": "Thank you! Let me check that for you. Your package 12345-ABCDE is currently in transit and expected to arrive tomorrow by 5 PM. You can also track it at: tracking.example.com/12345-ABCDE",
                        "meta": {
                            "channel": "web",
                            "conversation_id": "conv_001"
                        }
                    }
                ]
            },
            {
                "messages": [
                    {
                        "id": "msg_005",
                        "timestamp": "2025-11-26T20:15:00Z",
                        "role": "user",
                        "text": "What are your business hours?",
                        "meta": {
                            "channel": "whatsapp",
                            "conversation_id": "conv_002"
                        }
                    },
                    {
                        "id": "msg_006",
                        "timestamp": "2025-11-26T20:15:20Z",
                        "role": "assistant",
                        "text": "I am an AI assistant and I don't have access to specific business hours information. As an AI, I'm available 24/7 to help with general questions, but for specific business hours, you'd need to check with the business directly.",
                        "meta": {
                            "channel": "whatsapp",
                            "conversation_id": "conv_002"
                        }
                    }
                ]
            }
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2)
    
    click.echo(f"Sample conversation log written to {output_file}")


def _load_default_config() -> dict:
    """Load default rule configuration."""
    return {
        "rules": {
            "enabled_rules": [
                {
                    "name": "LengthRule",
                    "enabled": True,
                    "config": {
                        "max_length_chars": 1200
                    }
                },
                {
                    "name": "QuestionFollowupRule",
                    "enabled": True,
                    "config": {}
                },
                {
                    "name": "StyleRule",
                    "enabled": True,
                    "config": {
                        "forbidden_phrases": [
                            "i am an ai",
                            "as an ai", 
                            "as a language model",
                            "i cannot",
                            "i am not able",
                            "i am unable",
                            "i don't have",
                            "i do not have"
                        ],
                        "max_exclamation_marks": 3,
                        "require_capitalization": True
                    }
                },
                {
                    "name": "TurnEndingRule",
                    "enabled": True,
                    "config": {
                        "max_question_length": 800,
                        "max_question_sentences": 5
                    }
                },
                {
                    "name": "ConversationHealthRule",
                    "enabled": True,
                    "config": {
                        "max_consecutive_assistant": 3,
                        "max_message_ratio": 3.0
                    }
                }
            ]
        }
    }


# Create command group
@click.group()
def cli():
    """Boardy QA - Conversation Quality Assurance Harness."""
    pass


# Add commands to group
cli.add_command(main, name='analyze')
cli.add_command(init_config, name='init-config')
cli.add_command(init_sample, name='init-sample')


if __name__ == '__main__':
    cli()
