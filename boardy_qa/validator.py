"""JSON schema validation for conversation logs."""

import json
import jsonschema
from typing import List, Dict, Any, Union
from pathlib import Path

from .models import Message, Conversation


class ConversationValidator:
    """Validator for conversation JSON logs."""
    
    SCHEMA = {
        "type": "object",
        "properties": {
            "conversations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "timestamp": {
                                        "type": "string",
                                        "format": "date-time"
                                    },
                                    "role": {
                                        "type": "string",
                                        "enum": ["user", "assistant"]
                                    },
                                    "text": {"type": "string"},
                                    "meta": {
                                        "type": "object",
                                        "properties": {
                                            "channel": {
                                                "type": "string",
                                                "enum": ["whatsapp", "sms", "web"]
                                            },
                                            "conversation_id": {"type": "string"}
                                        },
                                        "required": ["channel", "conversation_id"]
                                    }
                                },
                                "required": ["id", "timestamp", "role", "text", "meta"]
                            }
                        }
                    },
                    "required": ["messages"]
                }
            }
        },
        "required": ["conversations"]
    }
    
    def __init__(self):
        self.validator = jsonschema.Draft7Validator(self.SCHEMA)
    
    def validate_file(self, file_path: Union[str, Path]) -> List[str]:
        """Validate a JSON file and return validation errors."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.validate_data(data)
        except json.JSONDecodeError as e:
            return [f"Invalid JSON: {str(e)}"]
        except FileNotFoundError:
            return [f"File not found: {file_path}"]
        except Exception as e:
            return [f"Error reading file: {str(e)}"]
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate parsed JSON data and return validation errors."""
        errors = []
        
        for error in self.validator.iter_errors(data):
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"Validation error at {path}: {error.message}")
        
        return errors
    
    def load_conversations(self, file_path: Union[str, Path]) -> tuple[List[Conversation], List[str]]:
        """Load and validate conversations from file."""
        validation_errors = self.validate_file(file_path)
        
        if validation_errors:
            return [], validation_errors
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = []
            for conv_data in data.get('conversations', []):
                messages = []
                for msg_data in conv_data.get('messages', []):
                    message = Message(**msg_data)
                    messages.append(message)
                
                conversation = Conversation(messages=messages)
                conversations.append(conversation)
            
            return conversations, []
        
        except Exception as e:
            return [], [f"Error loading conversations: {str(e)}"]
