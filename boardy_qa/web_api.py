"""Web API for Boardy QA paste analyzer."""

import json
import re
import tempfile
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .engine import RuleEngine
from .validator import ConversationValidator
from .ui_export import export_for_ui


class ConversationRequest(BaseModel):
    """Request model for conversation analysis."""
    text: str
    config: Dict[str, Any] = None


class ConversationResponse(BaseModel):
    """Response model for conversation analysis."""
    success: bool
    data: Dict[str, Any] = None
    error: str = None


# Create FastAPI app
app = FastAPI(
    title="Boardy QA API",
    description="Conversation Quality Assurance API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_conversation_text(text: str) -> Dict[str, Any]:
    """Parse conversation text into Boardy QA JSON format."""
    lines = [line for line in text.split('\n') if line.strip()]
    conversations = {}
    current_conversation_id = 'paste_conv'
    message_counter = 1

    # WhatsApp regex patterns
    patterns = [
        r'^\[(\d{1,2}\/\d{1,2}\/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.+)$',
        r'^\[(\d{1,2}\/\d{1,2}\/\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\]\s*([^:]+):\s*(.+)$',
        r'^(\d{1,2}\/\d{1,2}\/\d{2,4}),?\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)\s*([^:]+):\s*(.+)$'
    ]

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed = False
        for pattern in patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                date_str, time_str, name, message = match.groups()
                
                # Parse timestamp
                timestamp = parse_timestamp(date_str, time_str)
                if not timestamp:
                    continue
                
                # Determine role
                role = 'assistant' if 'boardy' in name.lower() else 'user'
                
                # Create conversation if needed
                if current_conversation_id not in conversations:
                    conversations[current_conversation_id] = []
                
                # Add message
                conversations[current_conversation_id].append({
                    "id": f"msg_{message_counter:03d}",
                    "timestamp": timestamp,
                    "role": role,
                    "text": message.strip(),
                    "meta": {
                        "channel": "web",
                        "conversation_id": current_conversation_id
                    }
                })
                
                message_counter += 1
                parsed = True
                break
        
        # If no pattern matched, try to handle simple format
        if not parsed and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                name, message = parts
                role = 'assistant' if 'boardy' in name.lower() else 'user'
                
                if current_conversation_id not in conversations:
                    conversations[current_conversation_id] = []
                
                conversations[current_conversation_id].append({
                    "id": f"msg_{message_counter:03d}",
                    "timestamp": datetime.now().isoformat(),
                    "role": role,
                    "text": message.strip(),
                    "meta": {
                        "channel": "web",
                        "conversation_id": current_conversation_id
                    }
                })
                
                message_counter += 1

    # Convert to Boardy QA format
    conversation_array = [
        {"messages": messages} 
        for messages in conversations.values()
    ]

    return {"conversations": conversation_array}


def parse_timestamp(date_str: str, time_str: str) -> str:
    """Parse timestamp and return ISO format."""
    try:
        import re
        # Parse date
        date_parts = date_str.split('/')
        if len(date_parts) != 3:
            return None
        
        month, day, year = date_parts
        if len(year) == 2:
            year = '20' + year
        
        # Parse time
        time_match = re.match(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?', time_str.strip(), re.IGNORECASE)
        if not time_match:
            return None
        
        hours, minutes, seconds, period = time_match.groups()
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds) if seconds else 0
        
        # Handle AM/PM
        if period and period.upper() == 'PM' and hours < 12:
            hours += 12
        elif period and period.upper() == 'AM' and hours == 12:
            hours = 0
        
        # Create ISO timestamp
        dt = datetime(int(year), int(month), int(day), hours, minutes, seconds)
        return dt.isoformat()
    except Exception:
        return None


@app.post("/analyze", response_model=ConversationResponse)
async def analyze_conversation(request: ConversationRequest):
    """Analyze a conversation from pasted text."""
    try:
        # Parse conversation text
        conversation_data = parse_conversation_text(request.text)
        
        if not conversation_data.get("conversations"):
            return ConversationResponse(
                success=False,
                error="Could not parse conversation. Please check the format."
            )
        
        # Create temporary file for the conversation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(conversation_data, f, indent=2)
            temp_file = f.name
        
        try:
            # Validate and load conversations
            validator = ConversationValidator()
            conversations, validation_errors = validator.load_conversations(temp_file)
            
            if validation_errors:
                return ConversationResponse(
                    success=False,
                    error=f"Validation errors: {'; '.join(validation_errors)}"
                )
            
            # Set up rule engine
            engine = RuleEngine()
            
            # Use provided config or default
            if request.config:
                engine.configure_rules(request.config.get('enabled_rules', []))
            else:
                # Default configuration
                engine.configure_rules([
                    {"name": "LengthRule", "enabled": True, "config": {"max_length_chars": 1200}},
                    {"name": "QuestionFollowupRule", "enabled": True, "config": {}},
                    {"name": "StyleRule", "enabled": True, "config": {
                        "forbidden_phrases": [
                            "i am an ai", "as an ai", "as a language model",
                            "i cannot", "i am unable", "i am not able",
                            "i don't have", "i do not have"
                        ],
                        "max_exclamation_marks": 3,
                        "require_capitalization": True
                    }},
                    {"name": "TurnEndingRule", "enabled": True, "config": {
                        "max_question_length": 800,
                        "max_question_sentences": 5
                    }},
                    {"name": "ConversationHealthRule", "enabled": True, "config": {
                        "max_consecutive_assistant": 3,
                        "max_message_ratio": 3.0
                    }}
                ])
            
            # Analyze conversations
            analyses = engine.analyze_conversations(conversations)
            stats = engine.generate_report_stats(analyses)
            
            # Export for UI
            ui_data = export_for_ui(analyses, stats)
            
            return ConversationResponse(
                success=True,
                data=ui_data
            )
            
        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)
            
    except Exception as e:
        return ConversationResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Boardy QA API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze - Analyze conversation text",
            "health": "GET /health - Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
