"""Advanced chunking strategies for document processing"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum

from sentence_transformers import SentenceTransformer
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChunkingStrategy(str, Enum):
    """Chunking strategy enumeration"""
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    SLIDING_WINDOW = "sliding_window"
    ADAPTIVE = "adaptive"


class BaseChunkingStrategy(ABC):
    """Base class for chunking strategies"""

    @abstractmethod
    def chunk(self, text: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: Text to chunk
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        pass

    def _calculate_chunk_quality(self, chunk_text: str) -> float:
        """
        Calculate quality score for a chunk
        
        Args:
            chunk_text: Chunk text
            
        Returns:
            Quality score between 0 and 1
        """
        if not chunk_text or len(chunk_text.strip()) < 10:
            return 0.0
        
        score = 1.0
        
        # Penalize very short chunks
        if len(chunk_text) < 50:
            score *= 0.7
        
        # Penalize chunks with too many special characters
        special_char_ratio = len(re.findall(r'[^\w\s]', chunk_text)) / max(len(chunk_text), 1)
        if special_char_ratio > 0.3:
            score *= 0.8
        
        # Reward chunks with sentence structure
        sentence_count = len(re.findall(r'[.!?]+', chunk_text))
        if sentence_count > 0:
            score *= 1.1
        
        return min(score, 1.0)


class SemanticChunkingStrategy(BaseChunkingStrategy):
    """Semantic chunking using sentence transformers to group related sentences"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", similarity_threshold: float = 0.7):
        """
        Initialize semantic chunking strategy
        
        Args:
            model_name: Sentence transformer model name
            similarity_threshold: Minimum similarity to group sentences
        """
        try:
            self.model = SentenceTransformer(model_name)
            self.similarity_threshold = similarity_threshold
        except Exception as e:
            logger.warning("sentence_transformer_init_failed", error=str(e), model=model_name)
            self.model = None
            self.similarity_threshold = similarity_threshold

    def chunk(self, text: str, max_chunk_size: int = 1000, min_chunk_size: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """
        Chunk text semantically by grouping similar sentences
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum characters per chunk
            min_chunk_size: Minimum characters per chunk
            
        Returns:
            List of chunk dictionaries
        """
        if not self.model:
            # Fallback to sliding window if model not available
            return SlidingWindowChunkingStrategy().chunk(text, max_chunk_size=max_chunk_size, **kwargs)
        
        # Split into sentences
        sentences = self._split_sentences(text)
        if not sentences:
            return []
        
        # Generate embeddings for sentences
        try:
            sentence_embeddings = self.model.encode(sentences, show_progress_bar=False)
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            return SlidingWindowChunkingStrategy().chunk(text, max_chunk_size=max_chunk_size, **kwargs)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, (sentence, embedding) in enumerate(zip(sentences, sentence_embeddings)):
            sentence_size = len(sentence)
            
            # Check if we should start a new chunk
            if current_chunk and current_size + sentence_size > max_chunk_size:
                # Finalize current chunk
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= min_chunk_size:
                    chunks.append({
                        "text": chunk_text,
                        "start": sum(len(s) for s in sentences[:i-len(current_chunk)]),
                        "end": sum(len(s) for s in sentences[:i]),
                        "index": len(chunks),
                        "quality_score": self._calculate_chunk_quality(chunk_text),
                        "strategy": "semantic",
                    })
                current_chunk = []
                current_size = 0
            
            # Check semantic similarity with previous sentence
            if current_chunk and i > 0:
                prev_embedding = sentence_embeddings[i - 1]
                similarity = self._cosine_similarity(embedding, prev_embedding)
                
                if similarity < self.similarity_threshold and current_size >= min_chunk_size:
                    # Start new chunk due to low similarity
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "start": sum(len(s) for s in sentences[:i-len(current_chunk)]),
                        "end": sum(len(s) for s in sentences[:i]),
                        "index": len(chunks),
                        "quality_score": self._calculate_chunk_quality(chunk_text),
                        "strategy": "semantic",
                    })
                    current_chunk = []
                    current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= min_chunk_size:
                chunks.append({
                    "text": chunk_text,
                    "start": sum(len(s) for s in sentences[:len(sentences)-len(current_chunk)]),
                    "end": len(text),
                    "index": len(chunks),
                    "quality_score": self._calculate_chunk_quality(chunk_text),
                    "strategy": "semantic",
                })
        
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting - can be enhanced with NLTK or spaCy
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vectors"""
        import numpy as np
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


class HierarchicalChunkingStrategy(BaseChunkingStrategy):
    """Hierarchical chunking preserving document structure"""

    def chunk(self, text: str, max_chunk_size: int = 1000, overlap: int = 200, **kwargs) -> List[Dict[str, Any]]:
        """
        Chunk text hierarchically preserving document structure
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        # Detect document structure
        sections = self._detect_sections(text)
        
        for section_idx, section in enumerate(sections):
            section_text = section["text"]
            section_level = section.get("level", 0)
            
            # If section is small enough, keep as single chunk
            if len(section_text) <= max_chunk_size:
                chunks.append({
                    "text": section_text,
                    "start": section["start"],
                    "end": section["end"],
                    "index": len(chunks),
                    "quality_score": self._calculate_chunk_quality(section_text),
                    "strategy": "hierarchical",
                    "section_level": section_level,
                    "section_title": section.get("title"),
                })
            else:
                # Split large sections using sliding window
                sub_chunks = self._chunk_section(section_text, max_chunk_size, overlap)
                for sub_idx, sub_chunk in enumerate(sub_chunks):
                    chunks.append({
                        "text": sub_chunk["text"],
                        "start": section["start"] + sub_chunk["start"],
                        "end": section["start"] + sub_chunk["end"],
                        "index": len(chunks),
                        "quality_score": self._calculate_chunk_quality(sub_chunk["text"]),
                        "strategy": "hierarchical",
                        "section_level": section_level,
                        "section_title": section.get("title"),
                        "sub_chunk_index": sub_idx,
                    })
        
        return chunks

    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """Detect document sections based on headers and structure"""
        sections = []
        
        # Detect markdown-style headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split('\n')
        
        current_section = {"text": "", "start": 0, "level": 0, "title": None}
        current_start = 0
        
        for i, line in enumerate(lines):
            header_match = re.match(header_pattern, line)
            
            if header_match:
                # Save previous section
                if current_section["text"]:
                    current_section["end"] = current_start
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_start = sum(len(l) + 1 for l in lines[:i])
                current_section = {
                    "text": "",
                    "start": current_start,
                    "level": level,
                    "title": title,
                }
            else:
                current_section["text"] += line + "\n"
        
        # Add final section
        if current_section["text"]:
            current_section["end"] = len(text)
            sections.append(current_section)
        
        # If no headers found, treat entire text as one section
        if not sections:
            sections.append({
                "text": text,
                "start": 0,
                "end": len(text),
                "level": 0,
                "title": None,
            })
        
        return sections

    def _chunk_section(self, text: str, max_chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """Chunk a section using sliding window"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)
                
                if break_point > max_chunk_size * 0.5:
                    chunk_text = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append({
                "text": chunk_text.strip(),
                "start": start,
                "end": end,
            })
            
            start = end - overlap
            chunk_index += 1
        
        return chunks


class SlidingWindowChunkingStrategy(BaseChunkingStrategy):
    """Sliding window chunking with optimized overlap"""

    def chunk(self, text: str, chunk_size: int = 1000, overlap: int = 200, **kwargs) -> List[Dict[str, Any]]:
        """
        Chunk text using sliding window with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:
                    chunk_text = text[start:start + break_point + 1]
                    end = start + break_point + 1
            
            chunks.append({
                "text": chunk_text.strip(),
                "start": start,
                "end": end,
                "index": chunk_index,
                "quality_score": self._calculate_chunk_quality(chunk_text),
                "strategy": "sliding_window",
            })
            
            # Move start position with overlap
            start = end - overlap
            chunk_index += 1
        
        return chunks


class AdaptiveChunkingStrategy(BaseChunkingStrategy):
    """Adaptive chunking that adjusts based on content type"""

    def chunk(self, text: str, content_type: str = "general", **kwargs) -> List[Dict[str, Any]]:
        """
        Chunk text adaptively based on content type
        
        Args:
            text: Text to chunk
            content_type: Type of content (general, code, structured, conversational)
            **kwargs: Additional parameters
            
        Returns:
            List of chunk dictionaries
        """
        # Determine chunking parameters based on content type
        if content_type == "code":
            chunk_size = 500
            overlap = 100
            strategy = SlidingWindowChunkingStrategy()
        elif content_type == "structured":
            chunk_size = 1500
            overlap = 300
            strategy = HierarchicalChunkingStrategy()
        elif content_type == "conversational":
            chunk_size = 800
            overlap = 150
            strategy = SemanticChunkingStrategy()
        else:
            chunk_size = kwargs.get("chunk_size", 1000)
            overlap = kwargs.get("overlap", 200)
            strategy = SemanticChunkingStrategy()
        
        # Use appropriate strategy
        if isinstance(strategy, SemanticChunkingStrategy):
            return strategy.chunk(text, max_chunk_size=chunk_size, **kwargs)
        elif isinstance(strategy, HierarchicalChunkingStrategy):
            return strategy.chunk(text, max_chunk_size=chunk_size, overlap=overlap, **kwargs)
        else:
            return strategy.chunk(text, chunk_size=chunk_size, overlap=overlap, **kwargs)


def get_chunking_strategy(strategy_name: str = "adaptive", **kwargs) -> BaseChunkingStrategy:
    """
    Get chunking strategy instance
    
    Args:
        strategy_name: Name of the strategy
        **kwargs: Strategy-specific parameters
        
    Returns:
        Chunking strategy instance
    """
    strategy_map = {
        "semantic": SemanticChunkingStrategy,
        "hierarchical": HierarchicalChunkingStrategy,
        "sliding_window": SlidingWindowChunkingStrategy,
        "adaptive": AdaptiveChunkingStrategy,
    }
    
    strategy_class = strategy_map.get(strategy_name.lower(), AdaptiveChunkingStrategy)
    return strategy_class(**kwargs)

