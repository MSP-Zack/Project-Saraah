#!/usr/bin/env python3
"""
Test script for the Advanced Memory System
Demonstrates memory storage, retrieval, and consolidation capabilities.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sarah_ai.core.memory_system import AdvancedMemorySystem, MemoryType, MemoryImportance

async def test_memory_system():
    """Test the advanced memory system capabilities"""

    print("🧠 Testing Advanced Memory System")
    print("=" * 50)

    # Initialize memory system
    memory = AdvancedMemorySystem("test_memory")

    try:
        # Initialize
        await memory.initialize()
        print("✅ Memory system initialized")

        # Test 1: Store different types of memories
        print("\n📝 Testing memory storage...")

        # Store working memory (short-term)
        working_id = await memory.store_memory(
            content="User is asking about favorite movies",
            memory_type=MemoryType.WORKING,
            importance=MemoryImportance.HIGH,
            source="conversation",
            tags=["query", "movies"]
        )
        print(f"✅ Stored working memory: {working_id[:8]}...")

        # Store episodic memory (conversation event)
        episodic_id = await memory.store_memory(
            content={
                "user_message": "What's your favorite movie?",
                "ai_response": "I love sci-fi movies like Blade Runner and The Matrix!",
                "context": "casual conversation"
            },
            content_type="structured",
            memory_type=MemoryType.EPISODIC,
            importance=MemoryImportance.MEDIUM,
            source="conversation",
            emotional_context={"user_excited": 0.7, "ai_enthusiastic": 0.8},
            tags=["movies", "conversation", "personal"]
        )
        print(f"✅ Stored episodic memory: {episodic_id[:8]}...")

        # Store semantic memory (learned fact)
        semantic_id = await memory.store_memory(
            content={
                "fact": {
                    "content": "User enjoys sci-fi movies",
                    "category": "entertainment",
                    "confidence": 0.9
                }
            },
            content_type="structured",
            memory_type=MemoryType.SEMANTIC,
            importance=MemoryImportance.HIGH,
            source="learning",
            tags=["preference", "movies", "sci-fi"]
        )
        print(f"✅ Stored semantic memory: {semantic_id[:8]}...")

        # Store procedural memory (learned behavior)
        procedural_id = await memory.store_memory(
            content={
                "skill": {
                    "name": "movie_recommendation",
                    "description": "Recommend movies based on user preferences",
                    "category": "recommendation",
                    "proficiency": 0.8
                }
            },
            content_type="structured",
            memory_type=MemoryType.PROCEDURAL,
            importance=MemoryImportance.MEDIUM,
            source="learning",
            tags=["skill", "recommendation"]
        )
        print(f"✅ Stored procedural memory: {procedural_id[:8]}...")

        # Store emotional memory
        emotional_id = await memory.store_memory(
            content={
                "emotional_state": {
                    "user_joy": 0.8,
                    "ai_joy": 0.9,
                    "context": "sharing interests"
                },
                "relationship_impact": 0.1
            },
            content_type="structured",
            memory_type=MemoryType.EMOTIONAL,
            importance=MemoryImportance.MEDIUM,
            source="interaction",
            emotional_context={"joy": 0.85, "connection": 0.7},
            tags=["emotion", "positive"]
        )
        print(f"✅ Stored emotional memory: {emotional_id[:8]}...")

        # Test 2: Memory retrieval
        print("\n🔍 Testing memory retrieval...")

        # Retrieve memories about movies
        movie_memories = await memory.retrieve_memories(
            query="movies sci-fi",  # Mock query
            memory_types=[MemoryType.EPISODIC, MemoryType.SEMANTIC],
            limit=5
        )
        print(f"✅ Retrieved {len(movie_memories)} movie-related memories")

        # Test conversation context recall
        print("\n💬 Testing conversation context recall...")

        current_context = {
            "topics": ["movies", "recommendations"],
            "user_emotion": "curious",
            "ai_emotion": "helpful"
        }

        conversation_history = [
            {"content": "What movies do you like?", "role": "user"},
            {"content": "I enjoy sci-fi movies!", "role": "ai"}
        ]

        context_recall = await memory.recall_conversation_context(
            current_context=current_context,
            conversation_history=conversation_history,
            user_id="test_user"
        )
        print(f"✅ Recalled conversation context with {len(context_recall.get('relevant_memories', []))} relevant memories")

        # Test 3: Memory consolidation
        print("\n🔄 Testing memory consolidation...")

        # Force consolidation (normally runs on schedule)
        await memory.consolidate_memories()
        print("✅ Memory consolidation completed")

        # Test 4: Get statistics
        print("\n📊 Getting memory statistics...")

        stats = await memory.get_memory_stats()
        print("✅ Memory system statistics:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}: {len(value)} items" if hasattr(value, '__len__') else f"  {key}: {value}")
            else:
                print(f"  {key}: {value}")

        print("\n🎉 All memory system tests completed successfully!")
        print("The advanced memory system is ready to surpass Neuro-sama's capabilities!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        await memory.shutdown()
        print("\n🧹 Memory system shutdown complete")

if __name__ == "__main__":
    asyncio.run(test_memory_system())