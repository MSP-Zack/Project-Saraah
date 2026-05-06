"""
Memory Decay Engine
Handles memory decay, forgetting, and memory lifecycle management.
Features:
- Time-based decay
- Access-based decay reduction
- Importance-based decay protection
- Memory pruning and cleanup
- Decay visualization and monitoring
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import math
import random

from .types import MemoryEntry, MemoryMetadata, MemoryType

class MemoryDecayEngine:
    """
    Engine responsible for managing memory decay and forgetting processes.
    Implements various decay models and cleanup strategies.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Decay configuration
        self.decay_models = {
            "working_memory": {
                "model": "exponential",
                "half_life_hours": 0.5,  # Very fast decay
                "min_importance": 0.1,
                "access_protection_factor": 0.8
            },
            "episodic_memory": {
                "model": "power_law",
                "decay_rate": 0.02,  # Slower decay
                "min_importance": 0.2,
                "access_protection_factor": 0.9
            },
            "semantic_memory": {
                "model": "logarithmic",
                "decay_rate": 0.005,  # Very slow decay
                "min_importance": 0.3,
                "access_protection_factor": 0.95
            },
            "procedural_memory": {
                "model": "negative_decay",  # Actually improves
                "improvement_rate": 0.001,
                "max_proficiency": 1.0,
                "min_proficiency": 0.1
            }
        }

        # Decay tracking
        self.decay_history: List[Dict[str, Any]] = []
        self.memory_lifetimes: Dict[str, List[datetime]] = defaultdict(list)
        self.decay_rates: Dict[str, float] = {}

        # Cleanup thresholds
        self.cleanup_thresholds = {
            "working_memory": 0.1,
            "episodic_memory": 0.15,
            "semantic_memory": 0.25,
            "procedural_memory": 0.05  # Very low threshold for skills
        }

        print(f"[DECAY ENGINE]: Initialized at {storage_path}")

    async def apply_decay(self, memory_system) -> List[Dict[str, Any]]:
        """
        Apply decay to all memories in the system.
        Returns a list of decay actions taken.
        """
        decay_actions = []

        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            type_name = memory_type.value
            memory_store = self._get_memory_store(memory_system, type_name)

            if not memory_store:
                continue

            type_actions = await self._apply_decay_to_type(memory_store, type_name)
            decay_actions.extend(type_actions)

        # Record decay run
        self.decay_history.append({
            "timestamp": datetime.now().isoformat(),
            "total_actions": len(decay_actions),
            "actions": decay_actions[:10]  # Keep only first 10 for history
        })

        # Keep only recent history
        if len(self.decay_history) > 50:
            self.decay_history = self.decay_history[-50:]

        print(f"[DECAY ENGINE]: Applied decay with {len(decay_actions)} actions")
        return decay_actions

    async def _apply_decay_to_type(self, memory_store, memory_type: str) -> List[Dict[str, Any]]:
        """Apply decay to a specific memory type"""
        actions = []
        decay_config = self.decay_models[memory_type]

        for memory_id, entry in memory_store.memory_entries.items():
            old_importance = entry.metadata.importance
            new_importance = await self._calculate_decayed_importance(entry, decay_config, memory_type)

            if abs(new_importance - old_importance) > 0.001:  # Only record significant changes
                entry.metadata.importance = new_importance

                actions.append({
                    "type": "importance_decay",
                    "memory_id": memory_id,
                    "memory_type": memory_type,
                    "old_importance": old_importance,
                    "new_importance": new_importance,
                    "decay_model": decay_config["model"],
                    "age_hours": (datetime.now() - entry.metadata.timestamp).total_seconds() / 3600
                })

                # Track decay rate
                if old_importance > 0:
                    decay_rate = (old_importance - new_importance) / old_importance
                    self.decay_rates[memory_id] = decay_rate

        return actions

    async def _calculate_decayed_importance(self, entry: MemoryEntry,
                                          decay_config: Dict[str, Any],
                                          memory_type: str) -> float:
        """Calculate the decayed importance for a memory"""
        age_hours = (datetime.now() - entry.metadata.timestamp).total_seconds() / 3600
        current_importance = entry.metadata.importance

        # Get access protection factor
        access_protection = decay_config["access_protection_factor"]

        # Apply access-based protection (recent access reduces decay)
        memory_access_times = getattr(entry, '_access_times', [])
        recent_accesses = [t for t in memory_access_times if (datetime.now() - t).hours <= 24]

        if recent_accesses:
            # Reduce decay based on recent access
            access_factor = min(1.0, len(recent_accesses) * 0.1)
            access_protection = min(1.0, access_protection + access_factor)

        # Apply decay based on model
        model = decay_config["model"]

        if model == "exponential":
            half_life = decay_config["half_life_hours"]
            decay_factor = math.exp(-age_hours * math.log(2) / half_life)
        elif model == "power_law":
            decay_rate = decay_config["decay_rate"]
            decay_factor = 1.0 / (1.0 + decay_rate * age_hours)
        elif model == "logarithmic":
            decay_rate = decay_config["decay_rate"]
            decay_factor = max(0.1, 1.0 - decay_rate * math.log(1 + age_hours))
        elif model == "negative_decay":
            # Procedural memory improves with age/use
            improvement_rate = decay_config["improvement_rate"]
            usage_count = getattr(entry, '_usage_count', 0)
            decay_factor = min(decay_config["max_proficiency"],
                              current_importance + improvement_rate * usage_count)
            return decay_factor
        else:
            decay_factor = 1.0  # No decay

        # Apply access protection
        decay_factor = decay_factor * access_protection + (1 - access_protection)

        # Calculate new importance
        new_importance = current_importance * decay_factor

        # Apply minimum importance threshold
        min_importance = decay_config["min_importance"]
        new_importance = max(min_importance, new_importance)

        return new_importance

    async def cleanup_decayed_memories(self, memory_system) -> List[Dict[str, Any]]:
        """
        Clean up memories that have decayed below cleanup thresholds.
        Returns a list of cleanup actions.
        """
        cleanup_actions = []

        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            type_name = memory_type.value
            memory_store = self._get_memory_store(memory_system, type_name)

            if not memory_store:
                continue

            threshold = self.cleanup_thresholds[type_name]
            type_actions = await self._cleanup_type_memories(memory_store, type_name, threshold)
            cleanup_actions.extend(type_actions)

        print(f"[DECAY ENGINE]: Cleaned up {len(cleanup_actions)} decayed memories")
        return cleanup_actions

    async def _cleanup_type_memories(self, memory_store, memory_type: str, threshold: float) -> List[Dict[str, Any]]:
        """Clean up decayed memories of a specific type"""
        actions = []
        to_remove = []

        for memory_id, entry in memory_store.memory_entries.items():
            if entry.metadata.importance < threshold:
                # Additional checks for cleanup
                age_days = (datetime.now() - entry.metadata.timestamp).days

                # Don't cleanup very recent memories
                if age_days < 1:
                    continue

                # Don't cleanup frequently accessed memories
                memory_access_times = getattr(entry, '_access_times', [])
                recent_accesses = [t for t in memory_access_times if (datetime.now() - t).days <= 7]

                if len(recent_accesses) > 2:
                    continue

                # Don't cleanup important relationships
                if len(entry.metadata.relationships) > 5:
                    continue

                to_remove.append(memory_id)

                # Record lifetime
                self.memory_lifetimes[memory_type].append(entry.metadata.timestamp)

        # Remove the memories
        for memory_id in to_remove:
            entry = memory_store.memory_entries[memory_id]
            del memory_store.memory_entries[memory_id]

            actions.append({
                "type": "memory_cleanup",
                "memory_id": memory_id,
                "memory_type": memory_type,
                "final_importance": entry.metadata.importance,
                "age_days": (datetime.now() - entry.metadata.timestamp).days,
                "reason": "importance_below_threshold"
            })

        return actions

    async def simulate_memory_lifespan(self, memory_type: str, initial_importance: float = 0.8) -> Dict[str, Any]:
        """Simulate how long a memory of given type would last"""
        config = self.decay_models[memory_type]
        importance = initial_importance
        hours = 0
        threshold = self.cleanup_thresholds[memory_type]

        while importance > threshold and hours < 8760:  # Max 1 year
            importance = await self._calculate_decayed_importance(
                MemoryEntry(
                    content="simulation",
                    content_type="text",
                    metadata=MemoryMetadata(
                        memory_id="simulation",
                        memory_type=MemoryType(memory_type),
                        timestamp=datetime.now() - timedelta(hours=hours),
                        importance=importance,
                        confidence=0.8,
                        source="simulation",
                        context="",
                        emotional_context={},
                        relationships=[],
                        tags=[]
                    )
                ),
                config,
                memory_type
            )
            hours += 1

        return {
            "memory_type": memory_type,
            "initial_importance": initial_importance,
            "final_importance": importance,
            "lifespan_hours": hours,
            "lifespan_days": hours / 24,
            "cleanup_threshold": threshold
        }

    async def get_decay_statistics(self) -> Dict[str, Any]:
        """Get comprehensive decay statistics"""
        stats = {}

        # Overall decay stats
        total_decays = sum(len(h["actions"]) for h in self.decay_history)
        recent_decays = sum(len(h["actions"]) for h in self.decay_history[-7:])  # Last 7 runs

        # Memory lifetimes
        for memory_type, lifetimes in self.memory_lifetimes.items():
            if lifetimes:
                ages = [(datetime.now() - t).days for t in lifetimes]
                stats[f"{memory_type}_avg_lifetime_days"] = sum(ages) / len(ages)
                stats[f"{memory_type}_max_lifetime_days"] = max(ages)
                stats[f"{memory_type}_min_lifetime_days"] = min(ages)

        # Decay rates
        if self.decay_rates:
            avg_decay_rate = sum(self.decay_rates.values()) / len(self.decay_rates)
            max_decay_rate = max(self.decay_rates.values())
            min_decay_rate = min(self.decay_rates.values())
        else:
            avg_decay_rate = max_decay_rate = min_decay_rate = 0.0

        stats.update({
            "total_decay_runs": len(self.decay_history),
            "total_decay_actions": total_decays,
            "recent_decay_actions": recent_decays,
            "avg_decay_rate": avg_decay_rate,
            "max_decay_rate": max_decay_rate,
            "min_decay_rate": min_decay_rate,
            "decay_models": self.decay_models.copy(),
            "cleanup_thresholds": self.cleanup_thresholds.copy()
        })

        return stats

    async def adjust_decay_parameters(self, memory_type: str, adjustments: Dict[str, Any]):
        """Adjust decay parameters for a memory type"""
        if memory_type in self.decay_models:
            self.decay_models[memory_type].update(adjustments)
            print(f"[DECAY ENGINE]: Updated decay parameters for {memory_type}: {adjustments}")

    async def reset_decay_tracking(self):
        """Reset all decay tracking data"""
        self.decay_history.clear()
        self.memory_lifetimes.clear()
        self.decay_rates.clear()
        print(f"[DECAY ENGINE]: Reset decay tracking data")

    async def get_memory_health_report(self, memory_system) -> Dict[str, Any]:
        """Generate a comprehensive memory health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "memory_types": {}
        }

        for memory_type in [MemoryType.WORKING, MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PROCEDURAL]:
            type_name = memory_type.value
            memory_store = self._get_memory_store(memory_system, type_name)

            if not memory_store:
                continue

            memories = list(memory_store.memory_entries.values())

            if not memories:
                continue

            # Calculate health metrics
            importances = [m.metadata.importance for m in memories]
            ages = [(datetime.now() - m.metadata.timestamp).days for m in memories]

            avg_importance = sum(importances) / len(importances)
            min_importance = min(importances)
            max_importance = max(importances)

            avg_age = sum(ages) / len(ages)
            oldest_age = max(ages)
            newest_age = min(ages)

            # Health score (0-100)
            health_score = self._calculate_memory_health(avg_importance, min_importance, len(memories))

            # Decay risk assessment
            at_risk_count = sum(1 for m in memories if m.metadata.importance < self.cleanup_thresholds[type_name])

            report["memory_types"][type_name] = {
                "total_memories": len(memories),
                "avg_importance": avg_importance,
                "min_importance": min_importance,
                "max_importance": max_importance,
                "avg_age_days": avg_age,
                "oldest_memory_days": oldest_age,
                "newest_memory_days": newest_age,
                "health_score": health_score,
                "at_risk_memories": at_risk_count,
                "risk_percentage": (at_risk_count / len(memories) * 100) if memories else 0
            }

        # Overall system health
        type_health_scores = [type_data["health_score"] for type_data in report["memory_types"].values()]
        report["overall_health"] = sum(type_health_scores) / len(type_health_scores) if type_health_scores else 0

        return report

    def _calculate_memory_health(self, avg_importance: float, min_importance: float, count: int) -> float:
        """Calculate a health score for memory type (0-100)"""
        # Base score from average importance
        importance_score = avg_importance * 100

        # Penalty for low minimum importance
        min_penalty = max(0, (0.3 - min_importance) * 50)

        # Bonus for having many memories (up to a point)
        count_bonus = min(20, count * 0.5)

        health_score = importance_score - min_penalty + count_bonus
        return max(0, min(100, health_score))

    def _get_memory_store(self, memory_system, memory_type: str):
        """Get the appropriate memory store for a memory type"""
        type_map = {
            "working": memory_system.working_memory,
            "episodic": memory_system.episodic_memory,
            "semantic": memory_system.semantic_memory,
            "procedural": memory_system.procedural_memory
        }
        return type_map.get(memory_type)

    async def save(self):
        """Save decay engine state to disk"""
        data = {
            "decay_models": self.decay_models,
            "cleanup_thresholds": self.cleanup_thresholds,
            "decay_history": self.decay_history,
            "memory_lifetimes": {mt: [t.isoformat() for t in times]
                               for mt, times in self.memory_lifetimes.items()},
            "decay_rates": self.decay_rates
        }

        file_path = self.storage_path / "decay_state.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    async def load(self):
        """Load decay engine state from disk"""
        file_path = self.storage_path / "decay_state.json"
        if not file_path.exists():
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.decay_models.update(data.get("decay_models", {}))
            self.cleanup_thresholds.update(data.get("cleanup_thresholds", {}))
            self.decay_history = data.get("decay_history", [])
            self.memory_lifetimes = defaultdict(list, {
                mt: [datetime.fromisoformat(t) for t in times]
                for mt, times in data.get("memory_lifetimes", {}).items()
            })
            self.decay_rates = data.get("decay_rates", {})

            print(f"[DECAY ENGINE]: Loaded decay state")

        except Exception as e:
            print(f"[DECAY ENGINE]: Error loading decay state: {e}")

    async def export_decay_analysis(self) -> Dict[str, Any]:
        """Export detailed decay analysis for monitoring"""
        return {
            "decay_models": self.decay_models.copy(),
            "cleanup_thresholds": self.cleanup_thresholds.copy(),
            "decay_history_summary": [
                {
                    "timestamp": h["timestamp"],
                    "actions_count": h["total_actions"]
                } for h in self.decay_history
            ],
            "memory_lifespan_simulations": {
                mt: await self.simulate_memory_lifespan(mt)
                for mt in self.decay_models.keys()
            }
        }