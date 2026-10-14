"""
Emotional Memory System
Manages emotional states, relationships, and emotional intelligence.
Features:
- Emotional state tracking
- Relationship dynamics
- Emotional contagion
- Mood-based memory retrieval
- Empathy learning
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque, Counter
import math

from .types import MemoryEntry, MemoryMetadata, MemoryType

class EmotionalMemory:
    """
    Emotional memory stores emotional experiences, relationships, and emotional intelligence.
    Tracks emotional states over time and learns emotional patterns.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Emotional state tracking
        self.current_emotional_state: Dict[str, float] = {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "disgust": 0.0,
            "trust": 0.0,
            "anticipation": 0.0
        }

        # Emotional history (rolling window)
        self.emotional_history: deque = deque(maxlen=1000)

        # Relationship tracking
        self.relationships: Dict[str, Dict[str, Any]] = {}  # person_id -> relationship_data

        # Emotional patterns and triggers
        self.emotional_patterns: Dict[str, Dict[str, Any]] = {}  # pattern_id -> pattern_data
        self.emotional_triggers: Dict[str, List[Dict[str, Any]]] = {}  # trigger_type -> triggers

        # Empathy learning
        self.empathy_patterns: Dict[str, Dict[str, Any]] = {}  # situation -> empathy_response

        # Memory entries
        self.memory_entries: Dict[str, MemoryEntry] = {}

        print(f"[EMOTIONAL MEMORY]: Initialized at {storage_path}")

    async def store(self, entry: MemoryEntry):
        """Store emotional memory"""
        memory_id = entry.metadata.memory_id
        self.memory_entries[memory_id] = entry

        # Extract emotional content
        if isinstance(entry.content, dict):
            await self._process_emotional_data(entry)

        # Update emotional state if emotional context exists
        if entry.metadata.emotional_context:
            await self.update_emotional_state(entry.metadata.emotional_context)

        # Save to disk
        await self._save_entry(entry)

    async def _process_emotional_data(self, entry: MemoryEntry):
        """Process emotional data from memory entry"""
        content = entry.content

        if "emotional_state" in content:
            await self._store_emotional_state(entry, content["emotional_state"])
        elif "relationship" in content:
            await self._store_relationship(entry, content["relationship"])
        elif "emotional_pattern" in content:
            await self._store_emotional_pattern(entry, content["emotional_pattern"])
        elif "empathy_response" in content:
            await self._store_empathy_pattern(entry, content["empathy_response"])

    async def _store_emotional_state(self, entry: MemoryEntry, emotional_state: Dict[str, Any]):
        """Store an emotional state snapshot"""
        state_data = {
            "timestamp": entry.metadata.timestamp.isoformat(),
            "emotions": emotional_state.get("emotions", {}),
            "intensity": emotional_state.get("intensity", 1.0),
            "context": entry.metadata.context,
            "trigger": emotional_state.get("trigger", ""),
            "source": entry.metadata.source,
            "memory_id": entry.metadata.memory_id
        }

        self.emotional_history.append(state_data)

        # Update current emotional state
        await self.update_emotional_state(emotional_state.get("emotions", {}))

    async def _store_relationship(self, entry: MemoryEntry, relationship: Dict[str, Any]):
        """Store relationship information"""
        person_id = relationship.get("person_id", f"person_{entry.metadata.memory_id}")

        if person_id not in self.relationships:
            self.relationships[person_id] = {
                "person_id": person_id,
                "name": relationship.get("name", "Unknown"),
                "relationship_type": relationship.get("relationship_type", "acquaintance"),
                "trust_level": relationship.get("trust_level", 0.5),
                "emotional_bond": relationship.get("emotional_bond", 0.0),
                "interaction_count": 0,
                "last_interaction": None,
                "shared_memories": [],
                "emotional_history": [],
                "personality_traits": relationship.get("personality_traits", {}),
                "communication_style": relationship.get("communication_style", {}),
                "created": entry.metadata.timestamp.isoformat(),
                "last_updated": entry.metadata.timestamp.isoformat()
            }

        rel = self.relationships[person_id]
        rel["interaction_count"] += 1
        rel["last_interaction"] = entry.metadata.timestamp.isoformat()
        rel["last_updated"] = entry.metadata.timestamp.isoformat()

        # Update emotional bond based on interaction
        if "emotional_context" in relationship:
            bond_change = self._calculate_bond_change(relationship["emotional_context"])
            rel["emotional_bond"] = max(-1.0, min(1.0, rel["emotional_bond"] + bond_change))

        # Store shared memory
        rel["shared_memories"].append(entry.metadata.memory_id)

        # Keep only recent memories
        if len(rel["shared_memories"]) > 50:
            rel["shared_memories"] = rel["shared_memories"][-50:]

        # Update emotional history
        if entry.metadata.emotional_context:
            rel["emotional_history"].append({
                "timestamp": entry.metadata.timestamp.isoformat(),
                "emotions": entry.metadata.emotional_context,
                "context": entry.metadata.context
            })

            # Keep only recent emotional history
            if len(rel["emotional_history"]) > 20:
                rel["emotional_history"] = rel["emotional_history"][-20:]

    def _calculate_bond_change(self, emotional_context: Dict[str, float]) -> float:
        """Calculate how much the emotional context affects relationship bond"""
        positive_emotions = emotional_context.get("joy", 0) + emotional_context.get("trust", 0)
        negative_emotions = emotional_context.get("anger", 0) + emotional_context.get("disgust", 0)

        bond_change = (positive_emotions - negative_emotions) * 0.1
        return bond_change

    async def _store_emotional_pattern(self, entry: MemoryEntry, pattern: Dict[str, Any]):
        """Store an emotional pattern"""
        pattern_id = pattern.get("id", f"pattern_{entry.metadata.memory_id}")

        self.emotional_patterns[pattern_id] = {
            "id": pattern_id,
            "trigger_situation": pattern.get("trigger_situation", ""),
            "emotional_response": pattern.get("emotional_response", {}),
            "context_conditions": pattern.get("context_conditions", {}),
            "frequency": pattern.get("frequency", 1),
            "success_rate": pattern.get("success_rate", 0.5),
            "last_triggered": None,
            "source_memories": [entry.metadata.memory_id],
            "created": entry.metadata.timestamp.isoformat(),
            "last_updated": entry.metadata.timestamp.isoformat()
        }

    async def _store_empathy_pattern(self, entry: MemoryEntry, empathy: Dict[str, Any]):
        """Store an empathy response pattern"""
        situation = empathy.get("situation", "general")

        if situation not in self.empathy_patterns:
            self.empathy_patterns[situation] = {
                "situation": situation,
                "empathy_responses": [],
                "success_count": 0,
                "total_count": 0,
                "avg_effectiveness": 0.0,
                "created": entry.metadata.timestamp.isoformat()
            }

        pattern = self.empathy_patterns[situation]
        pattern["empathy_responses"].append({
            "response": empathy.get("response", ""),
            "emotional_context": empathy.get("emotional_context", {}),
            "effectiveness": empathy.get("effectiveness", 0.5),
            "memory_id": entry.metadata.memory_id,
            "timestamp": entry.metadata.timestamp.isoformat()
        })

        # Update statistics
        pattern["total_count"] += 1
        if empathy.get("success", False):
            pattern["success_count"] += 1

        effectiveness = empathy.get("effectiveness", 0.5)
        current_avg = pattern["avg_effectiveness"]
        pattern["avg_effectiveness"] = (current_avg * (pattern["total_count"] - 1) + effectiveness) / pattern["total_count"]

    async def update_emotional_state(self, emotions: Dict[str, float]):
        """Update current emotional state"""
        decay_rate = 0.1  # How quickly emotions decay

        # Decay existing emotions
        for emotion in self.current_emotional_state:
            self.current_emotional_state[emotion] *= (1 - decay_rate)

        # Add new emotions
        for emotion, intensity in emotions.items():
            if emotion in self.current_emotional_state:
                self.current_emotional_state[emotion] = min(1.0, self.current_emotional_state[emotion] + intensity)

        # Normalize emotions (optional - can allow multiple emotions simultaneously)
        total_intensity = sum(self.current_emotional_state.values())
        if total_intensity > 1.0:
            for emotion in self.current_emotional_state:
                self.current_emotional_state[emotion] /= total_intensity

    async def get_current_emotional_state(self) -> Dict[str, float]:
        """Get current emotional state"""
        return self.current_emotional_state.copy()

    async def get_emotional_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get emotional history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = []
        for state in self.emotional_history:
            state_time = datetime.fromisoformat(state["timestamp"])
            if state_time >= cutoff_time:
                history.append(state)

        return history

    async def get_relationship_status(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Get relationship status for a person"""
        return self.relationships.get(person_id)

    async def get_all_relationships(self) -> List[Dict[str, Any]]:
        """Get all relationships"""
        return list(self.relationships.values())

    async def predict_emotional_response(self, situation: str, context: Dict[str, Any] = None) -> Dict[str, float]:
        """Predict emotional response to a situation"""
        predicted_emotions = {emotion: 0.0 for emotion in self.current_emotional_state.keys()}

        # Look for matching patterns
        for pattern_id, pattern in self.emotional_patterns.items():
            if self._matches_situation(pattern["trigger_situation"], situation, context):
                # Add predicted emotions
                response_emotions = pattern.get("emotional_response", {})
                for emotion, intensity in response_emotions.items():
                    if emotion in predicted_emotions:
                        predicted_emotions[emotion] += intensity * pattern.get("success_rate", 0.5)

        # Factor in current emotional state (emotional contagion)
        for emotion, intensity in self.current_emotional_state.items():
            predicted_emotions[emotion] += intensity * 0.3  # 30% influence from current state

        # Normalize
        total = sum(predicted_emotions.values())
        if total > 0:
            for emotion in predicted_emotions:
                predicted_emotions[emotion] /= total

        return predicted_emotions

    def _matches_situation(self, pattern_situation: str, current_situation: str,
                          context: Dict[str, Any] = None) -> bool:
        """Check if a pattern matches the current situation"""
        # Simple string matching (could be enhanced with NLP)
        if pattern_situation.lower() in current_situation.lower():
            return True

        # Check context conditions
        if context:
            # This would be more sophisticated in a real implementation
            return True

        return False

    async def get_empathy_response(self, situation: str, user_emotions: Dict[str, float]) -> Optional[str]:
        """Get an appropriate empathy response"""
        best_response = None
        best_score = 0.0

        for situation_key, pattern in self.empathy_patterns.items():
            if situation_key.lower() in situation.lower() or situation_key == "general":
                for response_data in pattern["empathy_responses"]:
                    score = self._calculate_empathy_match(response_data, user_emotions, pattern["avg_effectiveness"])

                    if score > best_score:
                        best_response = response_data["response"]
                        best_score = score

        return best_response

    def _calculate_empathy_match(self, response_data: Dict[str, Any],
                               user_emotions: Dict[str, float],
                               avg_effectiveness: float) -> float:
        """Calculate how well an empathy response matches"""
        score = avg_effectiveness

        # Check emotional alignment
        response_emotions = response_data.get("emotional_context", {})
        alignment = 0.0
        total = 0.0

        for emotion, intensity in user_emotions.items():
            if emotion in response_emotions:
                alignment += min(intensity, response_emotions[emotion])
            total += intensity

        if total > 0:
            score *= (alignment / total)

        return score

    async def apply_emotional_contagion(self, external_emotions: Dict[str, float],
                                       contagion_strength: float = 0.2):
        """Apply emotional contagion from external source"""
        for emotion, intensity in external_emotions.items():
            if emotion in self.current_emotional_state:
                current = self.current_emotional_state[emotion]
                self.current_emotional_state[emotion] = current + (intensity - current) * contagion_strength

    async def update_relationship_from_interaction(self, person_id: str,
                                                 interaction_quality: float,
                                                 emotional_context: Dict[str, float]):
        """Update relationship based on interaction"""
        if person_id not in self.relationships:
            return

        rel = self.relationships[person_id]

        # Update trust based on interaction quality
        trust_change = interaction_quality * 0.1
        rel["trust_level"] = max(0.0, min(1.0, rel["trust_level"] + trust_change))

        # Update emotional bond
        bond_change = self._calculate_bond_change(emotional_context)
        rel["emotional_bond"] = max(-1.0, min(1.0, rel["emotional_bond"] + bond_change))

        rel["last_updated"] = datetime.now().isoformat()

    async def get_mood_based_memories(self, current_mood: Dict[str, float],
                                    limit: int = 10) -> List[MemoryEntry]:
        """Retrieve memories that match current emotional state"""
        matching_memories = []

        for memory_id, entry in self.memory_entries.items():
            if entry.metadata.emotional_context:
                similarity = self._calculate_emotional_similarity(current_mood, entry.metadata.emotional_context)
                if similarity > 0.5:  # Similarity threshold
                    matching_memories.append((entry, similarity))

        # Sort by similarity and recency
        matching_memories.sort(key=lambda x: (x[1], x[0].metadata.timestamp), reverse=True)

        return [entry for entry, _ in matching_memories[:limit]]

    def _calculate_emotional_similarity(self, mood1: Dict[str, float], mood2: Dict[str, float]) -> float:
        """Calculate similarity between two emotional states"""
        emotions = set(mood1.keys()) | set(mood2.keys())
        total_similarity = 0.0

        for emotion in emotions:
            val1 = mood1.get(emotion, 0.0)
            val2 = mood2.get(emotion, 0.0)
            total_similarity += 1.0 - abs(val1 - val2)  # Closer values = higher similarity

        return total_similarity / len(emotions) if emotions else 0.0

    async def _save_entry(self, entry: MemoryEntry):
        """Save memory entry to disk"""
        entry_file = self.storage_path / f"{entry.metadata.memory_id}.json"

        data = {
            "memory_id": entry.metadata.memory_id,
            "content": entry.content,
            "content_type": entry.content_type,
            "metadata": {
                "importance": entry.metadata.importance,
                "source": entry.metadata.source,
                "context": entry.metadata.context,
                "emotional_context": entry.metadata.emotional_context,
                "tags": entry.metadata.tags,
                "timestamp": entry.metadata.timestamp.isoformat()
            }
        }

        with open(entry_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    async def load(self):
        """Load emotional memory from disk"""
        if not self.storage_path.exists():
            return

        entry_files = list(self.storage_path.glob("*.json"))
        print(f"[EMOTIONAL MEMORY]: Loading {len(entry_files)} entries...")

        for entry_file in entry_files:
            try:
                with open(entry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruct entry
                metadata = MemoryMetadata(
                    memory_id=data["memory_id"],
                    memory_type=MemoryType.EMOTIONAL,
                    timestamp=datetime.fromisoformat(data["metadata"]["timestamp"]),
                    importance=data["metadata"]["importance"],
                    confidence=0.8,
                    source=data["metadata"]["source"],
                    context=data["metadata"]["context"],
                    emotional_context=data["metadata"]["emotional_context"],
                    relationships=[],
                    tags=data["metadata"]["tags"]
                )

                entry = MemoryEntry(
                    content=data["content"],
                    content_type=data["content_type"],
                    metadata=metadata
                )

                # Process the entry
                self.memory_entries[data["memory_id"]] = entry
                await self._process_emotional_data(entry)

            except Exception as e:
                print(f"[EMOTIONAL MEMORY]: Error loading {entry_file}: {e}")

        print(f"[EMOTIONAL MEMORY]: Loaded {len(self.memory_entries)} emotional entries")

    async def save(self):
        """Save all emotional memory to disk"""
        for memory_id, entry in self.memory_entries.items():
            await self._save_entry(entry)

        # Save emotional state
        state_file = self.storage_path / "emotional_state.json"
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({
                "current_state": self.current_emotional_state,
                "history": list(self.emotional_history),
                "relationships": self.relationships,
                "patterns": self.emotional_patterns,
                "empathy": self.empathy_patterns
            }, f, indent=2)

    async def apply_decay(self, decay_rate: float = 0.001):
        """Apply decay to emotional memories"""
        # Emotional states decay over time
        for emotion in self.current_emotional_state:
            self.current_emotional_state[emotion] = max(0.0, self.current_emotional_state[emotion] - decay_rate)

        # Relationship bonds decay slightly
        for rel in self.relationships.values():
            rel["emotional_bond"] *= (1 - decay_rate * 0.1)  # Slower decay for relationships

    async def get_stats(self) -> Dict[str, Any]:
        """Get emotional memory statistics"""
        total_entries = len(self.memory_entries)
        total_relationships = len(self.relationships)
        total_patterns = len(self.emotional_patterns)

        # Current emotional state summary
        dominant_emotion = max(self.current_emotional_state.items(), key=lambda x: x[1])
        emotional_intensity = sum(self.current_emotional_state.values())

        # Relationship summary
        avg_trust = sum(r.get("trust_level", 0) for r in self.relationships.values()) / max(1, total_relationships)
        avg_bond = sum(r.get("emotional_bond", 0) for r in self.relationships.values()) / max(1, total_relationships)

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.json"))

        return {
            "total_entries": total_entries,
            "total_relationships": total_relationships,
            "total_patterns": total_patterns,
            "dominant_emotion": dominant_emotion[0],
            "emotional_intensity": emotional_intensity,
            "avg_relationship_trust": avg_trust,
            "avg_emotional_bond": avg_bond,
            "relationship_types": Counter(r.get("relationship_type", "unknown") for r in self.relationships.values()),
            "storage_size_mb": total_size / (1024 * 1024)
        }

    async def export(self) -> Dict[str, Any]:
        """Export all emotional memory"""
        return {
            "current_emotional_state": self.current_emotional_state.copy(),
            "emotional_history": list(self.emotional_history),
            "relationships": self.relationships.copy(),
            "emotional_patterns": self.emotional_patterns.copy(),
            "empathy_patterns": self.empathy_patterns.copy(),
            "memory_entries": {mid: {
                "content": entry.content,
                "content_type": entry.content_type,
                "metadata": {
                    "importance": entry.metadata.importance,
                    "source": entry.metadata.source,
                    "context": entry.metadata.context,
                    "emotional_context": entry.metadata.emotional_context,
                    "tags": entry.metadata.tags,
                    "timestamp": entry.metadata.timestamp.isoformat()
                }
            } for mid, entry in self.memory_entries.items()}
        }

    async def import_data(self, data: Dict[str, Any]):
        """Import emotional memory"""
        self.current_emotional_state.update(data.get("current_emotional_state", {}))
        self.emotional_history.extend(data.get("emotional_history", []))
        self.relationships.update(data.get("relationships", {}))
        self.emotional_patterns.update(data.get("emotional_patterns", {}))
        self.empathy_patterns.update(data.get("empathy_patterns", {}))

        # Import memory entries
        for memory_id, entry_data in data.get("memory_entries", {}).items():
            metadata = MemoryMetadata(
                memory_id=memory_id,
                memory_type=MemoryType.EMOTIONAL,
                timestamp=datetime.fromisoformat(entry_data["metadata"]["timestamp"]),
                importance=entry_data["metadata"]["importance"],
                confidence=0.8,
                source=entry_data["metadata"]["source"],
                context=entry_data["metadata"]["context"],
                emotional_context=entry_data["metadata"]["emotional_context"],
                relationships=[],
                tags=entry_data["metadata"]["tags"]
            )

            entry = MemoryEntry(
                content=entry_data["content"],
                content_type=entry_data["content_type"],
                metadata=metadata
            )

            self.memory_entries[memory_id] = entry

        print(f"[EMOTIONAL MEMORY]: Imported {len(self.memory_entries)} emotional entries")