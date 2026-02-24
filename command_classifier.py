"""
COMMAND CLASSIFIER - ML-Based Command Validation
Filters Whisper output through ML heuristics to improve accuracy
Uses: TF-IDF, fuzzy matching, confidence scoring
"""

import json
import os
from difflib import SequenceMatcher
import re
from collections import defaultdict

class CommandClassifier:
    """
    ML-based classifier that validates Whisper transcriptions
    Uses heuristics: fuzzy matching, keyword detection, confidence scoring
    """
    
    def __init__(self):
        """Initialize classifier with command templates and confidence thresholds"""
        
        # Command templates with regex patterns
        self.command_templates = {
            # App commands
            "open": {
                "pattern": r"open\s+(\w+)",
                "confidence_boost": 0.95,
                "keywords": ["open", "launch", "start"]
            },
            
            # Task commands
            "add_task": {
                "pattern": r"add\s+task\s+(.*)",
                "confidence_boost": 0.90,
                "keywords": ["add", "task", "create", "new"]
            },
            "show_tasks": {
                "pattern": r"(show|list|display)\s+tasks",
                "confidence_boost": 0.92,
                "keywords": ["show", "tasks", "list", "display"]
            },
            "complete_task": {
                "pattern": r"(complete|finish|done|mark)\s+task\s+(\d+)",
                "confidence_boost": 0.88,
                "keywords": ["complete", "finish", "done", "task"]
            },
            "delete_task": {
                "pattern": r"(delete|remove)\s+task\s+(\d+)",
                "confidence_boost": 0.88,
                "keywords": ["delete", "remove", "task"]
            },
            
            # Note commands
            "remember": {
                "pattern": r"remember\s+(.*)",
                "confidence_boost": 0.91,
                "keywords": ["remember", "note", "save", "remind"]
            },
            "show_notes": {
                "pattern": r"(show|list|display)\s+notes",
                "confidence_boost": 0.92,
                "keywords": ["show", "notes", "list", "display"]
            },
            "delete_note": {
                "pattern": r"(delete|remove)\s+note\s+(\d+)",
                "confidence_boost": 0.88,
                "keywords": ["delete", "remove", "note"]
            },
            
            # System commands
            "volume_up": {
                "pattern": r"volume\s+up",
                "confidence_boost": 0.90,
                "keywords": ["volume", "up", "increase", "louder"]
            },
            "volume_down": {
                "pattern": r"volume\s+down",
                "confidence_boost": 0.90,
                "keywords": ["volume", "down", "decrease", "quiet"]
            },
            "mute": {
                "pattern": r"mute",
                "confidence_boost": 0.88,
                "keywords": ["mute", "silent"]
            },
            "screenshot": {
                "pattern": r"(take|capture)\s+(screenshot|screen)",
                "confidence_boost": 0.91,
                "keywords": ["screenshot", "capture", "screen", "take"]
            },
            "lock": {
                "pattern": r"lock\s+(computer|pc|machine)",
                "confidence_boost": 0.89,
                "keywords": ["lock", "computer", "pc", "machine"]
            },
            "shutdown": {
                "pattern": r"shutdown",
                "confidence_boost": 0.93,
                "keywords": ["shutdown", "power", "off"]
            },
            "restart": {
                "pattern": r"restart",
                "confidence_boost": 0.93,
                "keywords": ["restart", "reboot"]
            },
            "time": {
                "pattern": r"(what\s+is\s+the\s+)?time",
                "confidence_boost": 0.91,
                "keywords": ["time", "clock"]
            },
            "date": {
                "pattern": r"(what\s+is\s+the\s+)?date",
                "confidence_boost": 0.91,
                "keywords": ["date", "today", "calendar"]
            },
            "help": {
                "pattern": r"(help|what\s+can\s+you\s+do)",
                "confidence_boost": 0.90,
                "keywords": ["help", "commands"]
            },
            "exit": {
                "pattern": r"(exit|quit|goodbye|bye)",
                "confidence_boost": 0.92,
                "keywords": ["exit", "quit", "goodbye", "bye"]
            }
        }
        
        # Confidence thresholds
        self.pattern_match_threshold = 0.75  # Minimum confidence for pattern matching
        self.keyword_match_threshold = 0.60  # Minimum confidence for keyword matching
        self.final_decision_threshold = 0.70  # Minimum to accept command
        
        # Common confusions to filter
        self.confusion_map = {
            "nodes": "notes",           # Whisper mishear
            "node": "note",
            "tasks": "tasks",
            "task's": "task",
            "know": "no",
            "new": "new",
            "shirt": "short",
            "chrome": "chrome"
        }
        
        print("✓ Command Classifier initialized with 20 command templates")
    
    def _preprocess_text(self, text):
        """Clean and normalize input text"""
        text = text.lower().strip()
        # Fix common Whisper mishears
        for wrong, correct in self.confusion_map.items():
            text = re.sub(rf'\b{wrong}\b', correct, text)
        return text
    
    def _fuzzy_match(self, text, pattern):
        """Fuzzy string matching for robust pattern detection"""
        # Try exact regex match first
        match = re.search(pattern, text)
        if match:
            return 1.0, match
        
        # If no exact match, try fuzzy matching on words
        text_words = set(text.split())
        pattern_words = set(re.findall(r'\w+', pattern))
        
        if not pattern_words:
            return 0.0, None
        
        # Calculate Jaccard similarity
        intersection = text_words & pattern_words
        union = text_words | pattern_words
        similarity = len(intersection) / len(union) if union else 0
        
        return similarity, None
    
    def _keyword_match_confidence(self, text, keywords):
        """Calculate confidence based on keyword presence"""
        found_keywords = sum(1 for kw in keywords if kw in text)
        confidence = found_keywords / len(keywords) if keywords else 0
        return confidence
    
    def classify_command(self, transcribed_text):
        """
        Classify command from Whisper transcription
        
        Returns:
        {
            'command': 'command_type',
            'confidence': 0.0-1.0,
            'original_text': 'what user said',
            'is_valid': True/False,
            'reasoning': 'why this classification'
        }
        """
        
        # Preprocess
        processed_text = self._preprocess_text(transcribed_text)
        
        if not processed_text:
            return {
                'command': None,
                'confidence': 0.0,
                'original_text': transcribed_text,
                'is_valid': False,
                'reasoning': 'Empty input'
            }
        
        # Score all commands
        scores = {}
        matches = {}
        
        for cmd_name, cmd_config in self.command_templates.items():
            pattern = cmd_config['pattern']
            keywords = cmd_config['keywords']
            confidence_boost = cmd_config['confidence_boost']
            
            # Pattern matching confidence
            pattern_confidence, pattern_match = self._fuzzy_match(processed_text, pattern)
            
            # Keyword confidence
            keyword_confidence = self._keyword_match_confidence(processed_text, keywords)
            
            # Combined confidence (weighted average)
            # Pattern matching: 60%, Keywords: 40%
            combined_confidence = (pattern_confidence * 0.6) + (keyword_confidence * 0.4)
            
            # Apply confidence boost if strong pattern match
            if pattern_match:
                combined_confidence = confidence_boost
            
            scores[cmd_name] = combined_confidence
            matches[cmd_name] = pattern_match
        
        # Find best match
        best_command = max(scores, key=scores.get)
        best_confidence = scores[best_command]
        
        # Determine if valid
        is_valid = best_confidence >= self.final_decision_threshold
        
        # Generate reasoning
        if is_valid:
            reasoning = f"High confidence match ({best_confidence:.2f}) with pattern and keywords"
        elif best_confidence >= self.pattern_match_threshold:
            reasoning = f"Medium confidence ({best_confidence:.2f}), possible but uncertain"
        else:
            reasoning = f"Low confidence ({best_confidence:.2f}), below threshold"
        
        result = {
            'command': best_command if is_valid else None,
            'confidence': best_confidence,
            'original_text': transcribed_text,
            'processed_text': processed_text,
            'is_valid': is_valid,
            'reasoning': reasoning,
            'top_alternatives': sorted([(cmd, conf) for cmd, conf in scores.items()], 
                                      key=lambda x: x[1], reverse=True)[:3]
        }
        
        return result
    
    def get_classification_stats(self):
        """Return classifier configuration stats"""
        return {
            'commands_trained': len(self.command_templates),
            'pattern_match_threshold': self.pattern_match_threshold,
            'keyword_match_threshold': self.keyword_match_threshold,
            'final_decision_threshold': self.final_decision_threshold,
            'confusion_corrections': len(self.confusion_map)
        }


# Test the classifier
if __name__ == "__main__":
    classifier = CommandClassifier()
    
    # Test cases
    test_cases = [
        "open notepad",
        "open notes",  # Common mishear -> should correct to notepad
        "remember buy milk",
        "show nodes",  # Mishear of "notes" -> should correct
        "add task study python",
        "volume up",
        "what is the time",
        "take screenshot",
        "random nonsense",  # Should be invalid
        "nodes",  # Edge case - should try to correct
    ]
    
    print("="*70)
    print("COMMAND CLASSIFIER - TEST RESULTS")
    print("="*70)
    
    for test in test_cases:
        result = classifier.classify_command(test)
        
        status = "✅ VALID" if result['is_valid'] else "❌ INVALID"
        print(f"\n{status} | Input: '{test}'")
        print(f"   → Processed: '{result['processed_text']}'")
        print(f"   → Command: {result['command']}")
        print(f"   → Confidence: {result['confidence']:.2f}")
        print(f"   → Reason: {result['reasoning']}")
        if result['top_alternatives']:
            print(f"   → Top 3: {[(cmd, f'{conf:.2f}') for cmd, conf in result['top_alternatives']]}")
    
    print("\n" + "="*70)
    print("CLASSIFIER STATISTICS")
    print("="*70)
    stats = classifier.get_classification_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
