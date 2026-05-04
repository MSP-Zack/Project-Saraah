import json
import os
import time
from typing import Dict, List, Optional
from datetime import datetime

class CollaborativeEditor:
    """
    Real-time collaborative document editor.
    Similar to Google Docs - both user and Sarah can type simultaneously.
    Uses operational transformation concepts for conflict resolution.
    """
    
    def __init__(self):
        self.docs_dir = "memory/documents"
        os.makedirs(self.docs_dir, exist_ok=True)
        self.active_doc = None
        self.cursors = {
            "user": {"position": 0, "color": "#ff003c", "name": "You"},
            "sarah": {"position": 0, "color": "#00d4ff", "name": "Sarah"}
        }
    
    def create_document(self, title: str = "Untitled") -> Dict:
        """Create a new collaborative document."""
        doc_id = f"doc_{int(time.time())}"
        doc = {
            "id": doc_id,
            "title": title,
            "content": "",
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "version": 1,
            "operations": [],
            "user_cursor": 0,
            "sarah_cursor": 0,
            "is_sarah_typing": False,
            "suggestions": []
        }
        
        path = os.path.join(self.docs_dir, f"{doc_id}.json")
        with open(path, 'w') as f:
            json.dump(doc, f, indent=2)
        
        self.active_doc = doc
        return {"success": True, "document": doc}
    
    def load_document(self, doc_id: str) -> Dict:
        """Load an existing document."""
        path = os.path.join(self.docs_dir, f"{doc_id}.json")
        if not os.path.exists(path):
            return {"success": False, "error": "Document not found"}
        
        with open(path, 'r') as f:
            doc = json.load(f)
        
        self.active_doc = doc
        return {"success": True, "document": doc}
    
    def save_document(self) -> Dict:
        """Save the active document."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        self.active_doc["modified"] = datetime.now().isoformat()
        self.active_doc["version"] += 1
        
        path = os.path.join(self.docs_dir, f"{self.active_doc['id']}.json")
        with open(path, 'w') as f:
            json.dump(self.active_doc, f, indent=2)
        
        return {"success": True, "document": self.active_doc}
    
    def user_type(self, text: str, position: Optional[int] = None) -> Dict:
        """User types text into the document."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        if position is None:
            position = self.active_doc["user_cursor"]
        
        content = self.active_doc["content"]
        new_content = content[:position] + text + content[position:]
        
        self.active_doc["content"] = new_content
        self.active_doc["user_cursor"] = position + len(text)
        
        # Record operation
        self.active_doc["operations"].append({
            "type": "insert",
            "source": "user",
            "position": position,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
        # Trim operations history
        self.active_doc["operations"] = self.active_doc["operations"][-100:]
        
        self.save_document()
        return {"success": True, "document": self.active_doc}
    
    def user_delete(self, length: int = 1, position: Optional[int] = None) -> Dict:
        """User deletes text."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        if position is None:
            position = self.active_doc["user_cursor"]
        
        content = self.active_doc["content"]
        deleted = content[position:position + length]
        new_content = content[:position] + content[position + length:]
        
        self.active_doc["content"] = new_content
        self.active_doc["user_cursor"] = position
        
        self.active_doc["operations"].append({
            "type": "delete",
            "source": "user",
            "position": position,
            "length": length,
            "deleted_text": deleted,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_document()
        return {"success": True, "document": self.active_doc}
    
    def sarah_type(self, text: str, position: Optional[int] = None) -> Dict:
        """Sarah types text into the document."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        if position is None:
            # Sarah types at her own cursor position
            position = self.active_doc.get("sarah_cursor", 0)
        
        content = self.active_doc["content"]
        new_content = content[:position] + text + content[position:]
        
        self.active_doc["content"] = new_content
        self.active_doc["sarah_cursor"] = position + len(text)
        self.active_doc["is_sarah_typing"] = True
        
        self.active_doc["operations"].append({
            "type": "insert",
            "source": "sarah",
            "position": position,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_document()
        return {"success": True, "document": self.active_doc}
    
    def sarah_suggest(self, text: str, explanation: str = "") -> Dict:
        """Sarah adds a suggestion/comment rather than direct edit."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        suggestion = {
            "id": len(self.active_doc.get("suggestions", [])),
            "text": text,
            "explanation": explanation,
            "timestamp": datetime.now().isoformat(),
            "accepted": None  # None = pending, True = accepted, False = rejected
        }
        
        if "suggestions" not in self.active_doc:
            self.active_doc["suggestions"] = []
        
        self.active_doc["suggestions"].append(suggestion)
        self.save_document()
        return {"success": True, "suggestion": suggestion}
    
    def accept_suggestion(self, suggestion_id: int) -> Dict:
        """Accept Sarah's suggestion."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        for s in self.active_doc.get("suggestions", []):
            if s["id"] == suggestion_id:
                s["accepted"] = True
                # Insert the suggestion text at the end
                self.active_doc["content"] += "\n" + s["text"]
                self.save_document()
                return {"success": True, "document": self.active_doc}
        
        return {"success": False, "error": "Suggestion not found"}
    
    def reject_suggestion(self, suggestion_id: int) -> Dict:
        """Reject Sarah's suggestion."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        for s in self.active_doc.get("suggestions", []):
            if s["id"] == suggestion_id:
                s["accepted"] = False
                self.save_document()
                return {"success": True}
        
        return {"success": False, "error": "Suggestion not found"}
    
    def set_cursor(self, who: str, position: int) -> Dict:
        """Set cursor position for user or Sarah."""
        if not self.active_doc:
            return {"success": False, "error": "No active document"}
        
        key = f"{who}_cursor"
        self.active_doc[key] = max(0, min(position, len(self.active_doc["content"])))
        return {"success": True, "cursor": self.active_doc[key]}
    
    def list_documents(self) -> List[Dict]:
        """List all saved documents."""
        docs = []
        for filename in os.listdir(self.docs_dir):
            if filename.endswith('.json'):
                path = os.path.join(self.docs_dir, filename)
                with open(path, 'r') as f:
                    doc = json.load(f)
                docs.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "modified": doc["modified"],
                    "preview": doc["content"][:100] + "..." if len(doc["content"]) > 100 else doc["content"]
                })
        return sorted(docs, key=lambda x: x["modified"], reverse=True)
    
    def get_active_document(self) -> Optional[Dict]:
        return self.active_doc
    
    def export_to_txt(self, doc_id: str) -> Dict:
        """Export document to plain text file."""
        result = self.load_document(doc_id)
        if not result["success"]:
            return result
        
        doc = result["document"]
        txt_path = os.path.join(self.docs_dir, f"{doc_id}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(doc["content"])
        
        return {"success": True, "path": txt_path}


# Plugin interface
class Plugin:
    def __init__(self):
        self.editor = CollaborativeEditor()
    
    def get_info(self) -> Dict:
        return {
            "name": "Collaborative Editor",
            "description": "Write documents together with Sarah",
            "version": "1.0"
        }
    
    def create_document(self, title: str = "Untitled") -> Dict:
        return self.editor.create_document(title)
    
    def load_document(self, doc_id: str) -> Dict:
        return self.editor.load_document(doc_id)
    
    def user_type(self, text: str, position: int = None) -> Dict:
        return self.editor.user_type(text, position)
    
    def user_delete(self, length: int = 1, position: int = None) -> Dict:
        return self.editor.user_delete(length, position)
    
    def sarah_type(self, text: str, position: int = None) -> Dict:
        return self.editor.sarah_type(text, position)
    
    def sarah_suggest(self, text: str, explanation: str = "") -> Dict:
        return self.editor.sarah_suggest(text, explanation)
    
    def accept_suggestion(self, suggestion_id: int) -> Dict:
        return self.editor.accept_suggestion(suggestion_id)
    
    def reject_suggestion(self, suggestion_id: int) -> Dict:
        return self.editor.reject_suggestion(suggestion_id)
    
    def set_cursor(self, who: str, position: int) -> Dict:
        return self.editor.set_cursor(who, position)
    
    def list_documents(self) -> List[Dict]:
        return self.editor.list_documents()
    
    def get_active(self) -> Optional[Dict]:
        return self.editor.get_active_document()
    
    def save(self) -> Dict:
        return self.editor.save_document()
    
    def export(self, doc_id: str) -> Dict:
        return self.editor.export_to_txt(doc_id)
