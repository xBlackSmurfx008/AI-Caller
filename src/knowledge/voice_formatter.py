"""Voice-optimized context formatting"""

from typing import List, Dict, Any, Optional
import re

from src.utils.logging import get_logger

logger = get_logger(__name__)


class VoiceFormatter:
    """Format knowledge base context for voice/speech output"""

    def __init__(self, max_length: int = 500, max_sentences: int = 3):
        """
        Initialize voice formatter
        
        Args:
            max_length: Maximum characters for voice output
            max_sentences: Maximum sentences to include
        """
        self.max_length = max_length
        self.max_sentences = max_sentences

    def format_for_voice(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: Optional[str] = None,
        prioritize_brevity: bool = True,
    ) -> str:
        """
        Format retrieved documents for voice output
        
        Args:
            retrieved_docs: Retrieved documents
            query: Optional query for context
            prioritize_brevity: Whether to prioritize brevity over completeness
            
        Returns:
            Formatted text optimized for speech
        """
        if not retrieved_docs:
            return ""
        
        # Sort by relevance score
        sorted_docs = sorted(
            retrieved_docs,
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )
        
        # Select most relevant documents
        max_docs = 2 if prioritize_brevity else 3
        selected_docs = sorted_docs[:max_docs]
        
        # Format each document
        formatted_parts = []
        total_length = 0
        
        for doc in selected_docs:
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            if not content:
                content = metadata.get("text", "")
            
            title = metadata.get("title", "Information")
            
            # Summarize content for voice
            summarized = self._summarize_for_voice(content, max_sentences=self.max_sentences)
            
            # Format as natural speech
            formatted = self._format_as_speech(title, summarized)
            
            # Check length constraints
            if total_length + len(formatted) > self.max_length and prioritize_brevity:
                # Truncate if needed
                remaining = self.max_length - total_length - 20  # Leave room for ellipsis
                if remaining > 50:
                    formatted = formatted[:remaining] + "..."
                else:
                    break
            
            formatted_parts.append(formatted)
            total_length += len(formatted)
        
        # Join with natural connectors
        if len(formatted_parts) == 1:
            return formatted_parts[0]
        elif len(formatted_parts) == 2:
            return f"{formatted_parts[0]} Additionally, {formatted_parts[1]}"
        else:
            result = ", ".join(formatted_parts[:-1])
            return f"{result}, and {formatted_parts[-1]}"

    def _summarize_for_voice(self, content: str, max_sentences: int = 3) -> str:
        """Summarize content for voice output"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return content[:200]  # Fallback truncation
        
        # Select most important sentences
        # Simple heuristic: prefer shorter, clearer sentences
        scored_sentences = []
        for sentence in sentences:
            score = 1.0
            # Penalize very long sentences
            if len(sentence) > 100:
                score *= 0.7
            # Penalize sentences with too many technical terms
            if len(re.findall(r'[A-Z]{2,}', sentence)) > 3:
                score *= 0.8
            scored_sentences.append((score, sentence))
        
        # Sort by score and take top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        selected = [s[1] for s in scored_sentences[:max_sentences]]
        
        # Reorder to maintain some coherence
        result = []
        for sentence in sentences:
            if sentence in selected:
                result.append(sentence)
                if len(result) >= max_sentences:
                    break
        
        return ". ".join(result) + "." if result else content[:200]

    def _format_as_speech(self, title: str, content: str) -> str:
        """Format content as natural speech"""
        # Remove markdown formatting
        content = re.sub(r'#+\s*', '', content)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        
        # Add prosody hints (simplified)
        # In production, you'd use SSML for TTS
        
        # Format with title if available
        if title and title != "Information":
            return f"According to {title}, {content}"
        else:
            return content

    def format_with_prosody(self, text: str) -> str:
        """
        Add prosody markers for TTS (simplified SSML-like)
        
        Args:
            text: Text to format
            
        Returns:
            Text with prosody hints
        """
        # Simple prosody hints
        # In production, use proper SSML
        
        # Emphasize important phrases (capitalized words, quotes)
        text = re.sub(r'"([^"]+)"', r'<emphasis>\1</emphasis>', text)
        
        # Pause markers for lists
        text = re.sub(r'([.!?])\s+([A-Z])', r'\1 <break time="300ms"/> \2', text)
        
        return text

    def handle_interruption(self, current_context: str, new_query: str) -> str:
        """
        Handle conversation interruption and follow-up
        
        Args:
            current_context: Current conversation context
            new_query: New query
            
        Returns:
            Updated context
        """
        # Detect if new query is a follow-up
        follow_up_indicators = ["also", "and", "what about", "how about", "tell me more"]
        
        is_follow_up = any(indicator in new_query.lower() for indicator in follow_up_indicators)
        
        if is_follow_up:
            # Combine contexts
            return f"{current_context} {new_query}"
        else:
            # New topic
            return new_query

    def format_for_tts(self, text: str) -> str:
        """
        Format text specifically for text-to-speech
        
        Args:
            text: Text to format
            
        Returns:
            TTS-optimized text
        """
        # Expand abbreviations
        abbreviations = {
            "API": "A P I",
            "URL": "U R L",
            "HTTP": "H T T P",
            "HTTPS": "H T T P S",
            "JSON": "J S O N",
            "XML": "X M L",
            "SQL": "S Q L",
            "etc.": "etcetera",
            "e.g.": "for example",
            "i.e.": "that is",
        }
        
        for abbr, expansion in abbreviations.items():
            text = text.replace(abbr, expansion)
        
        # Remove special characters that don't read well
        text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text

