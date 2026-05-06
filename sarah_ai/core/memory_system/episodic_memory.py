"""
Episodic Memory System
Stores specific events, conversations, and experiences with rich temporal context.
Features:
- Time-stamped memory storage
- Rich metadata (emotions, context, relationships)
- Temporal indexing and querying
- Memory consolidation to semantic memory
- Decay and cleanup mechanisms
"""

import json
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import heapq
from dataclasses import asdict

from .types import MemoryEntry, MemoryMetadata, MemoryType

class EpisodicMemory:
    """
    Episodic memory stores specific events and experiences.
    Like human episodic memory, it stores "what happened when and where".
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # In-memory storage for fast access
        self.memories: Dict[str, MemoryEntry] = {}

        # Temporal indexing
        self.time_index: Dict[str, List[str]] = defaultdict(list)  # date -> memory_ids
        self.context_index: Dict[str, List[str]] = defaultdict(list)  # context_key -> memory_ids
        self.emotion_index: Dict[str, List[str]] = defaultdict(list)  # emotion -> memory_ids

        # Memory strength tracking (for consolidation)
        self.memory_strengths: Dict[str, float] = {}

        print(f"[EPISODIC MEMORY]: Initialized at {storage_path}")

    async def store(self, entry: MemoryEntry):
        """Store an episodic memory"""
        memory_id = entry.metadata.memory_id

        # Store in memory
        self.memories[memory_id] = entry

        # Initialize memory strength
        self.memory_strengths[memory_id] = entry.metadata.importance

        # Update indices
        self._update_indices(entry)

        # Save to disk
        await self._save_memory(entry)

    async def retrieve(self, query: Dict[str, Any] = None,
                      limit: int = 10,
                      time_range: Tuple[datetime, datetime] = None) -> List[MemoryEntry]:
        """
        Retrieve episodic memories based on various criteria
        """
        candidates = list(self.memories.values())

        # Apply filters
        if query:
            candidates = self._filter_memories(candidates, query)

        if time_range:
            candidates = [m for m in candidates
                         if time_range[0] <= m.metadata.timestamp <= time_range[1]]

        # Sort by relevance (importance + recency + strength)
        candidates.sort(key=self._calculate_relevance_score, reverse=True)

        # Update access metadata
        for memory in candidates[:limit]:
            memory.metadata.access_count += 1
            memory.metadata.last_accessed = datetime.now()
            # Strengthen memory through access
            self.memory_strengths[memory.metadata.memory_id] *= 1.05

        return candidates[:limit]

    def _filter_memories(self, memories: List[MemoryEntry], query: Dict[str, Any]) -> List[MemoryEntry]:
        """Filter memories based on query criteria"""
        filtered = memories

        # Filter by source
        if "source" in query:
            filtered = [m for m in filtered if m.metadata.source == query["source"]]

        # Filter by tags
        if "tags" in query:
            query_tags = set(query["tags"])
            filtered = [m for m in filtered if set(m.metadata.tags).intersection(query_tags)]

        # Filter by emotional context
        if "emotion" in query:
            filtered = [m for m in filtered
                       if m.metadata.emotional_context.get("user_emotion") == query["emotion"] or
                          m.metadata.emotional_context.get("ai_emotion") == query["emotion"]]

        # Filter by content keywords
        if "keywords" in query:
            keywords = [k.lower() for k in query["keywords"]]
            filtered = [m for m in filtered
                       if isinstance(m.content, str) and
                       any(k in m.content.lower() for k in keywords)]

        # Filter by context
        if "context" in query:
            context_filters = query["context"]
            filtered = [m for m in filtered
                       if all(m.metadata.context.get(k) == v for k, v in context_filters.items())]

        return filtered

    def _calculate_relevance_score(self, memory: MemoryEntry) -> float:
        """Calculate relevance score for memory ranking"""
        base_score = memory.metadata.importance

        # Recency boost (newer memories get slight boost)
        hours_old = (datetime.now() - memory.metadata.timestamp).total_seconds() / 3600
        recency_boost = max(0, 1.0 - (hours_old / 24.0)) * 0.2  # Boost decays over 24 hours

        # Access frequency boost
        access_boost = min(0.3, memory.metadata.access_count * 0.05)

        # Memory strength boost
        strength_boost = self.memory_strengths.get(memory.metadata.memory_id, 0.5) * 0.1

        # Emotional intensity boost
        emotional_boost = 0.0
        if memory.metadata.emotional_context:
            intensity = memory.metadata.emotional_context.get("intensity", 0.5)
            emotional_boost = intensity * 0.1

        return base_score + recency_boost + access_boost + strength_boost + emotional_boost

    def _update_indices(self, entry: MemoryEntry):
        """Update search indices for the memory"""
        memory_id = entry.metadata.memory_id

        # Time index (by date)
        date_key = entry.metadata.timestamp.date().isoformat()
        if memory_id not in self.time_index[date_key]:
            self.time_index[date_key].append(memory_id)

        # Context index
        for key, value in entry.metadata.context.items():
            context_key = f"{key}:{value}"
            if memory_id not in self.context_index[context_key]:
                self.context_index[context_key].append(memory_id)

        # Emotion index
        for emotion_type in ["user_emotion", "ai_emotion"]:
            emotion = entry.metadata.emotional_context.get(emotion_type)
            if emotion and memory_id not in self.emotion_index[emotion]:
                self.emotion_index[emotion].append(memory_id)

    async def _save_memory(self, entry: MemoryEntry):
        """Save memory to disk"""
        memory_file = self.storage_path / f"{entry.metadata.memory_id}.json"

        # Convert numpy array to list for JSON serialization
        data = asdict(entry)
        if entry.embedding is not None:
            data["embedding"] = entry.embedding.tolist()

        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    async def load(self):
        """Load all memories from disk"""
        if not self.storage_path.exists():
            return

        memory_files = list(self.storage_path.glob("*.json"))
        print(f"[EPISODIC MEMORY]: Loading {len(memory_files)} memories...")

        for memory_file in memory_files:
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruct MemoryEntry
                metadata_dict = data["metadata"].copy()
                # Parse timestamp from string to datetime
                if isinstance(metadata_dict.get("timestamp"), str):
                    metadata_dict["timestamp"] = datetime.fromisoformat(metadata_dict["timestamp"])
                if isinstance(metadata_dict.get("last_accessed"), str):
                    metadata_dict["last_accessed"] = datetime.fromisoformat(metadata_dict["last_accessed"])

                metadata = MemoryMetadata(**metadata_dict)
                entry = MemoryEntry(
                    content=data["content"],
                    content_type=data["content_type"],
                    embedding=np.array(data.get("embedding")) if data.get("embedding") else None,
                    metadata=metadata
                )

                # Add to memory
                self.memories[metadata.memory_id] = entry
                self.memory_strengths[metadata.memory_id] = metadata.importance

                # Update indices
                self._update_indices(entry)

            except Exception as e:
                print(f"[EPISODIC MEMORY]: Error loading {memory_file}: {e}")

        print(f"[EPISODIC MEMORY]: Loaded {len(self.memories)} memories")

    async def save(self):
        """Save all memories to disk"""
        for memory_id, entry in self.memories.items():
            await self._save_memory(entry)

    async def get_conversation_history(self, user_id: str = None,
                                     limit: int = 50,
                                     days_back: int = 7) -> List[MemoryEntry]:
        """Get conversation history for a user"""
        start_date = datetime.now() - timedelta(days=days_back)

        query = {"source": "conversation"}
        if user_id:
            query["context"] = {"user_id": user_id}

        return await self.retrieve(query=query, limit=limit, time_range=(start_date, datetime.now()))

    async def get_emotional_timeline(self, user_id: str = None,
                                   emotion: str = None,
                                   days_back: int = 30) -> List[Dict[str, Any]]:
        """Get emotional timeline for analysis"""
        start_date = datetime.now() - timedelta(days=days_back)

        query = {}
        if emotion:
            query["emotion"] = emotion
        if user_id:
            query["context"] = {"user_id": user_id}

        memories = await self.retrieve(query=query, time_range=(start_date, datetime.now()))

        timeline = []
        for memory in memories:
            timeline.append({
                "timestamp": memory.metadata.timestamp.isoformat(),
                "user_emotion": memory.metadata.emotional_context.get("user_emotion"),
                "ai_emotion": memory.metadata.emotional_context.get("ai_emotion"),
                "intensity": memory.metadata.emotional_context.get("intensity", 0.5),
                "content_preview": str(memory.content)[:100] if isinstance(memory.content, str) else "structured_data"
            })

        return sorted(timeline, key=lambda x: x["timestamp"])

    async def find_similar_memories(self, target_memory: MemoryEntry,
                                  limit: int = 5) -> List[Tuple[MemoryEntry, float]]:
        """Find memories similar to the target (basic implementation)"""
        similar = []

        for memory_id, memory in self.memories.items():
            if memory_id == target_memory.metadata.memory_id:
                continue

            # Simple similarity based on shared tags and context
            tag_similarity = len(set(memory.metadata.tags).intersection(set(target_memory.metadata.tags)))
            context_similarity = len(set(memory.metadata.context.keys()).intersection(set(target_memory.metadata.context.keys())))

            similarity_score = (tag_similarity + context_similarity) / max(1, len(target_memory.metadata.tags) + len(target_memory.metadata.context))

            if similarity_score > 0.1:  # Minimum threshold
                similar.append((memory, similarity_score))

        # Sort by similarity
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]

    async def consolidate_to_semantic(self, consolidation_engine) -> List[MemoryEntry]:
        """Get memories ready for consolidation to semantic memory"""
        # Find memories with high strength that are old enough for consolidation
        consolidation_candidates = []

        for memory_id, entry in self.memories.items():
            strength = self.memory_strengths.get(memory_id, 0)
            age_hours = (datetime.now() - entry.metadata.timestamp).total_seconds() / 3600

            # Consolidate if: high strength + old enough + accessed multiple times
            if (strength > 0.7 and age_hours > 24 and entry.metadata.access_count > 2):
                consolidation_candidates.append(entry)

        return consolidation_candidates[:10]  # Limit batch size

    async def apply_decay(self, decay_rate: float = 0.001):
        """Apply time-based decay to memory strengths"""
        current_time = datetime.now()

        for memory_id, entry in self.memories.items():
            age_hours = (current_time - entry.metadata.timestamp).total_seconds() / 3600
            decay_amount = decay_rate * age_hours

            # Decay based on access frequency (accessed memories decay slower)
            access_factor = 1.0 / (1.0 + entry.metadata.access_count * 0.1)
            total_decay = decay_amount * access_factor

            self.memory_strengths[memory_id] = max(0.1, self.memory_strengths[memory_id] - total_decay)

    async def cleanup_decayed_memories(self, threshold: float = 0.1):
        """Remove memories that have decayed below threshold"""
        to_remove = []

        for memory_id, strength in self.memory_strengths.items():
            if strength < threshold:
                to_remove.append(memory_id)

        for memory_id in to_remove:
            if memory_id in self.memories:
                # Remove from memory
                del self.memories[memory_id]
                del self.memory_strengths[memory_id]

                # Remove from indices
                self._remove_from_indices(memory_id)

                # Remove from disk
                memory_file = self.storage_path / f"{memory_id}.json"
                if memory_file.exists():
                    memory_file.unlink()

        if to_remove:
            print(f"[EPISODIC MEMORY]: Cleaned up {len(to_remove)} decayed memories")

    def _remove_from_indices(self, memory_id: str):
        """Remove memory from all indices"""
        # Remove from time index
        for date_key, memory_ids in self.time_index.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)

        # Remove from context index
        for context_key, memory_ids in self.context_index.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)

        # Remove from emotion index
        for emotion_key, memory_ids in self.emotion_index.items():
            if memory_id in memory_ids:
                memory_ids.remove(memory_id)

    async def get_stats(self) -> Dict[str, Any]:
        """Get episodic memory statistics"""
        if not self.memories:
            return {
                "total_memories": 0,
                "avg_importance": 0.0,
                "avg_access_count": 0.0,
                "date_range": None,
                "top_emotions": [],
                "storage_size_mb": 0.0
            }

        # Calculate statistics
        importances = [m.metadata.importance for m in self.memories.values()]
        access_counts = [m.metadata.access_count for m in self.memories.values()]
        timestamps = [m.metadata.timestamp for m in self.memories.values()]

        # Emotion distribution
        emotion_counts = defaultdict(int)
        for memory in self.memories.values():
            user_emotion = memory.metadata.emotional_context.get("user_emotion")
            ai_emotion = memory.metadata.emotional_context.get("ai_emotion")
            if user_emotion:
                emotion_counts[f"user_{user_emotion}"] += 1
            if ai_emotion:
                emotion_counts[f"ai_{ai_emotion}"] += 1

        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.json"))

        return {
            "total_memories": len(self.memories),
            "avg_importance": sum(importances) / len(importances),
            "avg_access_count": sum(access_counts) / len(access_counts),
            "date_range": {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat()
            } if timestamps else None,
            "top_emotions": top_emotions,
            "storage_size_mb": total_size / (1024 * 1024),
            "memory_types": {
                "conversation": len([m for m in self.memories.values() if m.metadata.source == "conversation"]),
                "observation": len([m for m in self.memories.values() if m.metadata.source == "observation"]),
                "learning": len([m for m in self.memories.values() if m.metadata.source == "learning"])
            }
        }

    async def export(self) -> Dict[str, Any]:
        """Export all episodic memories"""
        return {
            "memories": {mid: asdict(entry) for mid, entry in self.memories.items()},
            "memory_strengths": self.memory_strengths.copy(),
            "indices": {
                "time_index": dict(self.time_index),
                "context_index": dict(self.context_index),
                "emotion_index": dict(self.emotion_index)
            }
        }

    async def import_data(self, data: Dict[str, Any]):
        """Import episodic memories"""
        # Clear existing data
        self.memories.clear()
        self.memory_strengths.clear()
        self.time_index.clear()
        self.context_index.clear()
        self.emotion_index.clear()

        # Import memories
        for memory_id, entry_data in data.get("memories", {}).items():
            metadata = MemoryMetadata(**entry_data["metadata"])
            entry = MemoryEntry(
                content=entry_data["content"],
                content_type=entry_data["content_type"],
                embedding=np.array(entry_data.get("embedding")) if entry_data.get("embedding") else None,
                metadata=metadata
            )

            self.memories[memory_id] = entry
            self._update_indices(entry)

        # Import strengths
        self.memory_strengths.update(data.get("memory_strengths", {}))

        print(f"[EPISODIC MEMORY]: Imported {len(self.memories)} memories")