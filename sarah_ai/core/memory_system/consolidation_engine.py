"""
Memory Consolidation Engine
Handles memory consolidation, strengthening, and migration between memory types.
Features:
- Episodic to semantic memory consolidation
- Memory strengthening based on access patterns
- Decay and forgetting mechanisms
- Memory reorganization
- Cross-memory relationship building
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import math
import heapq

from .types import MemoryEntry, MemoryMetadata, MemoryType

class MemoryConsolidationEngine:
    """
    Engine responsible for consolidating memories across different types,
    strengthening important memories, and managing memory decay.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Consolidation tracking
        self.consolidation_history: List[Dict[str, Any]] = []
        self.memory_access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.memory_strength: Dict[str, float] = defaultdict(float)

        # Consolidation rules
        self.consolidation_rules = {
            "episodic_to_semantic": {
                "min_access_count": 3,
                "min_age_days": 7,
                "similarity_threshold": 0.7,
                "importance_threshold": 0.6
            },
            "strengthening": {
                "access_boost": 0.1,
                "max_strength": 1.0,
                "decay_rate": 0.001
            },
            "decay": {
                "working_memory_decay": 0.1,  # Fast decay
                "episodic_decay": 0.01,       # Medium decay
                "semantic_decay": 0.001,     # Slow decay
                "procedural_decay": -0.001   # Actually improves with use
            }
        }

        print(f"[CONSOLIDATION ENGINE]: Initialized at {storage_path}")

    async def consolidate_memories(self, memory_system) -> List[Dict[str, Any]]:
        """
        Run memory consolidation process across all memory types.
        Returns a list of consolidation actions taken.
        """
        consolidation_actions = []

        # 1. Consolidate episodic to semantic memories
        episodic_actions = await self._consolidate_episodic_to_semantic(memory_system)
        consolidation_actions.extend(episodic_actions)

        # 2. Strengthen frequently accessed memories
        strengthening_actions = await self._strengthen_memories(memory_system)
        consolidation_actions.extend(strengthening_actions)

        # 3. Apply decay to old/unused memories
        decay_actions = await self._apply_memory_decay(memory_system)
        consolidation_actions.extend(decay_actions)

        # 4. Build cross-memory relationships
        relationship_actions = await self._build_memory_relationships(memory_system)
        consolidation_actions.extend(relationship_actions)

        # 5. Clean up decayed memories
        cleanup_actions = await self._cleanup_decayed_memories(memory_system)
        consolidation_actions.extend(cleanup_actions)

        # Record consolidation run
        self.consolidation_history.append({
            "timestamp": datetime.now().isoformat(),
            "actions_count": len(consolidation_actions),
            "actions": consolidation_actions
        })

        # Keep only recent history
        if len(self.consolidation_history) > 100:
            self.consolidation_history = self.consolidation_history[-100:]

        print(f"[CONSOLIDATION ENGINE]: Completed consolidation with {len(consolidation_actions)} actions")
        return consolidation_actions

    async def _consolidate_episodic_to_semantic(self, memory_system) -> List[Dict[str, Any]]:
        """Consolidate episodic memories into semantic memories"""
        actions = []
        rule = self.consolidation_rules["episodic_to_semantic"]

        # Get episodic memories that are old enough and frequently accessed
        candidate_memories = []
        for memory_id, entry in memory_system.episodic_memory.memory_entries.items():
            age_days = (datetime.now() - entry.metadata.timestamp).days
            access_count = len(self.memory_access_patterns.get(memory_id, []))

            if (age_days >= rule["min_age_days"] and
                access_count >= rule["min_access_count"] and
                entry.metadata.importance >= rule["importance_threshold"]):

                candidate_memories.append(entry)

        # Group similar memories
        memory_groups = self._group_similar_memories(candidate_memories, rule["similarity_threshold"])

        for group in memory_groups:
            if len(group) >= 2:  # Need at least 2 memories to consolidate
                consolidated_memory = await self._create_consolidated_memory(group)
                await memory_system.semantic_memory.store(consolidated_memory)

                actions.append({
                    "type": "episodic_to_semantic_consolidation",
                    "source_memories": [m.metadata.memory_id for m in group],
                    "consolidated_memory": consolidated_memory.metadata.memory_id,
                    "group_size": len(group)
                })

        return actions

    def _group_similar_memories(self, memories: List[MemoryEntry], threshold: float) -> List[List[MemoryEntry]]:
        """Group memories by similarity"""
        groups = []

        for memory in memories:
            # Find best matching group
            best_group = None
            best_similarity = 0.0

            for group in groups:
                similarity = self._calculate_memory_similarity(memory, group[0])
                if similarity >= threshold and similarity > best_similarity:
                    best_group = group
                    best_similarity = similarity

            if best_group:
                best_group.append(memory)
            else:
                groups.append([memory])

        return groups

    def _calculate_memory_similarity(self, memory1: MemoryEntry, memory2: MemoryEntry) -> float:
        """Calculate similarity between two memories"""
        similarity = 0.0
        factors = 0

        # Content similarity
        if isinstance(memory1.content, str) and isinstance(memory2.content, str):
            content_sim = self._calculate_text_similarity(memory1.content, memory2.content)
            similarity += content_sim
            factors += 1

        # Context similarity
        if memory1.metadata.context and memory2.metadata.context:
            context_sim = self._calculate_text_similarity(memory1.metadata.context, memory2.metadata.context)
            similarity += context_sim
            factors += 1

        # Tag overlap
        if memory1.metadata.tags and memory2.metadata.tags:
            tag_sim = len(set(memory1.metadata.tags) & set(memory2.metadata.tags)) / max(len(set(memory1.metadata.tags) | set(memory2.metadata.tags)), 1)
            similarity += tag_sim
            factors += 1

        # Emotional similarity
        if memory1.metadata.emotional_context and memory2.metadata.emotional_context:
            emotion_sim = self._calculate_emotional_similarity(memory1.metadata.emotional_context, memory2.metadata.emotional_context)
            similarity += emotion_sim
            factors += 1

        return similarity / factors if factors > 0 else 0.0

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_emotional_similarity(self, emotions1: Dict[str, float], emotions2: Dict[str, float]) -> float:
        """Calculate emotional similarity"""
        all_emotions = set(emotions1.keys()) | set(emotions2.keys())
        total_similarity = 0.0

        for emotion in all_emotions:
            val1 = emotions1.get(emotion, 0.0)
            val2 = emotions2.get(emotion, 0.0)
            total_similarity += 1.0 - abs(val1 - val2)

        return total_similarity / len(all_emotions) if all_emotions else 0.0

    async def _create_consolidated_memory(self, memory_group: List[MemoryEntry]) -> MemoryEntry:
        """Create a consolidated semantic memory from a group of episodic memories"""
        # Extract common patterns
        contents = []
        contexts = []
        tags = []
        emotions = []
        sources = []

        for memory in memory_group:
            if isinstance(memory.content, str):
                contents.append(memory.content)
            elif isinstance(memory.content, dict):
                contents.append(json.dumps(memory.content))

            if memory.metadata.context:
                contexts.append(memory.metadata.context)

            tags.extend(memory.metadata.tags)

            if memory.metadata.emotional_context:
                emotions.append(memory.metadata.emotional_context)

            sources.append(memory.metadata.source)

        # Create consolidated content
        consolidated_content = {
            "type": "consolidated_semantic",
            "source_memories": [m.metadata.memory_id for m in memory_group],
            "common_themes": self._extract_common_themes(contents),
            "generalized_context": self._generalize_context(contexts),
            "average_emotions": self._average_emotions(emotions),
            "frequency": len(memory_group),
            "time_span": {
                "start": min(m.metadata.timestamp for m in memory_group).isoformat(),
                "end": max(m.metadata.timestamp for m in memory_group).isoformat()
            }
        }

        # Create consolidated metadata
        consolidated_metadata = MemoryMetadata(
            memory_id=f"consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(memory_group)) % 10000}",
            memory_type=MemoryType.SEMANTIC,
            timestamp=datetime.now(),
            importance=sum(m.metadata.importance for m in memory_group) / len(memory_group),
            confidence=0.8,
            source="consolidation_engine",
            context=self._generalize_context(contexts),
            emotional_context=self._average_emotions(emotions),
            relationships=[m.metadata.memory_id for m in memory_group],
            tags=list(set(tags))  # Unique tags
        )

        return MemoryEntry(
            content=consolidated_content,
            content_type="structured",
            metadata=consolidated_metadata
        )

    def _extract_common_themes(self, contents: List[str]) -> List[str]:
        """Extract common themes from content"""
        all_words = []
        for content in contents:
            words = content.lower().split()
            all_words.extend(words)

        # Find most common words (excluding stop words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        word_counts = Counter(word for word in all_words if word not in stop_words and len(word) > 3)

        # Return top 5 most common words as themes
        return [word for word, _ in word_counts.most_common(5)]

    def _generalize_context(self, contexts: List[str]) -> str:
        """Generalize multiple contexts into one"""
        if not contexts:
            return ""

        # Simple approach: combine and find common elements
        all_context_words = []
        for context in contexts:
            words = context.lower().split()
            all_context_words.extend(words)

        word_counts = Counter(all_context_words)
        common_words = [word for word, count in word_counts.items() if count > len(contexts) * 0.5]

        return " ".join(common_words)

    def _average_emotions(self, emotions_list: List[Dict[str, float]]) -> Dict[str, float]:
        """Average multiple emotional contexts"""
        if not emotions_list:
            return {}

        all_emotions = set()
        for emotions in emotions_list:
            all_emotions.update(emotions.keys())

        averaged_emotions = {}
        for emotion in all_emotions:
            values = [emotions.get(emotion, 0.0) for emotions in emotions_list]
            averaged_emotions[emotion] = sum(values) / len(values)

        return averaged_emotions

    async def _strengthen_memories(self, memory_system) -> List[Dict[str, Any]]:
        """Strengthen memories based on access patterns"""
        actions = []
        rule = self.consolidation_rules["strengthening"]

        for memory_id, access_times in self.memory_access_patterns.items():
            if len(access_times) > 1:
                # Calculate access frequency
                recent_accesses = [t for t in access_times if (datetime.now() - t).days <= 30]
                access_frequency = len(recent_accesses) / 30  # accesses per day

                # Strengthen memory
                current_strength = self.memory_strength[memory_id]
                new_strength = min(rule["max_strength"], current_strength + rule["access_boost"] * access_frequency)

                if new_strength > current_strength:
                    self.memory_strength[memory_id] = new_strength

                    # Update memory importance if found
                    memory = self._find_memory_by_id(memory_system, memory_id)
                    if memory:
                        old_importance = memory.metadata.importance
                        memory.metadata.importance = min(1.0, old_importance + rule["access_boost"])

                        actions.append({
                            "type": "memory_strengthening",
                            "memory_id": memory_id,
                            "old_strength": current_strength,
                            "new_strength": new_strength,
                            "old_importance": old_importance,
                            "new_importance": memory.metadata.importance,
                            "access_frequency": access_frequency
                        })

        return actions

    async def _apply_memory_decay(self, memory_system) -> List[Dict[str, Any]]:
        """Apply decay to memories based on age and access patterns"""
        actions = []
        decay_rules = self.consolidation_rules["decay"]

        for memory_type, decay_rate in decay_rules.items():
            memory_store = self._get_memory_store(memory_system, memory_type)
            if not memory_store:
                continue

            for memory_id, entry in memory_store.memory_entries.items():
                age_days = (datetime.now() - entry.metadata.timestamp).days
                access_count = len(self.memory_access_patterns.get(memory_id, []))

                # Calculate decay factor
                decay_factor = decay_rate * age_days

                # Reduce decay for frequently accessed memories
                if access_count > 0:
                    decay_factor *= (1.0 / (1.0 + access_count))

                # Apply decay
                old_importance = entry.metadata.importance
                new_importance = max(0.1, old_importance - decay_factor)

                if new_importance < old_importance:
                    entry.metadata.importance = new_importance

                    actions.append({
                        "type": "memory_decay",
                        "memory_id": memory_id,
                        "memory_type": memory_type,
                        "old_importance": old_importance,
                        "new_importance": new_importance,
                        "age_days": age_days,
                        "access_count": access_count
                    })

        return actions

    async def _build_memory_relationships(self, memory_system) -> List[Dict[str, Any]]:
        """Build relationships between related memories"""
        actions = []

        # Get all memories
        all_memories = []
        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            memory_store = self._get_memory_store(memory_system, memory_type)
            if memory_store:
                all_memories.extend(memory_store.memory_entries.values())

        # Find related memories
        for i, memory1 in enumerate(all_memories):
            for memory2 in all_memories[i+1:]:
                if self._memories_are_related(memory1, memory2):
                    # Add relationship if not already present
                    if memory2.metadata.memory_id not in memory1.metadata.relationships:
                        memory1.metadata.relationships.append(memory2.metadata.memory_id)
                        actions.append({
                            "type": "relationship_added",
                            "memory1": memory1.metadata.memory_id,
                            "memory2": memory2.metadata.memory_id,
                            "relationship_type": "related"
                        })

                    if memory1.metadata.memory_id not in memory2.metadata.relationships:
                        memory2.metadata.relationships.append(memory1.metadata.memory_id)

        return actions

    def _memories_are_related(self, memory1: MemoryEntry, memory2: MemoryEntry) -> bool:
        """Check if two memories are related"""
        # Check for shared tags
        if set(memory1.metadata.tags) & set(memory2.metadata.tags):
            return True

        # Check for similar content
        if self._calculate_memory_similarity(memory1, memory2) > 0.5:
            return True

        # Check for temporal proximity (within 1 hour)
        time_diff = abs((memory1.metadata.timestamp - memory2.metadata.timestamp).total_seconds())
        if time_diff < 3600:  # 1 hour
            return True

        # Check for shared emotional context
        if (memory1.metadata.emotional_context and memory2.metadata.emotional_context and
            self._calculate_emotional_similarity(memory1.metadata.emotional_context, memory2.metadata.emotional_context) > 0.7):
            return True

        return False

    async def _cleanup_decayed_memories(self, memory_system) -> List[Dict[str, Any]]:
        """Clean up memories that have decayed below threshold"""
        actions = []
        decay_threshold = 0.2

        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            memory_store = self._get_memory_store(memory_system, memory_type)
            if not memory_store:
                continue

            to_remove = []
            for memory_id, entry in memory_store.memory_entries.items():
                if entry.metadata.importance < decay_threshold:
                    # Check if it's been accessed recently
                    recent_accesses = [t for t in self.memory_access_patterns.get(memory_id, [])
                                     if (datetime.now() - t).days <= 30]

                    if len(recent_accesses) == 0:
                        to_remove.append(memory_id)

            for memory_id in to_remove:
                del memory_store.memory_entries[memory_id]
                actions.append({
                    "type": "memory_cleanup",
                    "memory_id": memory_id,
                    "memory_type": memory_type,
                    "final_importance": memory_store.memory_entries[memory_id].metadata.importance if memory_id in memory_store.memory_entries else 0.0
                })

        return actions

    def _get_memory_store(self, memory_system, memory_type: str):
        """Get the appropriate memory store for a memory type"""
        type_map = {
            "working": memory_system.working_memory,
            "episodic": memory_system.episodic_memory,
            "semantic": memory_system.semantic_memory,
            "procedural": memory_system.procedural_memory
        }
        return type_map.get(memory_type)

    def _find_memory_by_id(self, memory_system, memory_id: str) -> Optional[MemoryEntry]:
        """Find a memory by ID across all stores"""
        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            memory_store = self._get_memory_store(memory_system, memory_type.value)
            if memory_store and memory_id in memory_store.memory_entries:
                return memory_store.memory_entries[memory_id]
        return None

    async def record_memory_access(self, memory_id: str):
        """Record that a memory was accessed"""
        self.memory_access_patterns[memory_id].append(datetime.now())

        # Keep only recent accesses
        recent_accesses = [t for t in self.memory_access_patterns[memory_id]
                          if (datetime.now() - t).days <= 90]  # 90 days
        self.memory_access_patterns[memory_id] = recent_accesses

    async def get_memory_strength(self, memory_id: str) -> float:
        """Get the strength of a memory"""
        return self.memory_strength.get(memory_id, 0.0)

    async def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get consolidation statistics"""
        total_accesses = sum(len(accesses) for accesses in self.memory_access_patterns.values())
        avg_strength = sum(self.memory_strength.values()) / max(1, len(self.memory_strength))

        recent_consolidations = [c for c in self.consolidation_history
                                if (datetime.now() - datetime.fromisoformat(c["timestamp"])).days <= 7]

        return {
            "total_memory_accesses": total_accesses,
            "unique_memories_accessed": len(self.memory_access_patterns),
            "average_memory_strength": avg_strength,
            "consolidation_runs": len(self.consolidation_history),
            "recent_consolidations": len(recent_consolidations),
            "total_consolidation_actions": sum(c["actions_count"] for c in recent_consolidations)
        }

    async def save(self):
        """Save consolidation state to disk"""
        data = {
            "consolidation_history": self.consolidation_history,
            "memory_access_patterns": {mid: [t.isoformat() for t in times]
                                     for mid, times in self.memory_access_patterns.items()},
            "memory_strength": dict(self.memory_strength),
            "consolidation_rules": self.consolidation_rules
        }

        file_path = self.storage_path / "consolidation_state.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    async def load(self):
        """Load consolidation state from disk"""
        file_path = self.storage_path / "consolidation_state.json"
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.consolidation_history = data.get("consolidation_history", [])
            self.memory_access_patterns = defaultdict(list, {
                mid: [datetime.fromisoformat(t) for t in times]
                for mid, times in data.get("memory_access_patterns", {}).items()
            })
            self.memory_strength = defaultdict(float, data.get("memory_strength", {}))
            self.consolidation_rules.update(data.get("consolidation_rules", {}))

            print(f"[CONSOLIDATION ENGINE]: Loaded consolidation state")

        except Exception as e:
            print(f"[CONSOLIDATION ENGINE]: Error loading consolidation state: {e}")

    async def reset_stats(self):
        """Reset consolidation statistics"""
        self.consolidation_history.clear()
        self.memory_access_patterns.clear()
        self.memory_strength.clear()
        print(f"[CONSOLIDATION ENGINE]: Reset consolidation statistics")