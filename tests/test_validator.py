"""Tests for the conversation validator."""

import pytest
import json
import tempfile
from pathlib import Path

from boardy_qa.validator import ConversationValidator
from boardy_qa.models import Message, Conversation


class TestConversationValidator:
    """Test the ConversationValidator."""
    
    def test_valid_data_passes(self):
        """Test that valid data passes validation."""
        validator = ConversationValidator()
        
        valid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "user",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        errors = validator.validate_data(valid_data)
        assert len(errors) == 0
    
    def test_missing_required_field_fails(self):
        """Test that missing required fields fail validation."""
        validator = ConversationValidator()
        
        invalid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "user",
                            # Missing "text" field
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        errors = validator.validate_data(invalid_data)
        assert len(errors) > 0
        assert any("text" in error.lower() for error in errors)
    
    def test_invalid_role_fails(self):
        """Test that invalid roles fail validation."""
        validator = ConversationValidator()
        
        invalid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "invalid_role",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        errors = validator.validate_data(invalid_data)
        assert len(errors) > 0
        assert any("invalid_role" in error for error in errors)
    
    def test_invalid_channel_fails(self):
        """Test that invalid channels fail validation."""
        validator = ConversationValidator()
        
        invalid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "user",
                            "text": "Hello!",
                            "meta": {
                                "channel": "invalid_channel",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        errors = validator.validate_data(invalid_data)
        assert len(errors) > 0
        assert any("invalid_channel" in error for error in errors)
    
    def test_invalid_timestamp_fails(self):
        """Test that invalid timestamps fail validation."""
        validator = ConversationValidator()
        
        invalid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "not-a-real-timestamp",
                            "role": "user",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        errors = validator.validate_data(invalid_data)
        assert len(errors) > 0
        assert any("timestamp" in error.lower() for error in errors)
    
    def test_valid_file_passes(self):
        """Test that valid files pass validation."""
        validator = ConversationValidator()
        
        valid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "user",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = f.name
        
        try:
            errors = validator.validate_file(temp_path)
            assert len(errors) == 0
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_json_file_fails(self):
        """Test that invalid JSON files fail validation."""
        validator = ConversationValidator()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            temp_path = f.name
        
        try:
            errors = validator.validate_file(temp_path)
            assert len(errors) > 0
            assert any("invalid json" in error.lower() for error in errors)
        finally:
            Path(temp_path).unlink()
    
    def test_nonexistent_file_fails(self):
        """Test that nonexistent files fail validation."""
        validator = ConversationValidator()
        
        errors = validator.validate_file("/nonexistent/path/file.json")
        assert len(errors) > 0
        assert any("not found" in error.lower() for error in errors)
    
    def test_load_conversations_success(self):
        """Test successful loading of conversations."""
        validator = ConversationValidator()
        
        valid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "user",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        },
                        {
                            "id": "msg_2",
                            "timestamp": "2025-11-26T20:10:15Z",
                            "role": "assistant",
                            "text": "Hi there!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_data, f)
            temp_path = f.name
        
        try:
            conversations, errors = validator.load_conversations(temp_path)
            assert len(errors) == 0
            assert len(conversations) == 1
            assert len(conversations[0].messages) == 2
            assert conversations[0].messages[0].role == "user"
            assert conversations[0].messages[1].role == "assistant"
            assert conversations[0].get_conversation_id() == "conv_1"
        finally:
            Path(temp_path).unlink()
    
    def test_load_conversations_with_validation_errors(self):
        """Test loading conversations with validation errors."""
        validator = ConversationValidator()
        
        invalid_data = {
            "conversations": [
                {
                    "messages": [
                        {
                            "id": "msg_1",
                            "timestamp": "2025-11-26T20:10:00Z",
                            "role": "invalid_role",
                            "text": "Hello!",
                            "meta": {
                                "channel": "web",
                                "conversation_id": "conv_1"
                            }
                        }
                    ]
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_data, f)
            temp_path = f.name
        
        try:
            conversations, errors = validator.load_conversations(temp_path)
            assert len(errors) > 0
            assert len(conversations) == 0
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__])
