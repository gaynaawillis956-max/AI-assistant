import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple

logger = logging.getLogger("chat-learner")


class ChatLearner:
    """Load and learn from chat examples to improve bot responses."""
    
    def __init__(self, chats_dir: str = "chats"):
        self.chats_dir = Path(chats_dir)
        self.examples_dir = self.chats_dir / "examples"
        self.learned_dir = self.chats_dir / "learned"
        self.conversations = []
        self._ensure_dirs()
        self.load_examples()
    
    def _ensure_dirs(self):
        """Create necessary directories."""
        self.examples_dir.mkdir(parents=True, exist_ok=True)
        self.learned_dir.mkdir(parents=True, exist_ok=True)
    
    def load_examples(self):
        """Load all chat examples from files."""
        if not self.examples_dir.exists():
            logger.warning(f"Examples directory not found: {self.examples_dir}")
            return
        
        for file_path in self.examples_dir.glob("*.txt"):
            try:
                conversation = self._parse_conversation(file_path)
                if conversation:
                    self.conversations.append(conversation)
                    logger.info(f"Loaded: {file_path.name}")
            except Exception as exc:
                logger.exception(f"Error loading {file_path}: {exc}")
    
    def _parse_conversation(self, file_path: Path) -> List[Dict]:
        """Parse conversation file into structured format."""
        conversation = []
        content = file_path.read_text(encoding="utf-8")
        lines = content.strip().split("\n")
        
        for line in lines:
            if not line.strip():
                continue
            
            if line.startswith("CUSTOMER:"):
                message = line.replace("CUSTOMER:", "").strip()
                conversation.append({"role": "user", "content": message})
            elif line.startswith("BOT:"):
                message = line.replace("BOT:", "").strip()
                conversation.append({"role": "assistant", "content": message})
        
        return conversation
    
    def extract_patterns(self) -> Dict:
        """Extract common phrases and patterns from conversations."""
        patterns = {
            "greetings": [],
            "pricing_responses": [],
            "payment_mentions": [],
            "common_phrases": [],
        }
        
        for conversation in self.conversations:
            for message in conversation:
                if message["role"] == "assistant":
                    content = message["content"].lower()
                    
                    # Greeting patterns
                    if any(word in content for word in ["hey", "hi", "what's up", "yo"]):
                        patterns["greetings"].append(message["content"])
                    
                    # Pricing patterns
                    if any(word in content for word in ["$", "price", "cost", "btc", "eth"]):
                        patterns["pricing_responses"].append(message["content"])
                    
                    # Payment patterns
                    if any(word in content for word in ["send", "payment", "address", "wallet", "confirm"]):
                        patterns["payment_mentions"].append(message["content"])
                    
                    # General phrases
                    if len(message["content"]) > 10:
                        patterns["common_phrases"].append(message["content"])
        
        # Remove duplicates
        for key in patterns:
            patterns[key] = list(set(patterns[key]))
        
        logger.info(f"Extracted patterns: {sum(len(v) for v in patterns.values())} total")
        return patterns
    
    def get_random_example(self, category: str = None) -> str:
        """Get a random bot response for reference."""
        import random
        
        if not self.conversations:
            return ""
        
        patterns = self.extract_patterns()
        
        if category and category in patterns and patterns[category]:
            return random.choice(patterns[category])
        
        # Get random bot response
        all_responses = []
        for conv in self.conversations:
            for msg in conv:
                if msg["role"] == "assistant":
                    all_responses.append(msg["content"])
        
        return random.choice(all_responses) if all_responses else ""
    
    def get_conversation_context(self) -> str:
        """Get context from learned conversations for system prompt."""
        patterns = self.extract_patterns()
        
        context = "Based on learned conversations, common bot behaviors:\n"
        context += f"- Greeting style: {patterns['greetings'][:2] if patterns['greetings'] else 'Direct and brief'}\n"
        context += f"- Pricing approach: {patterns['pricing_responses'][:2] if patterns['pricing_responses'] else 'Firm pricing, no negotiation'}\n"
        context += f"- Payment handling: {patterns['payment_mentions'][:2] if patterns['payment_mentions'] else 'Crypto only, immediate settlement'}\n"
        
        return context
    
    def save_learned_conversation(self, customer: str, conversation: List[Dict]) -> None:
        """Save a conversation as learned data."""
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.learned_dir / f"{customer}_{timestamp}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(conversation, f, indent=2)
            logger.info(f"Saved learned conversation: {filename}")
        except Exception as exc:
            logger.exception(f"Error saving learned conversation: {exc}")
