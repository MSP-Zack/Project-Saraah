"""
Common data structures and types for the memory system.
Separated to avoid circular imports.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

class MemoryType(Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"

class MemoryImportance(Enum):
    TRIVIAL = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    CRITICAL = 0.9

@dataclass
class MemoryMetadata:
    """Rich metadata for memory entries"""
    memory_id: str
    memory_type: MemoryType
    timestamp: datetime
    importance: float
    confidence: float
    source: str  # 'conversation', 'observation', 'learning', etc.
    context: Dict[str, Any]  # Conversation context, user state, etc.
    emotional_context: Dict[str, Any]  # Emotional state of user and AI
    relationships: List[str]  # Related memory IDs
    tags: List[str]  # Semantic tags
    decay_rate: float  # How fast this memory decays
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    consolidation_count: int = 0

@dataclass
class MemoryEntry:
    """Complete memory entry with content and metadata"""
    content: Any  # Text, structured data, or binary
    content_type: str  # 'text', 'audio', 'image', 'structured'
    embedding: Optional[np.ndarray] = None
    metadata: MemoryMetadata = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = MemoryMetadata(
                memory_id=str(uuid.uuid4()),
                memory_type=MemoryType.EPISODIC,
                timestamp=datetime.now(),
                importance=0.5,
                confidence=0.8,
                source="unknown",
                context={},
                emotional_context={},
                relationships=[],
                tags=[],
                decay_rate=0.01
            )