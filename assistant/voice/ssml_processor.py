"""
SSML Processor
Processes Speech Synthesis Markup Language for enhanced speech synthesis.
"""

import os
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class SSMLTag(Enum):
    SPEAK = "speak"
    VOICE = "voice"
    PROSODY = "prosody"
    BREAK = "break"
    EMPHASIS = "emphasis"
    SAY_AS = "say-as"
    AUDIO = "audio"
    SUB = "sub"
    MARK = "mark"
    P = "p"
    S = "s"


@dataclass
class SSMLInstruction:
    instruction_id: str
    tag: SSMLTag
    attributes: Dict[str, str]
    content: str
    start_index: int
    end_index: int


class SSMLProcessor:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ssml_dir = os.path.join(self.base_dir, "data", "ssml")
        self.templates_file = os.path.join(self.ssml_dir, "ssml_templates.json")
        
        os.makedirs(self.ssml_dir, exist_ok=True)
        
        # Load templates
        self.templates = self._load_templates()
        
        # Initialize default templates
        self._initialize_default_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load SSML templates from disk."""
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_templates(self):
        """Save SSML templates to disk."""
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            print(f"[SSMLProcessor] Failed to save templates: {e}")

    def _initialize_default_templates(self):
        """Initialize default SSML templates."""
        if not self.templates:
            self.templates = {
                'greeting': '<speak><voice name="default">Hello! How can I help you today?</voice></speak>',
                'confirmation': '<speak><prosody rate="fast">Confirmed. I will proceed with that.</prosody></speak>',
                'error': '<speak><prosody pitch="low">I apologize, but I encountered an error.</prosody></speak>',
                'excited': '<speak><prosody rate="fast" pitch="high">That is wonderful news!</prosody></speak>',
                'calm': '<speak><prosody rate="slow" pitch="low">I understand. Let me help you with that.</prosody></speak>',
                'emphasis': '<speak>This is <emphasis level="strong">very important</emphasis> information.</speak>',
                'pause': '<speak>Here is the result <break time="1s"/> and here is the next part.</speak>',
                'spelling': '<speak><say-as interpret-as="characters">JARVIS</say-as></speak>',
                'date': '<speak><say-as interpret-as="date" format="mdy">01/15/2024</say-as></speak>',
                'number': '<speak><say-as interpret-as="cardinal">12345</say-as></speak>',
                'ordinal': '<speak><say-as interpret-as="ordinal">1st</say-as></speak>',
                'currency': '<speak><say-as interpret-as="currency">$99.99</say-as></speak>',
                'time': '<speak><say-as interpret-as="time" format="hms12">2:30 PM</say-as></speak>',
                'address': '<speak><say-as interpret-as="address">123 Main Street</say-as></speak>'
            }
            self._save_templates()

    def parse_ssml(self, ssml_text: str) -> List[SSMLInstruction]:
        """
        Parse SSML text into instructions.
        
        Args:
            ssml_text: SSML text to parse
            
        Returns:
            List of SSMLInstructions
        """
        instructions = []
        
        # Pattern to match SSML tags
        pattern = r'<(\w+)([^>]*)>([^<]*)</\1>'
        
        for match in re.finditer(pattern, ssml_text):
            tag_name = match.group(1)
            attributes_str = match.group(2)
            content = match.group(3)
            
            # Parse attributes
            attributes = {}
            if attributes_str:
                attr_pattern = r'(\w+)="([^"]*)"'
                for attr_match in re.finditer(attr_pattern, attributes_str):
                    attributes[attr_match.group(1)] = attr_match.group(2)
            
            # Map to enum
            try:
                tag = SSMLTag(tag_name.lower())
            except ValueError:
                tag = SSMLTag.SPEAK  # Default
            
            instruction = SSMLInstruction(
                instruction_id=f"inst_{len(instructions)}",
                tag=tag,
                attributes=attributes,
                content=content,
                start_index=match.start(),
                end_index=match.end()
            )
            
            instructions.append(instruction)
        
        return instructions

    def generate_ssml(self, text: str, voice: str = "default", 
                     rate: str = "medium", pitch: str = "medium",
                     volume: str = "medium") -> str:
        """
        Generate SSML from plain text with parameters.
        
        Args:
            text: Plain text
            voice: Voice name
            rate: Speech rate (slow, medium, fast)
            pitch: Pitch (low, medium, high)
            volume: Volume (soft, medium, loud)
            
        Returns:
            SSML string
        """
        ssml = f'<speak>'
        ssml += f'<voice name="{voice}">'
        ssml += f'<prosody rate="{rate}" pitch="{pitch}" volume="{volume}">'
        ssml += text
        ssml += '</prosody>'
        ssml += '</voice>'
        ssml += '</speak>'
        
        return ssml

    def add_emphasis(self, text: str, level: str = "moderate") -> str:
        """
        Add emphasis to text.
        
        Args:
            text: Text to emphasize
            level: Emphasis level (strong, moderate, weak, none)
            
        Returns:
            SSML with emphasis
        """
        return f'<emphasis level="{level}">{text}</emphasis>'

    def add_break(self, time: str = "500ms") -> str:
        """
        Add a break/pause.
        
        Args:
            time: Break duration (e.g., "500ms", "1s")
            
        Returns:
            SSML break tag
        """
        return f'<break time="{time}"/>'

    def say_as(self, text: str, interpret_as: str, format: str = None) -> str:
        """
        Specify how text should be interpreted.
        
        Args:
            text: Text to interpret
            interpret_as: Interpretation type (characters, date, time, etc.)
            format: Optional format string
            
        Returns:
            SSML say-as tag
        """
        if format:
            return f'<say-as interpret-as="{interpret_as}" format="{format}">{text}</say-as>'
        return f'<say-as interpret-as="{interpret_as}">{text}</say-as>'

    def create_paragraph(self, text: str) -> str:
        """Create a paragraph in SSML."""
        return f'<p>{text}</p>'

    def create_sentence(self, text: str) -> str:
        """Create a sentence in SSML."""
        return f'<s>{text}</s>'

    def add_audio(self, src: str) -> str:
        """
        Add audio to SSML.
        
        Args:
            src: Audio source URL or path
            
        Returns:
            SSML audio tag
        """
        return f'<audio src="{src}"/>'

    def substitute(self, alias: str, text: str) -> str:
        """
        Create a pronunciation substitution.
        
        Args:
            alias: Alias text
            text: Substitution text
            
        Returns:
            SSML sub tag
        """
        return f'<sub alias="{alias}">{text}</sub>'

    def add_mark(self, name: str) -> str:
        """
        Add a mark for synchronization.
        
        Args:
            name: Mark name
            
        Returns:
            SSML mark tag
        """
        return f'<mark name="{name}"/>'

    def validate_ssml(self, ssml_text: str) -> Tuple[bool, List[str]]:
        """
        Validate SSML syntax.
        
        Args:
            ssml_text: SSML text to validate
            
        Returns:
            (is_valid, list of errors)
        """
        errors = []
        
        # Check for root speak tag
        if not ssml_text.startswith('<speak>') or not ssml_text.endswith('</speak>'):
            errors.append("SSML must be wrapped in <speak> tags")
        
        # Check for balanced tags
        open_tags = []
        pattern = r'<(/?)(\w+)[^>]*>'
        
        for match in re.finditer(pattern, ssml_text):
            is_closing = match.group(1) == "/"
            tag_name = match.group(2)
            
            if is_closing:
                if not open_tags or open_tags[-1] != tag_name:
                    errors.append(f"Unbalanced tag: {tag_name}")
                else:
                    open_tags.pop()
            else:
                open_tags.append(tag_name)
        
        if open_tags:
            errors.append(f"Unclosed tags: {', '.join(open_tags)}")
        
        return len(errors) == 0, errors

    def strip_ssml(self, ssml_text: str) -> str:
        """
        Remove SSML tags and return plain text.
        
        Args:
            ssml_text: SSML text
            
        Returns:
            Plain text
        """
        # Remove all tags
        plain_text = re.sub(r'<[^>]+>', '', ssml_text)
        
        # Clean up whitespace
        plain_text = ' '.join(plain_text.split())
        
        return plain_text

    def get_template(self, template_name: str) -> Optional[str]:
        """Get an SSML template by name."""
        return self.templates.get(template_name)

    def add_template(self, name: str, ssml: str) -> bool:
        """Add a custom SSML template."""
        self.templates[name] = ssml
        self._save_templates()
        return True

    def list_templates(self) -> List[str]:
        """List available SSML templates."""
        return list(self.templates.keys())

    def delete_template(self, name: str) -> bool:
        """Delete an SSML template."""
        if name in self.templates:
            del self.templates[name]
            self._save_templates()
            return True
        return False

    def convert_text_to_ssml(self, text: str, auto_emphasis: bool = True) -> str:
        """
        Automatically convert plain text to SSML with enhancements.
        
        Args:
            text: Plain text
            auto_emphasis: Whether to add emphasis to important words
            
        Returns:
            SSML string
        """
        ssml = '<speak>'
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Add as paragraph
            ssml += f'<p>{sentence}</p>'
            
            # Add pause after sentence
            ssml += '<break time="300ms"/>'
        
        ssml += '</speak>'
        
        return ssml

    def get_statistics(self) -> Dict[str, Any]:
        """Get SSML processor statistics."""
        return {
            'total_templates': len(self.templates),
            'available_templates': list(self.templates.keys())
        }

    def export_ssml(self, ssml_text: str, export_path: str) -> Tuple[bool, str]:
        """Export SSML to file."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(ssml_text)
            return True, f"SSML exported to {export_path}"
        except Exception as e:
            return False, f"Export failed: {str(e)}"
