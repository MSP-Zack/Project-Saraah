"""
Working Memory System
Implements short-term memory with limited capacity (like human working memory).
Features:
- Limited capacity (7±2 items)
- Fast access and retrieval
- Automatic decay and replacement
- Context-aware storage
"""

import time
from typing import List, Dict, Any, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime
import threading

from .types import MemoryEntry, MemoryMetadata, MemoryType, MemoryImportance

@dataclass
class WorkingMemoryItem:
    """Item in working memory with activation level"""
    entry: MemoryEntry
    activation: float  # 0.0 to 1.0
    last_accessed: float  # timestamp
    access_count: int = 0

class WorkingMemory:
    """
    Short-term working memory with limited capacity.
    Implements the "magical number seven" principle from cognitive psychology.
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.memories: List[WorkingMemoryItem] = []
        self.activation_decay_rate = 0.1  # How fast activation decays
        self.min_activation_threshold = 0.1  # Items below this get removed
        self.lock = threading.Lock()

        # Start background decay process
        self.decay_thread = threading.Thread(target=self._decay_loop, daemon=True)
        self.decay_thread.start()

    def store(self, entry: MemoryEntry, initial_activation: float = 0.8):
        """Store an item in working memory"""
        with self.lock:
            # Check if item already exists
            existing_index = None
            for i, item in enumerate(self.memories):
                if item.entry.metadata.memory_id == entry.metadata.memory_id:
                    existing_index = i
                    break

            if existing_index is not None:
                # Update existing item
                self.memories[existing_index].activation = min(1.0, self.memories[existing_index].activation + 0.2)
                self.memories[existing_index].last_accessed = time.time()
                self.memories[existing_index].access_count += 1
            else:
                # Add new item
                item = WorkingMemoryItem(
                    entry=entry,
                    activation=initial_activation,
                    last_accessed=time.time()
                )

                # If at capacity, remove lowest activation item
                if len(self.memories) >= self.capacity:
                    self._remove_lowest_activation()

                self.memories.append(item)

            # Sort by activation (highest first)
            self.memories.sort(key=lambda x: x.activation, reverse=True)

    def retrieve(self, query: str = None, limit: int = None) -> List[MemoryEntry]:
        """Retrieve items from working memory"""
        with self.lock:
            # Update access times and activations
            current_time = time.time()
            for item in self.memories:
                if query and self._matches_query(item.entry, query):
                    item.activation = min(1.0, item.activation + 0.1)
                    item.last_accessed = current_time
                    item.access_count += 1

            # Sort by activation and return
            sorted_memories = sorted(self.memories, key=lambda x: x.activation, reverse=True)
            result = [item.entry for item in sorted_memories]

            return result[:limit] if limit else result

    def get_context(self) -> Dict[str, Any]:
        """Get current working memory context for LLM"""
        with self.lock:
            context = {
                "recent_memories": [],
                "active_topics": set(),
                "emotional_state": {},
                "conversation_flow": []
            }

            # Get top activated memories
            sorted_items = sorted(self.memories, key=lambda x: x.activation, reverse=True)

            for item in sorted_items[:5]:  # Top 5 most active
                memory_summary = {
                    "content_preview": self._get_content_preview(item.entry),
                    "activation": item.activation,
                    "tags": item.entry.metadata.tags,
                    "timestamp": datetime.fromtimestamp(item.last_accessed).isoformat()
                }
                context["recent_memories"].append(memory_summary)

                # Extract topics
                if item.entry.metadata.tags:
                    context["active_topics"].update(item.entry.metadata.tags)

                # Extract emotional context
                if item.entry.metadata.emotional_context:
                    context["emotional_state"].update(item.entry.metadata.emotional_context)

            context["active_topics"] = list(context["active_topics"])
            return context

    def _matches_query(self, entry: MemoryEntry, query: str) -> bool:
        """Check if memory entry matches query"""
        query_lower = query.lower()

        # Check content
        if isinstance(entry.content, str):
            if query_lower in entry.content.lower():
                return True

        # Check tags
        if entry.metadata.tags:
            for tag in entry.metadata.tags:
                if query_lower in tag.lower():
                    return True

        # Check context
        for key, value in entry.metadata.context.items():
            if isinstance(value, str) and query_lower in value.lower():
                return True

        return False

    def _get_content_preview(self, entry: MemoryEntry, max_length: int = 100) -> str:
        """Get a preview of memory content"""
        if isinstance(entry.content, str):
            return entry.content[:max_length] + "..." if len(entry.content) > max_length else entry.content
        elif isinstance(entry.content, dict):
            return f"Structured data: {list(entry.content.keys())[:3]}..."
        else:
            return f"Binary content ({entry.content_type})"

    def _remove_lowest_activation(self):
        """Remove the item with lowest activation"""
        if not self.memories:
            return

        lowest_index = min(range(len(self.memories)), key=lambda i: self.memories[i].activation)
        removed_item = self.memories.pop(lowest_index)

        # Could optionally move to episodic memory here
        print(f"[WORKING MEMORY]: Removed low-activation item: {removed_item.entry.metadata.memory_id[:8]}")

    def _decay_loop(self):
        """Background process to decay activation levels"""
        while True:
            time.sleep(30)  # Decay every 30 seconds

            with self.lock:
                current_time = time.time()

                # Decay activations
                to_remove = []
                for i, item in enumerate(self.memories):
                    time_since_access = current_time - item.last_accessed
                    decay_amount = self.activation_decay_rate * (time_since_access / 60.0)  # Scale by minutes

                    item.activation = max(0.0, item.activation - decay_amount)

                    # Mark for removal if below threshold
                    if item.activation < self.min_activation_threshold:
                        to_remove.append(i)

                # Remove decayed items (in reverse order to maintain indices)
                for i in reversed(to_remove):
                    removed_item = self.memories.pop(i)
                    print(f"[WORKING MEMORY]: Decayed item removed: {removed_item.entry.metadata.memory_id[:8]}")

    def clear(self):
        """Clear all working memory"""
        with self.lock:
            self.memories.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get working memory statistics"""
        with self.lock:
            if not self.memories:
                return {
                    "capacity": self.capacity,
                    "current_items": 0,
                    "utilization": 0.0,
                    "avg_activation": 0.0,
                    "total_accesses": 0
                }

            activations = [item.activation for item in self.memories]
            total_accesses = sum(item.access_count for item in self.memories)

            return {
                "capacity": self.capacity,
                "current_items": len(self.memories),
                "utilization": len(self.memories) / self.capacity,
                "avg_activation": sum(activations) / len(activations),
                "total_accesses": total_accesses,
                "highest_activation": max(activations),
                "lowest_activation": min(activations)
            }