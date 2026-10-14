import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import re
import math

class MemoryEngine:
    """
    Advanced persistent memory system for Sarah.
    Stores every conversation thread with metadata, allows manual editing,
    searching, and semantic organization.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        self.conversations_file = os.path.join(memory_dir, "conversations.json")
        self.facts_file = os.path.join(memory_dir, "long_term_facts.json")
        self.memories_file = os.path.join(memory_dir, "memories.json")
        self.vision_file = os.path.join(memory_dir, "vision_observations.json")
        self.librarian_state_file = os.path.join(memory_dir, "librarian_state.json")
        self.memory_archive_file = os.path.join(memory_dir, "memory_archive.json")
        self.embeddings_file = os.path.join(memory_dir, "memory_embeddings.json")
        self.links_file = os.path.join(memory_dir, "memory_links.json")
        
        self.conversations = self._load_json(self.conversations_file, [])
        self.facts = self._load_json(self.facts_file, {})
        self.memories = self._load_json(self.memories_file, [])
        self.vision_observations = self._load_json(self.vision_file, [])
        self.librarian_state = self._load_json(self.librarian_state_file, {})
        self.memory_archive = self._load_json(self.memory_archive_file, [])
        self.embeddings = self._load_json(self.embeddings_file, {})
        self.memory_links = self._load_json(self.links_file, [])
    
    def _load_json(self, path: str, default: Any) -> Any:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    
    def _save_json(self, path: str, data: Any):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_conversation(self, role: str, content: str, metadata: Dict = None):
        """Add a message to the current conversation thread."""
        entry = {
            "id": len(self.conversations),
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.conversations.append(entry)
        self._save_json(self.conversations_file, self.conversations)
    
    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        """Get recent conversation history formatted for LLM context."""
        return self.conversations[-limit:]
    
    def get_formatted_history(self, limit: int = 20) -> List[Dict[str, str]]:
        """Get history formatted as OpenAI message objects."""
        history = []
        for msg in self.conversations[-limit:]:
            history.append({"role": msg["role"], "content": msg["content"]})
        return history
    
    def add_fact(self, category: str, fact: str):
        """Add a long-term fact about the user or world."""
        if category not in self.facts:
            self.facts[category] = []
        self.facts[category].append({
            "fact": fact,
            "timestamp": datetime.now().isoformat()
        })
        self._save_json(self.facts_file, self.facts)
    
    def get_facts(self, category: Optional[str] = None) -> Dict or List:
        if category:
            return self.facts.get(category, [])
        return self.facts
    
    def add_memory(self, title: str, content: str, importance: int = 5):
        """Add a significant memory with importance score (1-10)."""
        memory = {
            "id": len(self.memories),
            "title": title,
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }
        self.memories.append(memory)
        # Sort by importance
        self.memories.sort(key=lambda x: x["importance"], reverse=True)
        self._save_json(self.memories_file, self.memories)
        return memory

    @staticmethod
    def _memory_text(memory: Dict[str, Any]) -> str:
        return f"{memory.get('title', '')}: {memory.get('content', '')}".strip()

    async def add_memory_async(self, title: str, content: str, importance: int = 5) -> Dict[str, Any]:
        """Save a memory and index it with a configured embedding provider."""
        memory = self.add_memory(title, content, importance)
        try:
            from core.embedding_provider import EmbeddingProvider
        except ImportError:
            from .embedding_provider import EmbeddingProvider
        provider = EmbeddingProvider()
        if provider.is_available:
            try:
                vectors = await provider.embed([self._memory_text(memory)])
                if vectors:
                    self.embeddings[str(memory["id"])] = vectors[0]
                    self._save_json(self.embeddings_file, self.embeddings)
            except Exception as error:
                print(f"[MEMORY EMBEDDINGS]: Indexing failed: {error}")
        return memory
    
    def search_memories(self, query: str) -> List[Dict]:
        """Simple keyword search across all memory."""
        query_lower = query.lower()
        results = []
        for mem in self.memories:
            if query_lower in mem["title"].lower() or query_lower in mem["content"].lower():
                results.append(mem)
        for conv in self.conversations:
            if query_lower in conv.get("content", "").lower():
                results.append({
                    "type": "conversation",
                    "timestamp": conv["timestamp"],
                    "role": conv["role"],
                    "content": conv["content"]
                })
        return results

    def get_relevant_memories(self, query: str, limit: int = 8) -> List[Dict]:
        """Return durable memories ranked by simple token overlap.

        This is a dependable fallback for prompt recall when no embedding
        provider is configured. It intentionally excludes conversation rows.
        """
        tokens = {
            token for token in re.findall(r"\b\w{3,}\b", query.lower())
            if token not in {"the", "and", "that", "this", "with", "from", "what", "when", "how"}
        }
        if not tokens:
            return []

        ranked = []
        for memory in self.memories:
            text = f"{memory.get('title', '')} {memory.get('content', '')}".lower()
            overlap = len(tokens.intersection(set(re.findall(r"\b\w{3,}\b", text))))
            if overlap:
                score = overlap + (memory.get("importance", 5) / 10)
                ranked.append((score, memory))
        ranked.sort(key=lambda item: (item[0], item[1].get("timestamp", "")), reverse=True)
        return [memory for _, memory in ranked[:max(1, min(limit, 20))]]

    async def get_relevant_memories_async(self, query: str, limit: int = 8) -> List[Dict]:
        """Use provider-backed semantic recall when indexed vectors exist."""
        try:
            from core.embedding_provider import EmbeddingProvider
        except ImportError:
            from .embedding_provider import EmbeddingProvider
        provider = EmbeddingProvider()
        if not provider.is_available or not self.embeddings:
            return self.get_relevant_memories(query, limit)
        try:
            vectors = await provider.embed([query])
            if not vectors:
                return self.get_relevant_memories(query, limit)
            query_vector = vectors[0]
            query_norm = math.sqrt(sum(value * value for value in query_vector)) or 1.0
            ranked = []
            by_id = {str(memory.get("id")): memory for memory in self.memories}
            for memory_id, vector in self.embeddings.items():
                memory = by_id.get(str(memory_id))
                if not memory or not vector:
                    continue
                vector_norm = math.sqrt(sum(value * value for value in vector)) or 1.0
                score = sum(a * b for a, b in zip(query_vector, vector)) / (query_norm * vector_norm)
                ranked.append((score, memory))
            ranked.sort(key=lambda item: item[0], reverse=True)
            return [memory for score, memory in ranked[:max(1, min(limit, 20))] if score >= 0.25]
        except Exception as error:
            print(f"[MEMORY EMBEDDINGS]: Retrieval failed, using lexical fallback: {error}")
            return self.get_relevant_memories(query, limit)

    async def backfill_embeddings(self, limit: int = 100) -> Dict[str, Any]:
        """Index a bounded batch of existing memories with explicit user intent."""
        try:
            from core.embedding_provider import EmbeddingProvider
        except ImportError:
            from .embedding_provider import EmbeddingProvider
        provider = EmbeddingProvider()
        if not provider.is_available:
            return {"indexed": 0, "remaining": len(self.memories), "available": False}
        missing = [memory for memory in self.memories if str(memory.get("id")) not in self.embeddings]
        batch = missing[:max(1, min(limit, 500))]
        if not batch:
            return {"indexed": 0, "remaining": 0, "available": True}
        vectors = await provider.embed([self._memory_text(memory) for memory in batch])
        if vectors:
            for memory, vector in zip(batch, vectors):
                self.embeddings[str(memory["id"])] = vector
            self._save_json(self.embeddings_file, self.embeddings)
        return {"indexed": len(vectors or []), "remaining": max(0, len(missing) - len(vectors or [])), "available": True}

    def find_semantic_duplicate_candidates(self, threshold: float = 0.90, limit: int = 50) -> List[Dict[str, Any]]:
        """Return high-similarity pairs for review; never merges automatically."""
        by_id = {str(memory.get("id")): memory for memory in self.memories}
        candidates = []
        ids = [memory_id for memory_id in self.embeddings if memory_id in by_id]
        for index, first_id in enumerate(ids):
            first_vector = self.embeddings[first_id]
            first_norm = math.sqrt(sum(value * value for value in first_vector)) or 1.0
            for second_id in ids[index + 1:]:
                second_vector = self.embeddings[second_id]
                second_norm = math.sqrt(sum(value * value for value in second_vector)) or 1.0
                score = sum(a * b for a, b in zip(first_vector, second_vector)) / (first_norm * second_norm)
                if score >= threshold:
                    candidates.append({"canonical": by_id[first_id], "duplicate": by_id[second_id], "similarity": round(score, 4)})
        candidates.sort(key=lambda item: item["similarity"], reverse=True)
        return candidates[:max(1, min(limit, 200))]

    def build_memory_links(self, threshold: float = 0.72, limit: int = 100) -> Dict[str, int]:
        """Create idempotent, evidence-backed links between related memories."""
        by_id = {str(memory.get("id")): memory for memory in self.memories}
        links = {(str(link["from_id"]), str(link["to_id"])) for link in self.memory_links}
        created = 0
        ids = [memory_id for memory_id in self.embeddings if memory_id in by_id]
        for index, first_id in enumerate(ids):
            first_vector = self.embeddings[first_id]
            first_norm = math.sqrt(sum(value * value for value in first_vector)) or 1.0
            for second_id in ids[index + 1:]:
                second_vector = self.embeddings[second_id]
                second_norm = math.sqrt(sum(value * value for value in second_vector)) or 1.0
                score = sum(a * b for a, b in zip(first_vector, second_vector)) / (first_norm * second_norm)
                ordered = tuple(sorted((str(first_id), str(second_id))))
                if score >= threshold and ordered not in links:
                    self.memory_links.append({
                        "from_id": ordered[0],
                        "to_id": ordered[1],
                        "similarity": round(score, 4),
                        "reason": "embedding_similarity",
                        "created_at": datetime.now().isoformat(),
                    })
                    links.add(ordered)
                    created += 1
                    if created >= limit:
                        break
            if created >= limit:
                break
        if created:
            self._save_json(self.links_file, self.memory_links[-1000:])
        return {"created": created, "total": len(self.memory_links)}

    def get_memory_links(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.memory_links[-max(1, min(limit, 1000)):]

    def merge_memories(self, canonical_id: int, duplicate_id: int, reason: str = "reviewed semantic duplicate") -> Dict[str, Any]:
        """Soft-archive a reviewed duplicate and preserve its provenance."""
        canonical = next((memory for memory in self.memories if memory.get("id") == canonical_id), None)
        duplicate = next((memory for memory in self.memories if memory.get("id") == duplicate_id), None)
        if not canonical or not duplicate or canonical_id == duplicate_id:
            raise ValueError("both distinct memory IDs must exist")
        archived = {**duplicate, "archived_at": datetime.now().isoformat(), "archive_reason": reason, "merged_into": canonical_id}
        self.memories = [memory for memory in self.memories if memory.get("id") != duplicate_id]
        self.memory_archive.append(archived)
        self.embeddings.pop(str(duplicate_id), None)
        self.memory_links = [link for link in self.memory_links if str(duplicate_id) not in {str(link.get("from_id")), str(link.get("to_id"))}]
        self._save_json(self.memories_file, self.memories)
        self._save_json(self.memory_archive_file, self.memory_archive)
        self._save_json(self.embeddings_file, self.embeddings)
        self._save_json(self.links_file, self.memory_links)
        return {"canonical": canonical, "archived": archived}

    def curate_exact_duplicates(self) -> Dict[str, int]:
        """Archive exact duplicate memories without destroying user data."""
        seen = {}
        kept = []
        archived = []
        for memory in self.memories:
            key = (
                re.sub(r"\s+", " ", str(memory.get("title", "")).strip().lower()),
                re.sub(r"\s+", " ", str(memory.get("content", "")).strip().lower()),
            )
            canonical = seen.get(key)
            if canonical is None:
                seen[key] = memory
                kept.append(memory)
                continue
            archived.append({
                **memory,
                "archived_at": datetime.now().isoformat(),
                "archive_reason": "exact_duplicate",
                "canonical_id": canonical.get("id"),
            })

        if not archived:
            return {"scanned": len(self.memories), "archived": 0}

        self.memories = kept
        self.memory_archive.extend(archived)
        self._save_json(self.memories_file, self.memories)
        self._save_json(self.memory_archive_file, self.memory_archive)
        return {"scanned": len(self.memories) + len(archived), "archived": len(archived)}

    def run_librarian(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Run the idempotent, reversible maintenance pass once per day."""
        current = now or datetime.now()
        day = current.strftime("%Y-%m-%d")
        if self.librarian_state.get("last_run_day") == day:
            return {"status": "already_ran", "day": day, "result": self.librarian_state.get("last_result", {})}

        result = self.curate_exact_duplicates()
        result["semantic_candidates"] = len(self.find_semantic_duplicate_candidates())
        result["links"] = self.build_memory_links()
        self.librarian_state = {
            "last_run_day": day,
            "last_run_at": current.isoformat(),
            "last_result": result,
        }
        self._save_json(self.librarian_state_file, self.librarian_state)
        return {"status": "completed", "day": day, "result": result}
    
    def edit_conversation(self, message_id: int, new_content: str) -> bool:
        """Manually edit a specific conversation entry."""
        for msg in self.conversations:
            if msg["id"] == message_id:
                msg["content"] = new_content
                msg["edited"] = datetime.now().isoformat()
                self._save_json(self.conversations_file, self.conversations)
                return True
        return False
    
    def delete_conversation(self, message_id: int) -> bool:
        """Delete a specific conversation entry."""
        self.conversations = [m for m in self.conversations if m["id"] != message_id]
        # Reindex
        for i, msg in enumerate(self.conversations):
            msg["id"] = i
        self._save_json(self.conversations_file, self.conversations)
        return True
    
    def edit_memory(self, memory_id: int, new_title: str = None, new_content: str = None, new_importance: int = None) -> bool:
        for mem in self.memories:
            if mem["id"] == memory_id:
                if new_title: mem["title"] = new_title
                if new_content: mem["content"] = new_content
                if new_importance is not None: mem["importance"] = new_importance
                mem["edited"] = datetime.now().isoformat()
                self._save_json(self.memories_file, self.memories)
                return True
        return False
    
    def delete_memory(self, memory_id: int) -> bool:
        self.memories = [m for m in self.memories if m["id"] != memory_id]
        for i, mem in enumerate(self.memories):
            mem["id"] = i
        self._save_json(self.memories_file, self.memories)
        return True
    
    def get_stats(self) -> Dict[str, int]:
        return {
            "total_conversations": len(self.conversations),
            "total_memories": len(self.memories),
            "total_facts": sum(len(v) for v in self.facts.values()),
            "fact_categories": len(self.facts),
            "total_vision_observations": len(self.vision_observations),
            "embedded_memories": len(self.embeddings),
        }
    
    def get_all_memories(self) -> List[Dict]:
        return self.memories

    def add_vision_observation(self, description: str, source: str = "webcam", limit: int = 500) -> Dict:
        """Persist a visual observation for later recall."""
        observation = {
            "id": len(self.vision_observations),
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "description": description.strip(),
        }
        self.vision_observations.append(observation)
        self.vision_observations = self.vision_observations[-limit:]
        self._save_json(self.vision_file, self.vision_observations)
        return observation

    def get_vision_observations(self, limit: int = 100) -> List[Dict]:
        """Return the most recent visual observations."""
        return self.vision_observations[-max(1, min(limit, 500)):]
    
    def clear_conversations(self):
        self.conversations = []
        self._save_json(self.conversations_file, [])
