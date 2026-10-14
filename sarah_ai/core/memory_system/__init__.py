"""
Advanced Memory System for Sarah AI Companion
Surpasses Neuro-sama's memory capabilities with multi-layered, multi-modal memory architecture.

Features:
- Hierarchical memory (Working → Episodic → Semantic → Procedural)
- Vector-based semantic search
- Graph-based relationship modeling
- Emotional memory tracking
- Multi-modal storage (text, audio, visual)
- Real-time consolidation and decay
- Advanced retrieval with context awareness
"""

import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from pathlib import Path

# Memory types and data structures
from .types import MemoryType, MemoryImportance, MemoryMetadata, MemoryEntry

# Memory subsystems
from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory
from .semantic_memory import SemanticMemory
from .procedural_memory import ProceduralMemory
from .emotional_memory import EmotionalMemory
from .retrieval_engine import MemoryRetrievalEngine
from .consolidation_engine import MemoryConsolidationEngine
from .decay_engine import MemoryDecayEngine
from .vector_store import VectorStore
from .graph_store import GraphStore

class AdvancedMemorySystem:
    """
    Master memory system orchestrator that manages all memory types and operations.
    This system surpasses Neuro-sama by providing:
    - Multi-layered memory architecture
    - Real-time emotional tracking
    - Semantic and episodic memory with vector search
    - Graph-based relationship modeling
    - Adaptive memory consolidation and decay
    - Multi-modal memory storage
    """

    def __init__(self, base_path: str = "memory"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # Initialize memory subsystems
        self.working_memory = WorkingMemory(capacity=50)  # 7±2 items like human memory
        self.episodic_memory = EpisodicMemory(self.base_path / "episodic")
        self.semantic_memory = SemanticMemory(self.base_path / "semantic")
        self.procedural_memory = ProceduralMemory(self.base_path / "procedural")
        self.emotional_memory = EmotionalMemory(self.base_path / "emotional")

        # Initialize storage engines
        self.vector_store = VectorStore(self.base_path / "vectors")
        self.graph_store = GraphStore(self.base_path / "graph")

        # Initialize processing engines
        self.retrieval_engine = MemoryRetrievalEngine(self.base_path / "retrieval")
        self.consolidation_engine = MemoryConsolidationEngine(self.base_path / "consolidation")
        self.decay_engine = MemoryDecayEngine(self.base_path / "decay")

        # System state
        self.is_initialized = False
        self.last_consolidation = datetime.now()
        self.consolidation_interval = timedelta(hours=1)  # Consolidate every hour

        print("[MEMORY]: Advanced memory system initialized with Neuro-sama surpassing capabilities.")

    async def initialize(self):
        """Initialize all memory subsystems"""
        if self.is_initialized:
            return

        # Load existing memories
        await self.episodic_memory.load()
        await self.semantic_memory.load()
        await self.procedural_memory.load()
        await self.emotional_memory.load()

        # Initialize vector and graph stores
        await self.vector_store.load()
        await self.graph_store.load()

        # Initialize processing engines
        await self.retrieval_engine.load_index()
        await self.consolidation_engine.load()
        await self.decay_engine.load()

        self.is_initialized = True
        print("[MEMORY]: All memory subsystems loaded and ready.")

    async def store_memory(self, content: Union[str, Dict[str, Any], bytes],
                          content_type: str = "text",
                          memory_type: MemoryType = MemoryType.EPISODIC,
                          importance: MemoryImportance = MemoryImportance.MEDIUM,
                          source: str = "conversation",
                          context: Dict[str, Any] = None,
                          emotional_context: Dict[str, Any] = None,
                          tags: List[str] = None) -> str:
        """
        Store a new memory with rich metadata and automatic processing.
        Returns the memory ID.
        """

        # Create memory entry
        entry = MemoryEntry(
            content=content,
            content_type=content_type
        )

        # Set metadata
        entry.metadata.memory_type = memory_type
        entry.metadata.importance = importance.value
        entry.metadata.source = source
        entry.metadata.context = context or {}
        entry.metadata.emotional_context = emotional_context or {}
        entry.metadata.tags = tags or []

        # Set decay rate based on importance (important memories decay slower)
        entry.metadata.decay_rate = 0.05 / (importance.value + 0.1)  # Higher importance = slower decay

        # Generate embedding for semantic search
        if content_type == "text" and isinstance(content, str):
            # For now, create a simple embedding (would use actual embedding model)
            entry.embedding = np.random.rand(384).astype(np.float32)  # Mock embedding

        # Store in appropriate memory system
        memory_id = entry.metadata.memory_id

        if memory_type == MemoryType.WORKING:
            self.working_memory.store(entry)
        elif memory_type == MemoryType.EPISODIC:
            await self.episodic_memory.store(entry)
        elif memory_type == MemoryType.SEMANTIC:
            await self.semantic_memory.store(entry)
        elif memory_type == MemoryType.PROCEDURAL:
            await self.procedural_memory.store(entry)
        elif memory_type == MemoryType.EMOTIONAL:
            await self.emotional_memory.store(entry)

        # Store in vector database for search
        if entry.embedding is not None:
            metadata_dict = {
                "memory_type": memory_type.value,
                "importance": importance.value,
                "source": source,
                "tags": tags or [],
                "timestamp": entry.metadata.timestamp.isoformat()
            }
            await self.vector_store.store(memory_id, entry.embedding, metadata_dict)

        # Store relationships in graph database
        node_data = {
            "memory_type": memory_type.value,
            "importance": importance.value,
            "source": source,
            "tags": tags or [],
            "timestamp": entry.metadata.timestamp.isoformat()
        }
        await self.graph_store.add_node(memory_id, node_data)

        # Update emotional memory if emotional context provided
        if emotional_context:
            await self.emotional_memory.update_emotional_state(emotional_context)

        print(f"[MEMORY]: Stored {memory_type.value} memory: {memory_id[:8]}...")
        return memory_id

    async def retrieve_memories(self, query: str,
                               memory_types: List[MemoryType] = None,
                               limit: int = 10,
                               context: Dict[str, Any] = None,
                               emotional_filter: Dict[str, Any] = None,
                               time_filter: Dict[str, Any] = None) -> List[Tuple[MemoryEntry, float]]:
        """
        Advanced memory retrieval with semantic search, context awareness, and filtering.
        Returns list of (memory_entry, relevance_score) tuples.
        """

        # Use advanced retrieval engine
        filters = {}
        if memory_types:
            filters["memory_type"] = [mt.value for mt in memory_types]
        if emotional_filter:
            filters["emotions"] = emotional_filter
        if time_filter:
            filters["date_range"] = (time_filter.get("start"), time_filter.get("end"))

        # Create mock query vector (would use actual embedding)
        query_vector = np.random.rand(384).astype(np.float32)

        results = await self.retrieval_engine.search(query, limit=limit, filters=filters)
        return [(self._get_memory_by_id(memory_id), score) for memory_id, score in results]

    def _get_memory_by_id(self, memory_id: str) -> Optional[MemoryEntry]:
        """Get memory entry by ID from any memory store"""
        # Check all memory stores
        stores = [
            self.working_memory,
            self.episodic_memory,
            self.semantic_memory,
            self.procedural_memory,
            self.emotional_memory
        ]

        for store in stores:
            if hasattr(store, 'memory_entries') and memory_id in store.memory_entries:
                return store.memory_entries[memory_id]

        return None

    async def recall_conversation_context(self, current_context: Dict[str, Any],
                                        conversation_history: List[Dict[str, Any]],
                                        user_id: str = None) -> Dict[str, Any]:
        """
        Recall relevant memories for current conversation context.
        This is what makes Sarah remember everything about users.
        """

        # Extract key elements from current context
        current_topics = current_context.get("topics", [])
        user_emotion = current_context.get("user_emotion", "neutral")
        ai_emotion = current_context.get("ai_emotion", "neutral")

        # Build comprehensive query
        query_parts = []

        # Add current topics
        if current_topics:
            query_parts.extend(current_topics)

        # Add recent conversation summary
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            recent_text = " ".join([msg.get("content", "") for msg in recent_messages])
            query_parts.append(f"Recent conversation: {recent_text[:200]}...")

        # Add emotional context
        query_parts.append(f"User feeling {user_emotion}, AI feeling {ai_emotion}")

        query = " ".join(query_parts)

        # Retrieve relevant memories
        relevant_memories = await self.retrieve_memories(
            query=query,
            memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.EMOTIONAL],
            limit=20,
            context={"user_id": user_id, "conversation_id": current_context.get("conversation_id")},
            emotional_filter={"user_emotion": user_emotion}
        )

        # Build context response
        context_response = {
            "relevant_memories": [entry.metadata.memory_id for entry, score in relevant_memories],
            "user_preferences": await self._extract_user_preferences(relevant_memories),
            "relationship_context": await self._extract_relationship_context(user_id, relevant_memories),
            "emotional_history": await self._extract_emotional_history(user_id, relevant_memories),
            "conversation_patterns": await self._extract_conversation_patterns(user_id, relevant_memories),
            "inside_jokes": await self._extract_inside_jokes(relevant_memories),
            "personal_details": await self._extract_personal_details(user_id, relevant_memories)
        }

        return context_response

    async def _extract_user_preferences(self, memories: List[Tuple[MemoryEntry, float]]) -> Dict[str, Any]:
        """Extract user preferences from memory patterns"""
        preferences = {}

        for entry, score in memories:
            if entry.metadata.memory_type == MemoryType.SEMANTIC:
                content = entry.content
                if isinstance(content, dict) and "preference" in content:
                    pref = content["preference"]
                    if pref["category"] not in preferences:
                        preferences[pref["category"]] = []
                    preferences[pref["category"]].append({
                        "value": pref["value"],
                        "confidence": pref.get("confidence", score),
                        "last_updated": entry.metadata.timestamp.isoformat()
                    })

        return preferences

    async def _extract_relationship_context(self, user_id: str, memories: List[Tuple[MemoryEntry, float]]) -> Dict[str, Any]:
        """Extract relationship dynamics and history"""
        relationship_data = {
            "trust_level": 0.5,
            "emotional_attachment": 0.5,
            "interaction_count": 0,
            "shared_experiences": [],
            "conflict_history": [],
            "support_moments": []
        }

        for entry, score in memories:
            if entry.metadata.source == "conversation" and user_id in str(entry.content):
                relationship_data["interaction_count"] += 1

                # Analyze emotional context
                emotional = entry.metadata.emotional_context
                if emotional.get("relationship_impact"):
                    impact = emotional["relationship_impact"]
                    if impact > 0:
                        relationship_data["trust_level"] = min(1.0, relationship_data["trust_level"] + impact * 0.1)
                        relationship_data["emotional_attachment"] = min(1.0, relationship_data["emotional_attachment"] + impact * 0.05)
                    elif impact < 0:
                        relationship_data["trust_level"] = max(0.0, relationship_data["trust_level"] + impact * 0.1)

        return relationship_data

    async def _extract_emotional_history(self, user_id: str, memories: List[Tuple[MemoryEntry, float]]) -> List[Dict[str, Any]]:
        """Extract emotional interaction history"""
        emotional_history = []

        for entry, score in memories:
            if entry.metadata.emotional_context:
                emotional_history.append({
                    "timestamp": entry.metadata.timestamp.isoformat(),
                    "user_emotion": entry.metadata.emotional_context.get("user_emotion"),
                    "ai_emotion": entry.metadata.emotional_context.get("ai_emotion"),
                    "context": entry.metadata.context,
                    "memory_id": entry.metadata.memory_id
                })

        return sorted(emotional_history, key=lambda x: x["timestamp"], reverse=True)[:10]

    async def _extract_conversation_patterns(self, user_id: str, memories: List[Tuple[MemoryEntry, float]]) -> Dict[str, Any]:
        """Extract conversation patterns and preferences"""
        patterns = {
            "favorite_topics": [],
            "communication_style": "casual",
            "response_preferences": {},
            "humor_style": "neutral"
        }

        # Analyze conversation content for patterns
        topic_counts = {}
        for entry, score in memories:
            if isinstance(entry.content, str):
                # Simple topic extraction (could be enhanced with NLP)
                words = entry.content.lower().split()
                for word in words:
                    if len(word) > 4:  # Focus on meaningful words
                        topic_counts[word] = topic_counts.get(word, 0) + 1

        # Get top topics
        patterns["favorite_topics"] = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return patterns

    async def _extract_inside_jokes(self, memories: List[Tuple[MemoryEntry, float]]) -> List[Dict[str, Any]]:
        """Extract inside jokes and recurring humorous elements"""
        jokes = []

        for entry, score in memories:
            if entry.metadata.tags and "humor" in entry.metadata.tags:
                if isinstance(entry.content, str):
                    jokes.append({
                        "content": entry.content,
                        "context": entry.metadata.context,
                        "timestamp": entry.metadata.timestamp.isoformat(),
                        "relevance_score": score
                    })

        return jokes[:5]  # Return top 5 jokes

    async def _extract_personal_details(self, user_id: str, memories: List[Tuple[MemoryEntry, float]]) -> Dict[str, Any]:
        """Extract personal details about the user"""
        personal_info = {
            "name": None,
            "age": None,
            "interests": [],
            "occupation": None,
            "location": None,
            "personality_traits": [],
            "preferences": {}
        }

        for entry, score in memories:
            if entry.metadata.memory_type == MemoryType.SEMANTIC:
                content = entry.content
                if isinstance(content, dict):
                    if "personal_detail" in content:
                        detail = content["personal_detail"]
                        category = detail.get("category")
                        value = detail.get("value")

                        if category == "name":
                            personal_info["name"] = value
                        elif category == "age":
                            personal_info["age"] = value
                        elif category == "interest":
                            if value not in personal_info["interests"]:
                                personal_info["interests"].append(value)
                        elif category == "occupation":
                            personal_info["occupation"] = value
                        elif category == "location":
                            personal_info["location"] = value

        return personal_info

    async def consolidate_memories(self):
        """Run memory consolidation process"""
        if datetime.now() - self.last_consolidation < self.consolidation_interval:
            return

        print("[MEMORY]: Running memory consolidation...")

        # Run full consolidation process
        consolidation_actions = await self.consolidation_engine.consolidate_memories(self)

        # Apply decay
        await self.decay_engine.apply_decay(self)

        # Clean up decayed memories
        await self.decay_engine.cleanup_decayed_memories(self)

        self.last_consolidation = datetime.now()
        print(f"[MEMORY]: Memory consolidation complete. {len(consolidation_actions)} actions performed.")

    async def _cleanup_memories(self):
        """Clean up memories that have decayed below threshold"""
        # This is now handled by the decay engine
        pass

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory system statistics"""
        return {
            "working_memory": {
                "capacity": self.working_memory.capacity,
                "current_items": len(self.working_memory.memories),
                "utilization": len(self.working_memory.memories) / self.working_memory.capacity
            },
            "episodic_memory": await self.episodic_memory.get_stats(),
            "semantic_memory": await self.semantic_memory.get_stats(),
            "procedural_memory": await self.procedural_memory.get_stats(),
            "emotional_memory": await self.emotional_memory.get_stats(),
            "vector_store": await self.vector_store.get_stats(),
            "graph_store": await self.graph_store.get_stats(),
            "last_consolidation": self.last_consolidation.isoformat(),
            "system_health": "excellent" if self.is_initialized else "initializing"
        }

    async def export_memories(self, export_path: str):
        """Export all memories for backup or analysis"""
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "system_stats": await self.get_memory_stats(),
            "episodic_memories": await self.episodic_memory.export(),
            "semantic_memories": await self.semantic_memory.export(),
            "procedural_memories": await self.procedural_memory.export(),
            "emotional_memories": await self.emotional_memory.export()
        }

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, default=str)

        print(f"[MEMORY]: Memories exported to {export_path}")

    async def import_memories(self, import_path: str):
        """Import memories from backup"""
        with open(import_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        # Import each memory type
        if "episodic_memories" in import_data:
            await self.episodic_memory.import_data(import_data["episodic_memories"])
        if "semantic_memories" in import_data:
            await self.semantic_memory.import_data(import_data["semantic_memories"])
        if "procedural_memories" in import_data:
            await self.procedural_memory.import_data(import_data["procedural_memories"])
        if "emotional_memories" in import_data:
            await self.emotional_memory.import_data(import_data["emotional_memories"])

        print(f"[MEMORY]: Memories imported from {import_path}")

    async def shutdown(self):
        """Gracefully shutdown the memory system"""
        print("[MEMORY]: Shutting down memory system...")

        # Save all memories
        await self.episodic_memory.save()
        await self.semantic_memory.save()
        await self.procedural_memory.save()
        await self.emotional_memory.save()

        # Save storage engines
        await self.vector_store.save()
        await self.graph_store.save()

        # Save processing engines
        await self.consolidation_engine.save()
        await self.decay_engine.save()

        print("[MEMORY]: Memory system shutdown complete.")