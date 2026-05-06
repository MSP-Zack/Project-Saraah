"""
Memory Retrieval Engine
Advanced memory search and retrieval system.
Features:
- Semantic search with embeddings
- Multi-modal retrieval
- Context-aware ranking
- Emotional filtering
- Temporal queries
- Relationship-based retrieval
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import math
import re

from .types import MemoryEntry, MemoryMetadata, MemoryType

class MemoryRetrievalEngine:
    """
    Advanced memory retrieval system that combines multiple search strategies
    and ranking algorithms to find the most relevant memories.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Search indexes
        self.content_index: Dict[str, Set[str]] = defaultdict(set)  # word -> memory_ids
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> memory_ids
        self.context_index: Dict[str, Set[str]] = defaultdict(set)  # context -> memory_ids
        self.emotion_index: Dict[str, List[Tuple[str, float]]] = defaultdict(list)  # emotion -> [(memory_id, intensity), ...]
        self.temporal_index: Dict[str, List[str]] = defaultdict(list)  # date_key -> memory_ids
        self.relationship_index: Dict[str, Set[str]] = defaultdict(set)  # relationship -> memory_ids

        # Memory cache for fast access
        self.memory_cache: Dict[str, MemoryEntry] = {}

        # Search configuration
        self.search_weights = {
            "semantic_similarity": 0.4,
            "temporal_recency": 0.2,
            "emotional_relevance": 0.15,
            "importance": 0.15,
            "context_match": 0.1
        }

        print(f"[RETRIEVAL ENGINE]: Initialized at {storage_path}")

    async def index_memory(self, entry: MemoryEntry):
        """Index a memory entry for fast retrieval"""
        memory_id = entry.metadata.memory_id
        self.memory_cache[memory_id] = entry

        # Index content (simple word-based for now)
        if isinstance(entry.content, str):
            words = self._tokenize_text(entry.content)
            for word in words:
                self.content_index[word].add(memory_id)
        elif isinstance(entry.content, dict):
            # Index structured content
            content_text = json.dumps(entry.content)
            words = self._tokenize_text(content_text)
            for word in words:
                self.content_index[word].add(memory_id)

        # Index tags
        for tag in entry.metadata.tags:
            self.tag_index[tag].add(memory_id)

        # Index context
        if entry.metadata.context:
            context_words = self._tokenize_text(entry.metadata.context)
            for word in context_words:
                self.context_index[word].add(memory_id)

        # Index emotions
        if entry.metadata.emotional_context:
            for emotion, intensity in entry.metadata.emotional_context.items():
                self.emotion_index[emotion].append((memory_id, intensity))

        # Index temporal
        date_key = entry.metadata.timestamp.strftime("%Y-%m-%d")
        self.temporal_index[date_key].append(memory_id)

        # Index relationships
        for relationship in entry.metadata.relationships:
            self.relationship_index[relationship].add(memory_id)

    def _tokenize_text(self, text: str) -> List[str]:
        """Simple text tokenization"""
        # Convert to lowercase and split on non-word characters
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words (basic list)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'}
        return [word for word in words if word not in stop_words and len(word) > 2]

    async def search(self, query: str, filters: Dict[str, Any] = None,
                    limit: int = 20) -> List[Tuple[MemoryEntry, float]]:
        """
        Perform advanced memory search with ranking

        Args:
            query: Search query string
            filters: Optional filters (memory_type, date_range, emotions, etc.)
            limit: Maximum number of results to return

        Returns:
            List of (memory_entry, relevance_score) tuples
        """
        if filters is None:
            filters = {}

        # Get candidate memories
        candidate_ids = await self._get_candidate_memories(query, filters)

        if not candidate_ids:
            return []

        # Score and rank candidates
        scored_results = []
        for memory_id in candidate_ids:
            if memory_id in self.memory_cache:
                entry = self.memory_cache[memory_id]
                score = await self._calculate_relevance_score(entry, query, filters)
                scored_results.append((entry, score))

        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results[:limit]

    async def _get_candidate_memories(self, query: str, filters: Dict[str, Any]) -> Set[str]:
        """Get candidate memory IDs that match the query and filters"""
        candidates = set()

        # Text-based search
        query_words = self._tokenize_text(query)
        if query_words:
            # Find memories containing any of the query words
            word_candidates = set()
            for word in query_words:
                word_candidates.update(self.content_index.get(word, set()))
                word_candidates.update(self.context_index.get(word, set()))

            if word_candidates:
                candidates.update(word_candidates)

        # Tag-based filtering
        if "tags" in filters:
            tag_candidates = set()
            for tag in filters["tags"]:
                tag_candidates.update(self.tag_index.get(tag, set()))

            if tag_candidates:
                if candidates:
                    candidates = candidates.intersection(tag_candidates)
                else:
                    candidates = tag_candidates

        # Memory type filtering
        if "memory_type" in filters:
            type_candidates = set()
            for memory_id, entry in self.memory_cache.items():
                if entry.metadata.memory_type == filters["memory_type"]:
                    type_candidates.add(memory_id)

            if type_candidates:
                if candidates:
                    candidates = candidates.intersection(type_candidates)
                else:
                    candidates = type_candidates

        # Date range filtering
        if "date_range" in filters:
            date_candidates = set()
            start_date, end_date = filters["date_range"]

            for date_key, memory_ids in self.temporal_index.items():
                try:
                    entry_date = datetime.strptime(date_key, "%Y-%m-%d").date()
                    if start_date <= entry_date <= end_date:
                        date_candidates.update(memory_ids)
                except ValueError:
                    continue

            if date_candidates:
                if candidates:
                    candidates = candidates.intersection(date_candidates)
                else:
                    candidates = date_candidates

        # Emotional filtering
        if "emotions" in filters:
            emotion_candidates = set()
            required_emotions = filters["emotions"]

            for emotion, min_intensity in required_emotions.items():
                for memory_id, intensity in self.emotion_index.get(emotion, []):
                    if intensity >= min_intensity:
                        emotion_candidates.add(memory_id)

            if emotion_candidates:
                if candidates:
                    candidates = candidates.intersection(emotion_candidates)
                else:
                    candidates = emotion_candidates

        # Relationship filtering
        if "relationships" in filters:
            rel_candidates = set()
            for relationship in filters["relationships"]:
                rel_candidates.update(self.relationship_index.get(relationship, set()))

            if rel_candidates:
                if candidates:
                    candidates = candidates.intersection(rel_candidates)
                else:
                    candidates = rel_candidates

        # If no specific filters, return all memories (limited)
        if not candidates and not any(k in filters for k in ["tags", "memory_type", "date_range", "emotions", "relationships"]):
            candidates = set(self.memory_cache.keys())

        return candidates

    async def _calculate_relevance_score(self, entry: MemoryEntry, query: str,
                                       filters: Dict[str, Any]) -> float:
        """Calculate relevance score for a memory entry"""
        score = 0.0

        # Semantic similarity (basic text matching for now)
        semantic_score = self._calculate_semantic_similarity(entry, query)
        score += semantic_score * self.search_weights["semantic_similarity"]

        # Temporal recency
        temporal_score = self._calculate_temporal_score(entry.metadata.timestamp)
        score += temporal_score * self.search_weights["temporal_recency"]

        # Emotional relevance
        emotional_score = self._calculate_emotional_relevance(entry, filters.get("current_emotions", {}))
        score += emotional_score * self.search_weights["emotional_relevance"]

        # Importance
        importance_score = entry.metadata.importance
        score += importance_score * self.search_weights["importance"]

        # Context match
        context_score = self._calculate_context_match(entry, filters.get("context", ""))
        score += context_score * self.search_weights["context_match"]

        return score

    def _calculate_semantic_similarity(self, entry: MemoryEntry, query: str) -> float:
        """Calculate semantic similarity between entry and query"""
        query_words = set(self._tokenize_text(query))

        # Get entry text
        if isinstance(entry.content, str):
            entry_words = set(self._tokenize_text(entry.content))
        elif isinstance(entry.content, dict):
            entry_text = json.dumps(entry.content)
            entry_words = set(self._tokenize_text(entry_text))
        else:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(entry_words))
        union = len(query_words.union(entry_words))

        return intersection / union if union > 0 else 0.0

    def _calculate_temporal_score(self, timestamp: datetime) -> float:
        """Calculate recency score (newer = higher score)"""
        now = datetime.now()
        hours_old = (now - timestamp).total_seconds() / 3600

        # Exponential decay: score = e^(-hours_old/24) for daily decay
        # This gives ~0.37 score for 24h old, ~0.14 for 48h old, etc.
        return math.exp(-hours_old / 24)

    def _calculate_emotional_relevance(self, entry: MemoryEntry, current_emotions: Dict[str, float]) -> float:
        """Calculate emotional relevance score"""
        if not entry.metadata.emotional_context or not current_emotions:
            return 0.5  # Neutral score

        total_similarity = 0.0
        emotion_count = 0

        for emotion, current_intensity in current_emotions.items():
            if emotion in entry.metadata.emotional_context:
                entry_intensity = entry.metadata.emotional_context[emotion]
                similarity = 1.0 - abs(current_intensity - entry_intensity)
                total_similarity += similarity
                emotion_count += 1

        return total_similarity / emotion_count if emotion_count > 0 else 0.5

    def _calculate_context_match(self, entry: MemoryEntry, query_context: str) -> float:
        """Calculate context matching score"""
        if not query_context or not entry.metadata.context:
            return 0.5

        query_context_words = set(self._tokenize_text(query_context))
        entry_context_words = set(self._tokenize_text(entry.metadata.context))

        intersection = len(query_context_words.intersection(entry_context_words))
        union = len(query_context_words.union(entry_context_words))

        return intersection / union if union > 0 else 0.0

    async def find_similar_memories(self, reference_memory: MemoryEntry,
                                  limit: int = 10) -> List[Tuple[MemoryEntry, float]]:
        """Find memories similar to a reference memory"""
        # Use the reference memory's content and context as query
        query_parts = []

        if isinstance(reference_memory.content, str):
            query_parts.append(reference_memory.content)
        elif isinstance(reference_memory.content, dict):
            query_parts.append(json.dumps(reference_memory.content))

        if reference_memory.metadata.context:
            query_parts.append(reference_memory.metadata.context)

        query = " ".join(query_parts)

        # Create filters based on reference memory
        filters = {
            "memory_type": reference_memory.metadata.memory_type,
            "current_emotions": reference_memory.metadata.emotional_context or {}
        }

        # Exclude the reference memory itself
        results = await self.search(query, filters, limit + 1)
        results = [(entry, score) for entry, score in results
                  if entry.metadata.memory_id != reference_memory.metadata.memory_id]

        return results[:limit]

    async def get_conversation_context(self, current_context: str,
                                     conversation_history: List[Dict[str, Any]],
                                     limit: int = 5) -> List[MemoryEntry]:
        """Get relevant memories for conversation context"""
        # Extract key topics and entities from conversation
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_history[-10:]])
        conversation_text += " " + current_context

        # Search for relevant memories
        results = await self.search(conversation_text, limit=limit * 2)

        # Filter and rank for conversation relevance
        conversation_memories = []
        for entry, score in results:
            # Boost score for recent conversational memories
            if entry.metadata.source == "conversation":
                score *= 1.2

            # Boost score for memories with emotional context
            if entry.metadata.emotional_context:
                score *= 1.1

            conversation_memories.append((entry, score))

        conversation_memories.sort(key=lambda x: x[1], reverse=True)
        return [entry for entry, _ in conversation_memories[:limit]]

    async def get_temporal_memories(self, start_date: datetime, end_date: datetime,
                                  limit: int = 50) -> List[MemoryEntry]:
        """Get memories within a time range"""
        filters = {
            "date_range": (start_date.date(), end_date.date())
        }

        results = await self.search("", filters, limit)
        return [entry for entry, _ in results]

    async def get_emotion_based_memories(self, emotions: Dict[str, float],
                                       limit: int = 20) -> List[MemoryEntry]:
        """Get memories matching emotional criteria"""
        filters = {
            "emotions": emotions
        }

        results = await self.search("", filters, limit)
        return [entry for entry, _ in results]

    async def rebuild_index(self):
        """Rebuild search indexes from all cached memories"""
        # Clear existing indexes
        self.content_index.clear()
        self.tag_index.clear()
        self.context_index.clear()
        self.emotion_index.clear()
        self.temporal_index.clear()
        self.relationship_index.clear()

        # Re-index all memories
        for memory_id, entry in self.memory_cache.items():
            await self.index_memory(entry)

        print(f"[RETRIEVAL ENGINE]: Rebuilt index for {len(self.memory_cache)} memories")

    async def save_index(self):
        """Save search indexes to disk"""
        index_data = {
            "content_index": {word: list(ids) for word, ids in self.content_index.items()},
            "tag_index": {tag: list(ids) for tag, ids in self.tag_index.items()},
            "context_index": {word: list(ids) for word, ids in self.context_index.items()},
            "emotion_index": dict(self.emotion_index),
            "temporal_index": dict(self.temporal_index),
            "relationship_index": {rel: list(ids) for rel, ids in self.relationship_index.items()}
        }

        index_file = self.storage_path / "search_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2)

    async def load_index(self):
        """Load search indexes from disk"""
        index_file = self.storage_path / "search_index.json"
        if not index_file.exists():
            return

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            # Restore indexes
            self.content_index = defaultdict(set, {k: set(v) for k, v in index_data.get("content_index", {}).items()})
            self.tag_index = defaultdict(set, {k: set(v) for k, v in index_data.get("tag_index", {}).items()})
            self.context_index = defaultdict(set, {k: set(v) for k, v in index_data.get("context_index", {}).items()})
            self.emotion_index = defaultdict(list, index_data.get("emotion_index", {}))
            self.temporal_index = defaultdict(list, index_data.get("temporal_index", {}))
            self.relationship_index = defaultdict(set, {k: set(v) for k, v in index_data.get("relationship_index", {}).items()})

            print(f"[RETRIEVAL ENGINE]: Loaded search index")

        except Exception as e:
            print(f"[RETRIEVAL ENGINE]: Error loading search index: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get retrieval engine statistics"""
        total_memories = len(self.memory_cache)
        total_content_words = len(self.content_index)
        total_tags = len(self.tag_index)
        total_emotions = len(self.emotion_index)

        # Index sizes
        index_sizes = {
            "content_index": sum(len(ids) for ids in self.content_index.values()),
            "tag_index": sum(len(ids) for ids in self.tag_index.values()),
            "context_index": sum(len(ids) for ids in self.context_index.values()),
            "emotion_index": sum(len(entries) for entries in self.emotion_index.values()),
            "temporal_index": sum(len(ids) for ids in self.temporal_index.values()),
            "relationship_index": sum(len(ids) for ids in self.relationship_index.values())
        }

        return {
            "total_memories": total_memories,
            "index_coverage": {
                "content_words": total_content_words,
                "tags": total_tags,
                "emotions": total_emotions
            },
            "index_sizes": index_sizes,
            "search_weights": self.search_weights.copy()
        }

    async def optimize_index(self):
        """Optimize search indexes for better performance"""
        # Remove empty entries
        self.content_index = defaultdict(set, {k: v for k, v in self.content_index.items() if v})
        self.tag_index = defaultdict(set, {k: v for k, v in self.tag_index.items() if v})
        self.context_index = defaultdict(set, {k: v for k, v in self.context_index.items() if v})
        self.emotion_index = defaultdict(list, {k: v for k, v in self.emotion_index.items() if v})
        self.temporal_index = defaultdict(list, {k: v for k, v in self.temporal_index.items() if v})
        self.relationship_index = defaultdict(set, {k: v for k, v in self.relationship_index.items() if v})

        print(f"[RETRIEVAL ENGINE]: Optimized search indexes")

    async def clear_cache(self):
        """Clear memory cache (keeps indexes)"""
        self.memory_cache.clear()
        print(f"[RETRIEVAL ENGINE]: Cleared memory cache")