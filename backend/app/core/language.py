import re
from typing import List, Any, Optional

def detect_message_language(text: str, history: Optional[List[Any]] = None) -> str:
    """
    Dynamically detects message language. Returns 'urdu', 'roman_urdu', or 'english'.
    If the message contains no alphanumeric text (e.g. emojis or punctuation),
    it falls back to analyzing the conversation history.
    """
    if not text:
        return _fallback_to_history(history)
        
    cleaned = re.sub(r'[^\w\s]', '', text).strip()
    if not cleaned:
        return _fallback_to_history(history)

    # 1. Detect Urdu Script (Arabic Unicode range)
    if any(0x0600 <= ord(c) <= 0x06FF for c in text):
        return "urdu"
        
    # 2. Extract words and calculate score
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return _fallback_to_history(history)
        
    roman_urdu_words = {
        "hai", "kya", "hain", "haan", "nahin", "nhi", "batao", "mujhe", "acha", "shukriya", "kia",
        "ki", "ka", "aur", "se", "ho", "mein", "hun", "hoon", "bhi", "tou", "to", "kr", "kar", "karna",
        "karein", "karta", "raha", "rahi", "rha", "rhi", "kab", "sab", "hum", "tum", "aap", "ap",
        "kese", "kaise", "bataen", "batae", "shuru", "khatam", "hoga", "hogi", "oge", "rahe", "karne",
        "karta", "karte", "chahiye", "chaheye", "zarurat", "masla", "theek", "thik", "gaya", "gayi", "gae",
        "salam", "assalam", "aoa", "yar", "yaar", "ji", "jee", "achha"
    }
    
    english_words = {
        "the", "and", "of", "to", "is", "in", "it", "you", "that", "was", "for", "on", "are", "as",
        "with", "they", "at", "be", "this", "have", "from", "or", "had", "by", "but", "not", "what",
        "all", "were", "we", "when", "your", "can", "there", "use", "an", "each", "which", "she",
        "do", "how", "their", "if", "would", "about", "who", "get", "which", "go", "me", "my"
    }
    
    roman_score = sum(1 for w in words if w in roman_urdu_words)
    english_score = sum(1 for w in words if w in english_words)
    
    if roman_score > english_score:
        return "roman_urdu"
    elif english_score > roman_score:
        return "english"
    else:
        if roman_score > 0:
            return "roman_urdu"
        return _fallback_to_history(history)

def _fallback_to_history(history: Optional[List[Any]]) -> str:
    """Traverses conversation history in reverse to find the last resolved language."""
    if not history:
        return "english"  # Ultimate default fallback
        
    for msg in reversed(history):
        content = None
        if isinstance(msg, dict):
            content = msg.get("content")
        else:
            content = getattr(msg, "content", None)
            
        if content:
            cleaned = re.sub(r'[^\w\s]', '', content).strip()
            if not cleaned:
                continue
            if any(0x0600 <= ord(c) <= 0x06FF for c in content):
                return "urdu"
            words = re.findall(r'\b\w+\b', content.lower())
            if not words:
                continue
            roman_urdu_words = {
                "hai", "kya", "hain", "haan", "nahin", "nhi", "batao", "mujhe", "acha", "shukriya", "kia",
                "ki", "ka", "aur", "se", "ho", "mein", "hun", "hoon", "bhi", "tou", "to", "kr", "kar", "karna"
            }
            if any(w in words for w in roman_urdu_words):
                return "roman_urdu"
            return "english"
            
    return "english"
