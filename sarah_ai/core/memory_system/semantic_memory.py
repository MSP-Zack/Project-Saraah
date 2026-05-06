"""
Semantic Memory System
Stores abstract knowledge, concepts, patterns, and user preferences.
Features:
- Concept abstraction from episodic memories
- User preference learning and storage
- Knowledge graph construction
- Pattern recognition and generalization
- Long-term knowledge consolidation
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import re

from .types import MemoryEntry, MemoryMetadata, MemoryType

class SemanticMemory:
    """
    Semantic memory stores abstract knowledge and patterns.
    Like human semantic memory, it stores "what things mean" and general knowledge.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Knowledge storage
        self.knowledge_base: Dict[str, Dict[str, Any]] = {}  # concept -> knowledge
        self.user_preferences: Dict[str, Dict[str, Any]] = {}  # user_id -> preferences
        self.concept_relationships: Dict[str, Set[str]] = defaultdict(set)  # concept -> related_concepts
        self.patterns: Dict[str, Dict[str, Any]] = {}  # pattern_id -> pattern_data

        # Memory entries for persistence
        self.memory_entries: Dict[str, MemoryEntry] = {}

        print(f"[SEMANTIC MEMORY]: Initialized at {storage_path}")

    async def store(self, entry: MemoryEntry):
        """Store semantic knowledge"""
        memory_id = entry.metadata.memory_id

        # Store the entry
        self.memory_entries[memory_id] = entry

        # Extract and store semantic knowledge
        if isinstance(entry.content, dict):
            await self._process_structured_knowledge(entry)
        elif isinstance(entry.content, str):
            await self._process_text_knowledge(entry)

        # Save to disk
        await self._save_entry(entry)

    async def _process_structured_knowledge(self, entry: MemoryEntry):
        """Process structured knowledge (preferences, facts, etc.)"""
        content = entry.content

        if "preference" in content:
            await self._store_user_preference(entry, content["preference"])
        elif "fact" in content:
            await self._store_fact(entry, content["fact"])
        elif "concept" in content:
            await self._store_concept(entry, content["concept"])
        elif "pattern" in content:
            await self._store_pattern(entry, content["pattern"])

    async def _process_text_knowledge(self, entry: MemoryEntry):
        """Extract semantic knowledge from text"""
        text = entry.content

        # Extract potential preferences
        preference_patterns = [
            r"I (?:really )?(like|love|hate|dislike) (.+)",
            r"My favorite (.+) is (.+)",
            r"I prefer (.+)",
            r"I'm interested in (.+)"
        ]

        for pattern in preference_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    pref_type, pref_value = match
                else:
                    pref_type = "interest"
                    pref_value = match

                preference = {
                    "category": pref_type,
                    "value": pref_value.strip(),
                    "confidence": 0.6,
                    "source_memory": entry.metadata.memory_id,
                    "last_updated": entry.metadata.timestamp.isoformat()
                }

                user_id = entry.metadata.context.get("user_id", "general")
                await self._store_user_preference_data(user_id, preference)

        # Extract concepts and relationships
        await self._extract_concepts_from_text(text, entry)

    async def _store_user_preference(self, entry: MemoryEntry, preference: Dict[str, Any]):
        """Store a user preference"""
        user_id = entry.metadata.context.get("user_id", "general")
        await self._store_user_preference_data(user_id, preference)

    async def _store_user_preference_data(self, user_id: str, preference: Dict[str, Any]):
        """Store preference data for a user"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        category = preference["category"]
        value = preference["value"]

        if category not in self.user_preferences[user_id]:
            self.user_preferences[user_id][category] = []

        # Check if preference already exists
        existing = None
        for pref in self.user_preferences[user_id][category]:
            if pref["value"].lower() == value.lower():
                existing = pref
                break

        if existing:
            # Update confidence and timestamp
            existing["confidence"] = min(1.0, existing["confidence"] + 0.1)
            existing["last_updated"] = preference["last_updated"]
            existing["access_count"] = existing.get("access_count", 0) + 1
        else:
            # Add new preference
            preference["access_count"] = 1
            self.user_preferences[user_id][category].append(preference)

    async def _store_fact(self, entry: MemoryEntry, fact: Dict[str, Any]):
        """Store a factual piece of knowledge"""
        fact_key = fact.get("key", f"fact_{entry.metadata.memory_id}")

        knowledge = {
            "type": "fact",
            "content": fact.get("content"),
            "category": fact.get("category", "general"),
            "confidence": fact.get("confidence", 0.8),
            "source_memories": [entry.metadata.memory_id],
            "last_updated": entry.metadata.timestamp.isoformat(),
            "verification_count": 1
        }

        self.knowledge_base[fact_key] = knowledge

    async def _store_concept(self, entry: MemoryEntry, concept: Dict[str, Any]):
        """Store a conceptual piece of knowledge"""
        concept_key = concept.get("name", f"concept_{entry.metadata.memory_id}")

        if concept_key not in self.knowledge_base:
            self.knowledge_base[concept_key] = {
                "type": "concept",
                "definition": concept.get("definition", ""),
                "examples": concept.get("examples", []),
                "related_concepts": concept.get("related", []),
                "confidence": concept.get("confidence", 0.7),
                "source_memories": [entry.metadata.memory_id],
                "last_updated": entry.metadata.timestamp.isoformat()
            }
        else:
            # Update existing concept
            existing = self.knowledge_base[concept_key]
            if concept.get("definition"):
                existing["definition"] = concept["definition"]
            if concept.get("examples"):
                existing["examples"].extend(concept["examples"])
                existing["examples"] = list(set(existing["examples"]))  # Remove duplicates
            existing["source_memories"].append(entry.metadata.memory_id)
            existing["last_updated"] = entry.metadata.timestamp.isoformat()

        # Update concept relationships
        for related in concept.get("related", []):
            self.concept_relationships[concept_key].add(related)
            self.concept_relationships[related].add(concept_key)

    async def _store_pattern(self, entry: MemoryEntry, pattern: Dict[str, Any]):
        """Store a recognized pattern"""
        pattern_id = pattern.get("id", f"pattern_{entry.metadata.memory_id}")

        self.patterns[pattern_id] = {
            "pattern": pattern.get("pattern"),
            "description": pattern.get("description"),
            "examples": pattern.get("examples", []),
            "frequency": pattern.get("frequency", 1),
            "confidence": pattern.get("confidence", 0.6),
            "source_memories": [entry.metadata.memory_id],
            "last_updated": entry.metadata.timestamp.isoformat()
        }

    async def _extract_concepts_from_text(self, text: str, entry: MemoryEntry):
        """Extract concepts and relationships from text"""
        # Simple concept extraction (could be enhanced with NLP)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)  # Proper nouns

        concepts = []
        for word in words:
            if len(word) > 3:  # Filter short words
                concepts.append(word.lower())

        # Store as concepts if we found meaningful ones
        if concepts:
            concept_data = {
                "name": f"text_concepts_{entry.metadata.memory_id}",
                "definition": f"Concepts extracted from: {text[:100]}...",
                "examples": concepts[:5],
                "related": concepts[1:] if len(concepts) > 1 else [],
                "confidence": 0.4
            }
            await self._store_concept(entry, concept_data)

    async def retrieve(self, query: str = None,
                      concept: str = None,
                      user_id: str = None,
                      category: str = None,
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve semantic knowledge
        """
        results = []

        # Search knowledge base
        if query:
            for key, knowledge in self.knowledge_base.items():
                if query.lower() in key.lower() or (isinstance(knowledge.get("content"), str) and query.lower() in knowledge["content"].lower()):
                    results.append(knowledge)

        # Get specific concept
        if concept and concept in self.knowledge_base:
            results.append(self.knowledge_base[concept])

        # Get user preferences
        if user_id and user_id in self.user_preferences:
            user_prefs = self.user_preferences[user_id]
            if category and category in user_prefs:
                results.extend(user_prefs[category])
            elif not category:
                for cat_prefs in user_prefs.values():
                    results.extend(cat_prefs)

        # Get patterns
        if query:
            for pattern_id, pattern_data in self.patterns.items():
                if query.lower() in pattern_data.get("description", "").lower():
                    results.append(pattern_data)

        # Sort by confidence and return top results
        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return results[:limit]

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get complete user profile from semantic memory"""
        if user_id not in self.user_preferences:
            return {"user_id": user_id, "preferences": {}, "insights": []}

        preferences = self.user_preferences[user_id]

        # Generate insights from preferences
        insights = []
        all_prefs = []
        for cat_prefs in preferences.values():
            all_prefs.extend(cat_prefs)

        # Find patterns in preferences
        categories = Counter(pref["category"] for pref in all_prefs)
        top_categories = categories.most_common(3)

        for category, count in top_categories:
            insights.append(f"Strong preference for {category} (mentioned {count} times)")

        return {
            "user_id": user_id,
            "preferences": preferences,
            "insights": insights,
            "total_preferences": len(all_prefs),
            "last_updated": max((pref["last_updated"] for cat_prefs in preferences.values() for pref in cat_prefs), default=None)
        }

    async def find_related_concepts(self, concept: str, depth: int = 2) -> Set[str]:
        """Find concepts related to the given concept"""
        visited = set()
        to_visit = {concept}
        current_depth = 0

        while to_visit and current_depth < depth:
            current_level = to_visit.copy()
            to_visit.clear()

            for current_concept in current_level:
                if current_concept not in visited:
                    visited.add(current_concept)
                    to_visit.update(self.concept_relationships[current_concept])

            current_depth += 1

        return visited - {concept}

    async def get_patterns(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve learned patterns"""
        if query:
            matching_patterns = []
            for pattern_id, pattern_data in self.patterns.items():
                if query.lower() in pattern_data.get("description", "").lower():
                    matching_patterns.append(pattern_data)
            return matching_patterns[:limit]
        else:
            return list(self.patterns.values())[:limit]

    async def consolidate_from_episodic(self, episodic_memories: List[MemoryEntry]):
        """Consolidate patterns from episodic memories into semantic knowledge"""
        # Analyze episodic memories for patterns
        conversation_patterns = await self._analyze_conversation_patterns(episodic_memories)
        preference_patterns = await self._analyze_preference_patterns(episodic_memories)

        # Store discovered patterns
        for pattern in conversation_patterns:
            await self._store_pattern_from_analysis(pattern)

        for pattern in preference_patterns:
            await self._store_preference_pattern(pattern)

    async def _analyze_conversation_patterns(self, memories: List[MemoryEntry]) -> List[Dict[str, Any]]:
        """Analyze episodic memories for conversation patterns"""
        patterns = []

        # Group by user
        user_conversations = defaultdict(list)
        for memory in memories:
            user_id = memory.metadata.context.get("user_id")
            if user_id:
                user_conversations[user_id].append(memory)

        # Analyze each user's conversation patterns
        for user_id, user_memories in user_conversations.items():
            if len(user_memories) < 5:  # Need minimum conversations for pattern analysis
                continue

            # Analyze response times, topics, emotional patterns
            topics = Counter()
            emotions = Counter()
            response_times = []

            for memory in user_memories:
                if memory.metadata.tags:
                    topics.update(memory.metadata.tags)

                user_emotion = memory.metadata.emotional_context.get("user_emotion")
                if user_emotion:
                    emotions[user_emotion] += 1

            # Create pattern if significant
            if len(topics) > 0:
                top_topics = topics.most_common(3)
                top_emotions = emotions.most_common(2)

                pattern = {
                    "id": f"user_{user_id}_conversation_pattern",
                    "description": f"User {user_id} frequently discusses {', '.join(t[0] for t in top_topics)}",
                    "pattern": {
                        "user_id": user_id,
                        "top_topics": dict(top_topics),
                        "emotional_tendencies": dict(top_emotions)
                    },
                    "frequency": len(user_memories),
                    "confidence": min(0.9, len(user_memories) / 20.0),  # Higher confidence with more data
                    "source_memories": [m.metadata.memory_id for m in user_memories]
                }
                patterns.append(pattern)

        return patterns

    async def _analyze_preference_patterns(self, memories: List[MemoryEntry]) -> List[Dict[str, Any]]:
        """Analyze episodic memories for preference patterns"""
        patterns = []

        # Extract preferences from memories
        all_preferences = []
        for memory in memories:
            if isinstance(memory.content, str):
                # Look for preference indicators
                pref_matches = re.findall(r'I (?:really )?(like|love|prefer|hate|dislike) (.+?)(?:\.|!|\?|$)', memory.content, re.IGNORECASE)
                for pref_type, pref_value in pref_matches:
                    all_preferences.append({
                        "type": pref_type.lower(),
                        "value": pref_value.strip().lower(),
                        "user_id": memory.metadata.context.get("user_id"),
                        "memory_id": memory.metadata.memory_id
                    })

        # Group by user and find patterns
        user_preferences = defaultdict(list)
        for pref in all_preferences:
            if pref["user_id"]:
                user_preferences[pref["user_id"]].append(pref)

        for user_id, prefs in user_preferences.items():
            if len(prefs) < 3:  # Need minimum preferences for pattern
                continue

            # Analyze preference patterns
            pref_types = Counter(p["type"] for p in prefs)
            pref_values = Counter(p["value"] for p in prefs)

            # Find strong preferences (mentioned multiple times)
            strong_prefs = {value: count for value, count in pref_values.items() if count >= 2}

            if strong_prefs:
                pattern = {
                    "user_id": user_id,
                    "strong_preferences": strong_prefs,
                    "preference_types": dict(pref_types),
                    "total_preferences": len(prefs),
                    "source_memories": list(set(p["memory_id"] for p in prefs))
                }
                patterns.append(pattern)

        return patterns

    async def _store_pattern_from_analysis(self, pattern: Dict[str, Any]):
        """Store a pattern discovered from analysis"""
        pattern_id = pattern["id"]
        self.patterns[pattern_id] = pattern

    async def _store_preference_pattern(self, pattern: Dict[str, Any]):
        """Store a preference pattern"""
        user_id = pattern["user_id"]

        # Store as semantic knowledge
        pattern_key = f"user_{user_id}_preferences"
        self.knowledge_base[pattern_key] = {
            "type": "user_preference_pattern",
            "content": pattern,
            "confidence": 0.8,
            "last_updated": datetime.now().isoformat()
        }

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
        """Load semantic memory from disk"""
        if not self.storage_path.exists():
            return

        entry_files = list(self.storage_path.glob("*.json"))
        print(f"[SEMANTIC MEMORY]: Loading {len(entry_files)} entries...")

        for entry_file in entry_files:
            try:
                with open(entry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruct entry
                metadata = MemoryMetadata(
                    memory_id=data["memory_id"],
                    memory_type=MemoryType.SEMANTIC,
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
                await self._process_structured_knowledge(entry)

            except Exception as e:
                print(f"[SEMANTIC MEMORY]: Error loading {entry_file}: {e}")

        print(f"[SEMANTIC MEMORY]: Loaded {len(self.memory_entries)} semantic entries")

    async def save(self):
        """Save all semantic memory to disk"""
        for memory_id, entry in self.memory_entries.items():
            await self._save_entry(entry)

    async def apply_decay(self, decay_rate: float = 0.0005):
        """Apply slow decay to semantic knowledge (semantic memory is more stable)"""
        # Semantic memory decays much slower than episodic
        for key, knowledge in self.knowledge_base.items():
            if "confidence" in knowledge:
                knowledge["confidence"] = max(0.3, knowledge["confidence"] - decay_rate)

        # User preferences also decay slowly
        for user_id, preferences in self.user_preferences.items():
            for category, pref_list in preferences.items():
                for pref in pref_list:
                    pref["confidence"] = max(0.2, pref["confidence"] - decay_rate)

    async def cleanup_decayed_memories(self, threshold: float = 0.2):
        """Remove semantic knowledge that has decayed below threshold"""
        # Clean knowledge base
        to_remove = []
        for key, knowledge in self.knowledge_base.items():
            if knowledge.get("confidence", 1.0) < threshold:
                to_remove.append(key)

        for key in to_remove:
            del self.knowledge_base[key]

        # Clean user preferences
        for user_id in self.user_preferences:
            for category in list(self.user_preferences[user_id].keys()):
                self.user_preferences[user_id][category] = [
                    pref for pref in self.user_preferences[user_id][category]
                    if pref.get("confidence", 1.0) >= threshold
                ]

                # Remove empty categories
                if not self.user_preferences[user_id][category]:
                    del self.user_preferences[user_id][category]

        if to_remove:
            print(f"[SEMANTIC MEMORY]: Cleaned up {len(to_remove)} decayed knowledge items")

    async def get_stats(self) -> Dict[str, Any]:
        """Get semantic memory statistics"""
        total_knowledge = len(self.knowledge_base)
        total_users = len(self.user_preferences)
        total_patterns = len(self.patterns)

        # Calculate preference stats
        total_preferences = sum(
            len(cat_prefs) for user_prefs in self.user_preferences.values()
            for cat_prefs in user_prefs.values()
        )

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.json"))

        return {
            "total_knowledge_items": total_knowledge,
            "total_users": total_users,
            "total_preferences": total_preferences,
            "total_patterns": total_patterns,
            "avg_preferences_per_user": total_preferences / max(1, total_users),
            "knowledge_categories": {
                "facts": len([k for k in self.knowledge_base.values() if k.get("type") == "fact"]),
                "concepts": len([k for k in self.knowledge_base.values() if k.get("type") == "concept"]),
                "user_patterns": len([k for k in self.knowledge_base.values() if k.get("type") == "user_preference_pattern"])
            },
            "storage_size_mb": total_size / (1024 * 1024)
        }

    async def export(self) -> Dict[str, Any]:
        """Export all semantic memory"""
        return {
            "knowledge_base": self.knowledge_base.copy(),
            "user_preferences": self.user_preferences.copy(),
            "concept_relationships": {k: list(v) for k, v in self.concept_relationships.items()},
            "patterns": self.patterns.copy(),
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
        """Import semantic memory"""
        self.knowledge_base.update(data.get("knowledge_base", {}))
        self.user_preferences.update(data.get("user_preferences", {}))
        self.concept_relationships.update({k: set(v) for k, v in data.get("concept_relationships", {}).items()})
        self.patterns.update(data.get("patterns", {}))

        # Import memory entries
        for memory_id, entry_data in data.get("memory_entries", {}).items():
            metadata = MemoryMetadata(
                memory_id=memory_id,
                memory_type=MemoryType.SEMANTIC,
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

        print(f"[SEMANTIC MEMORY]: Imported {len(self.memory_entries)} semantic entries")