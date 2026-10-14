"""
Procedural Memory System
Stores learned behaviors, response patterns, and procedural knowledge.
Features:
- Response pattern learning
- Behavioral adaptation
- Skill acquisition tracking
- Automated response generation
- Performance optimization
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import pickle

from .types import MemoryEntry, MemoryMetadata, MemoryType

class ProceduralMemory:
    """
    Procedural memory stores "how to" knowledge and learned behaviors.
    Like human procedural memory, it stores skills and habits.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

        # Skill and behavior storage
        self.skills: Dict[str, Dict[str, Any]] = {}  # skill_name -> skill_data
        self.response_patterns: Dict[str, Dict[str, Any]] = {}  # pattern_id -> pattern_data
        self.behavior_chains: Dict[str, List[Dict[str, Any]]] = {}  # chain_id -> chain_steps
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}  # skill_name -> metrics

        # Memory entries
        self.memory_entries: Dict[str, MemoryEntry] = {}

        print(f"[PROCEDURAL MEMORY]: Initialized at {storage_path}")

    async def store(self, entry: MemoryEntry):
        """Store procedural knowledge"""
        memory_id = entry.metadata.memory_id
        self.memory_entries[memory_id] = entry

        # Extract procedural knowledge
        if isinstance(entry.content, dict):
            await self._process_procedural_data(entry)

        # Save to disk
        await self._save_entry(entry)

    async def _process_procedural_data(self, entry: MemoryEntry):
        """Process procedural knowledge data"""
        content = entry.content

        if "skill" in content:
            await self._store_skill(entry, content["skill"])
        elif "response_pattern" in content:
            await self._store_response_pattern(entry, content["response_pattern"])
        elif "behavior_chain" in content:
            await self._store_behavior_chain(entry, content["behavior_chain"])
        elif "performance" in content:
            await self._store_performance_metric(entry, content["performance"])

    async def _store_skill(self, entry: MemoryEntry, skill: Dict[str, Any]):
        """Store a learned skill"""
        skill_name = skill.get("name", f"skill_{entry.metadata.memory_id}")

        if skill_name not in self.skills:
            self.skills[skill_name] = {
                "name": skill_name,
                "description": skill.get("description", ""),
                "category": skill.get("category", "general"),
                "proficiency": skill.get("proficiency", 0.5),
                "usage_count": 0,
                "success_rate": 0.0,
                "last_used": None,
                "learned_from": [entry.metadata.memory_id],
                "prerequisites": skill.get("prerequisites", []),
                "examples": skill.get("examples", []),
                "created": entry.metadata.timestamp.isoformat(),
                "last_updated": entry.metadata.timestamp.isoformat()
            }
        else:
            # Update existing skill
            existing = self.skills[skill_name]
            existing["usage_count"] += 1
            existing["last_used"] = entry.metadata.timestamp.isoformat()
            existing["last_updated"] = entry.metadata.timestamp.isoformat()

            # Update proficiency based on success
            if "success" in skill:
                success_rate = existing["success_rate"]
                new_success = 1.0 if skill["success"] else 0.0
                existing["success_rate"] = (success_rate * (existing["usage_count"] - 1) + new_success) / existing["usage_count"]

                # Adjust proficiency
                existing["proficiency"] = min(1.0, existing["proficiency"] + (0.1 if skill["success"] else -0.05))

    async def _store_response_pattern(self, entry: MemoryEntry, pattern: Dict[str, Any]):
        """Store a response pattern"""
        pattern_id = pattern.get("id", f"pattern_{entry.metadata.memory_id}")

        self.response_patterns[pattern_id] = {
            "id": pattern_id,
            "trigger": pattern.get("trigger", ""),
            "response_template": pattern.get("response_template", ""),
            "context_conditions": pattern.get("context_conditions", {}),
            "emotional_context": pattern.get("emotional_context", {}),
            "success_rate": pattern.get("success_rate", 0.5),
            "usage_count": 0,
            "last_used": None,
            "source_memories": [entry.metadata.memory_id],
            "created": entry.metadata.timestamp.isoformat(),
            "last_updated": entry.metadata.timestamp.isoformat()
        }

    async def _store_behavior_chain(self, entry: MemoryEntry, chain: Dict[str, Any]):
        """Store a behavior chain"""
        chain_id = chain.get("id", f"chain_{entry.metadata.memory_id}")

        self.behavior_chains[chain_id] = chain.get("steps", [])

        # Store metadata
        chain_metadata = {
            "id": chain_id,
            "description": chain.get("description", ""),
            "trigger_condition": chain.get("trigger_condition", {}),
            "success_rate": chain.get("success_rate", 0.5),
            "execution_count": 0,
            "last_executed": None,
            "source_memory": entry.metadata.memory_id,
            "created": entry.metadata.timestamp.isoformat()
        }

        # Store as skill
        await self._store_skill(entry, {
            "name": f"behavior_chain_{chain_id}",
            "description": chain_metadata["description"],
            "category": "behavior",
            "proficiency": chain_metadata["success_rate"]
        })

    async def _store_performance_metric(self, entry: MemoryEntry, performance: Dict[str, Any]):
        """Store performance metrics for skills"""
        skill_name = performance.get("skill_name", "unknown")

        if skill_name not in self.performance_metrics:
            self.performance_metrics[skill_name] = {
                "skill_name": skill_name,
                "total_attempts": 0,
                "successful_attempts": 0,
                "avg_response_time": 0.0,
                "error_rate": 0.0,
                "metrics_history": [],
                "last_updated": entry.metadata.timestamp.isoformat()
            }

        metrics = self.performance_metrics[skill_name]
        metrics["total_attempts"] += 1

        if performance.get("success", False):
            metrics["successful_attempts"] += 1

        # Update averages
        success_rate = metrics["successful_attempts"] / metrics["total_attempts"]
        metrics["error_rate"] = 1.0 - success_rate

        if "response_time" in performance:
            # Rolling average
            current_avg = metrics["avg_response_time"]
            new_time = performance["response_time"]
            metrics["avg_response_time"] = (current_avg * (metrics["total_attempts"] - 1) + new_time) / metrics["total_attempts"]

        # Store in history
        metrics["metrics_history"].append({
            "timestamp": entry.metadata.timestamp.isoformat(),
            "success": performance.get("success", False),
            "response_time": performance.get("response_time"),
            "memory_id": entry.metadata.memory_id
        })

        # Keep only recent history
        if len(metrics["metrics_history"]) > 100:
            metrics["metrics_history"] = metrics["metrics_history"][-100:]

        metrics["last_updated"] = entry.metadata.timestamp.isoformat()

    async def get_response_pattern(self, context: Dict[str, Any],
                                 emotional_context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Find an appropriate response pattern for the given context"""
        best_pattern = None
        best_score = 0.0

        for pattern_id, pattern in self.response_patterns.items():
            score = self._calculate_pattern_match(pattern, context, emotional_context)

            if score > best_score and score > 0.6:  # Minimum threshold
                best_pattern = pattern
                best_score = score

        if best_pattern:
            # Update usage statistics
            best_pattern["usage_count"] += 1
            best_pattern["last_used"] = datetime.now().isoformat()

        return best_pattern

    def _calculate_pattern_match(self, pattern: Dict[str, Any],
                               context: Dict[str, Any],
                               emotional_context: Dict[str, Any] = None) -> float:
        """Calculate how well a pattern matches the current context"""
        score = 0.0
        total_weight = 0.0

        # Check context conditions
        context_conditions = pattern.get("context_conditions", {})
        for condition_key, condition_value in context_conditions.items():
            total_weight += 1.0
            if condition_key in context and context[condition_key] == condition_value:
                score += 1.0

        # Check emotional context
        if emotional_context:
            emotional_conditions = pattern.get("emotional_context", {})
            for emotion_key, emotion_value in emotional_conditions.items():
                total_weight += 0.5  # Emotional matches are less critical
                if emotion_key in emotional_context and emotional_context[emotion_key] == emotion_value:
                    score += 0.5

        # Factor in success rate and usage
        success_weight = pattern.get("success_rate", 0.5)
        recency_weight = 1.0  # Could be based on last_used timestamp

        final_score = (score / max(total_weight, 1.0)) * success_weight * recency_weight
        return final_score

    async def execute_behavior_chain(self, chain_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a behavior chain"""
        if chain_id not in self.behavior_chains:
            return []

        chain = self.behavior_chains[chain_id]
        results = []

        for step in chain:
            step_result = await self._execute_chain_step(step, context)
            results.append(step_result)

            # Check if step failed and should break chain
            if not step_result.get("success", False) and step.get("break_on_failure", False):
                break

        # Update chain performance
        success_count = sum(1 for r in results if r.get("success", False))
        success_rate = success_count / len(results) if results else 0.0

        # Update the corresponding skill
        skill_name = f"behavior_chain_{chain_id}"
        if skill_name in self.skills:
            self.skills[skill_name]["proficiency"] = success_rate
            self.skills[skill_name]["usage_count"] += 1

        return results

    async def _execute_chain_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step in a behavior chain"""
        step_type = step.get("type", "unknown")
        step_params = step.get("params", {})

        # This would integrate with the action engine
        # For now, return a mock result
        return {
            "step_type": step_type,
            "params": step_params,
            "success": True,
            "result": f"Executed {step_type} with params {step_params}",
            "timestamp": datetime.now().isoformat()
        }

    async def get_skill_proficiency(self, skill_name: str) -> float:
        """Get proficiency level for a skill"""
        if skill_name in self.skills:
            return self.skills[skill_name]["proficiency"]
        return 0.0

    async def improve_skill(self, skill_name: str, success: bool, performance_data: Dict[str, Any] = None):
        """Update skill proficiency based on performance"""
        if skill_name not in self.skills:
            # Create new skill
            await self._store_skill(
                MemoryEntry(
                    content={"skill": {"name": skill_name, "description": "Auto-learned skill"}},
                    content_type="structured"
                ),
                {"name": skill_name, "success": success}
            )
            return

        skill = self.skills[skill_name]
        skill["usage_count"] += 1

        # Update success rate
        success_rate = skill["success_rate"]
        new_success = 1.0 if success else 0.0
        skill["success_rate"] = (success_rate * (skill["usage_count"] - 1) + new_success) / skill["usage_count"]

        # Adjust proficiency
        proficiency_change = 0.05 if success else -0.02
        skill["proficiency"] = max(0.0, min(1.0, skill["proficiency"] + proficiency_change))

        skill["last_used"] = datetime.now().isoformat()
        skill["last_updated"] = datetime.now().isoformat()

        # Store performance metric
        if performance_data:
            await self._store_performance_metric(
                MemoryEntry(
                    content={"performance": {"skill_name": skill_name, **performance_data}},
                    content_type="structured"
                ),
                {"skill_name": skill_name, **performance_data}
            )

    async def get_available_skills(self, category: str = None) -> List[Dict[str, Any]]:
        """Get all available skills, optionally filtered by category"""
        skills = list(self.skills.values())

        if category:
            skills = [s for s in skills if s.get("category") == category]

        # Sort by proficiency
        skills.sort(key=lambda s: s.get("proficiency", 0), reverse=True)
        return skills

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
        """Load procedural memory from disk"""
        if not self.storage_path.exists():
            return

        entry_files = list(self.storage_path.glob("*.json"))
        print(f"[PROCEDURAL MEMORY]: Loading {len(entry_files)} entries...")

        for entry_file in entry_files:
            try:
                with open(entry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Reconstruct entry
                metadata = MemoryMetadata(
                    memory_id=data["memory_id"],
                    memory_type=MemoryType.PROCEDURAL,
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
                await self._process_procedural_data(entry)

            except Exception as e:
                print(f"[PROCEDURAL MEMORY]: Error loading {entry_file}: {e}")

        print(f"[PROCEDURAL MEMORY]: Loaded {len(self.memory_entries)} procedural entries")

    async def save(self):
        """Save all procedural memory to disk"""
        for memory_id, entry in self.memory_entries.items():
            await self._save_entry(entry)

        # Save compiled knowledge
        skills_file = self.storage_path / "skills.pkl"
        with open(skills_file, 'wb') as f:
            pickle.dump(self.skills, f)

        patterns_file = self.storage_path / "response_patterns.pkl"
        with open(patterns_file, 'wb') as f:
            pickle.dump(self.response_patterns, f)

    async def apply_decay(self, decay_rate: float = 0.0002):
        """Apply slow decay to procedural memory (skills improve with practice)"""
        # Skills actually improve slightly over time if used
        for skill_name, skill in self.skills.items():
            if skill["usage_count"] > 0:
                # Slight improvement for established skills
                skill["proficiency"] = min(1.0, skill["proficiency"] + 0.001)
            else:
                # Slow decay for unused skills
                skill["proficiency"] = max(0.1, skill["proficiency"] - decay_rate)

    async def cleanup_decayed_memories(self, threshold: float = 0.1):
        """Remove skills that have decayed below threshold"""
        to_remove = []
        for skill_name, skill in self.skills.items():
            if skill["proficiency"] < threshold and skill["usage_count"] < 5:
                to_remove.append(skill_name)

        for skill_name in to_remove:
            del self.skills[skill_name]

        if to_remove:
            print(f"[PROCEDURAL MEMORY]: Cleaned up {len(to_remove)} decayed skills")

    async def get_stats(self) -> Dict[str, Any]:
        """Get procedural memory statistics"""
        total_skills = len(self.skills)
        total_patterns = len(self.response_patterns)
        total_chains = len(self.behavior_chains)

        # Calculate averages
        avg_proficiency = sum(s.get("proficiency", 0) for s in self.skills.values()) / max(1, total_skills)
        avg_success_rate = sum(s.get("success_rate", 0) for s in self.skills.values()) / max(1, total_skills)

        # Storage size
        total_size = sum(f.stat().st_size for f in self.storage_path.glob("*.json"))

        return {
            "total_skills": total_skills,
            "total_response_patterns": total_patterns,
            "total_behavior_chains": total_chains,
            "avg_skill_proficiency": avg_proficiency,
            "avg_success_rate": avg_success_rate,
            "skill_categories": Counter(s.get("category", "unknown") for s in self.skills.values()),
            "storage_size_mb": total_size / (1024 * 1024)
        }

    async def export(self) -> Dict[str, Any]:
        """Export all procedural memory"""
        return {
            "skills": self.skills.copy(),
            "response_patterns": self.response_patterns.copy(),
            "behavior_chains": self.behavior_chains.copy(),
            "performance_metrics": self.performance_metrics.copy(),
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
        """Import procedural memory"""
        self.skills.update(data.get("skills", {}))
        self.response_patterns.update(data.get("response_patterns", {}))
        self.behavior_chains.update(data.get("behavior_chains", {}))
        self.performance_metrics.update(data.get("performance_metrics", {}))

        # Import memory entries
        for memory_id, entry_data in data.get("memory_entries", {}).items():
            metadata = MemoryMetadata(
                memory_id=memory_id,
                memory_type=MemoryType.PROCEDURAL,
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

        print(f"[PROCEDURAL MEMORY]: Imported {len(self.memory_entries)} procedural entries")