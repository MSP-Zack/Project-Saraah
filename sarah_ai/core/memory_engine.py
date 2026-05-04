import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

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
        
        self.conversations = self._load_json(self.conversations_file, [])
        self.facts = self._load_json(self.facts_file, {})
        self.memories = self._load_json(self.memories_file, [])
    
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
        self.memories.append({
            "id": len(self.memories),
            "title": title,
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        })
        # Sort by importance
        self.memories.sort(key=lambda x: x["importance"], reverse=True)
        self._save_json(self.memories_file, self.memories)
    
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
            "fact_categories": len(self.facts)
        }
    
    def get_all_memories(self) -> List[Dict]:
        return self.memories
    
    def clear_conversations(self):
        self.conversations = []
        self._save_json(self.conversations_file, [])
