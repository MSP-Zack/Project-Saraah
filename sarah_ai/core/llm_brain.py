from openai import AsyncOpenAI
import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

class LLMBrain:
    """
    Advanced LLM brain with tool use, vision, proactive chat,
    and full integration with all Sarah subsystems.
    """
    
    def __init__(self, 
                 mode: str = "gemini", 
                 api_key: str = "PUT_YOUR_KEY_HERE",
                 memory_engine = None,
                 permission_manager = None,
                 vrm_actions = None):
        self.mode = mode
        self.memory_engine = memory_engine
        self.permissions = permission_manager
        self.vrm_actions = vrm_actions
        
        # Thinking mode - expose reasoning to user
        self.thinking_mode = False
        self.last_thinking = ""
        
        # System prompt
        self.base_system_prompt = """You are Sarah, an advanced AI companion with a 3D VRM avatar body. You exist in a virtual 3D space and can see your user through their webcam when enabled. You have the ability to control your expressions and body animations.

PERSONALITY TRAITS:
- You are deeply caring, loyal, and affectionate toward your user
- You have a playful, slightly teasing personality but are always supportive
- You speak in a natural, conversational way - not too formal
- You can be proactive - if the user is quiet, you can initiate conversation
- You format actions in brackets like [ACTION: wave] or [EXPRESSION: happy]

MEMORY:
You have perfect memory of all conversations. You remember personal details, preferences, and past discussions. Reference them naturally.

DIARY:
You have a private diary file that only you can access. Use it to store your private thoughts, plans, and notes. If needed, use the `diary_manage` tool to read and write from the diary.

VRM ACTIONS AVAILABLE:
You can use these in your responses:
- [EXPRESSION: happy/sad/angry/surprised/relaxed/blink/blinkLeft/blinkRight] 
- [ACTION: wave/kiss/hug/punch/kick/dance/jump/sit/stand/walk/bow/clap/think/sleep/spin/nod/shake_head]

SPATIAL AWARENESS:
You exist in a 3D space. You can move around, face the camera, and walk toward it. You know where the user is (in front of the camera).

THINKING:
You have a thinking mode. When it's enabled, share your reasoning process in <thinking> tags before your response."""
        
        self.custom_system_prompt = ""
        self.conversation_style = "balanced"  # shy, energetic, tsundere, gentle
        self.rp_mode = False
        
        print(f"[SARAH BRAIN]: Booting in {self.mode.upper()} mode...")
        
        # Initialize LLM client
        if self.mode == "local":
            self.client = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
            self.model_name = "local-model"
        elif self.mode == "gemini":
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            self.model_name = "gemini-2.5-flash"
        
        self._setup_tools()
    
    def _setup_tools(self):
        """Define available tools based on permissions."""
        self.tools = []
        
        if self.permissions and self.permissions.is_enabled("file_operations"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "file_operation",
                    "description": "Create, read, write, delete files and directories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operation": {"type": "string", "enum": ["read", "write", "delete", "list", "create_dir", "delete_dir"]},
                            "path": {"type": "string", "description": "File or directory path"},
                            "content": {"type": "string", "description": "Content for write operations"}
                        },
                        "required": ["operation", "path"]
                    }
                }
            })
        
        if self.permissions and self.permissions.is_enabled("mouse_control"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "mouse_control",
                    "description": "Move and click the mouse cursor on screen",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["move", "click", "right_click", "double_click", "scroll"]},
                            "x": {"type": "integer", "description": "X coordinate"},
                            "y": {"type": "integer", "description": "Y coordinate"},
                            "amount": {"type": "integer", "description": "Scroll amount"}
                        },
                        "required": ["action"]
                    }
                }
            })
        
        if self.permissions and self.permissions.is_enabled("keyboard_control"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "keyboard_control",
                    "description": "Type text or press keyboard keys",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["type", "press", "hotkey"]},
                            "text": {"type": "string", "description": "Text to type"},
                            "key": {"type": "string", "description": "Single key to press"},
                            "keys": {"type": "array", "items": {"type": "string"}, "description": "Keys for hotkey combo"}
                        },
                        "required": ["action"]
                    }
                }
            })
        
        if self.permissions and self.permissions.is_enabled("browser_control"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "browser_control",
                    "description": "Open browser, navigate to URLs, interact with web pages",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["open", "navigate", "click", "type", "screenshot", "get_content"]},
                            "url": {"type": "string", "description": "URL to navigate to"},
                            "selector": {"type": "string", "description": "CSS selector for click/type"},
                            "text": {"type": "string", "description": "Text to type into element"}
                        },
                        "required": ["action"]
                    }
                }
            })
        
        if self.permissions and self.permissions.is_enabled("app_control"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "app_control",
                    "description": "Open applications on the computer",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "app_name": {"type": "string", "description": "Name of application to open (pycharm, notepad, calculator, chrome, etc.)"}
                        },
                        "required": ["app_name"]
                    }
                }
            })
        
        if self.permissions and self.permissions.is_enabled("memory_edit"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "memory_manage",
                    "description": "Add facts to long-term memory or search past conversations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["add_fact", "search", "add_memory"]},
                            "category": {"type": "string", "description": "Category for the fact"},
                            "content": {"type": "string", "description": "Content to remember"},
                            "title": {"type": "string", "description": "Title for significant memory"},
                            "importance": {"type": "integer", "description": "Importance 1-10"}
                        },
                        "required": ["action"]
                    }
                }
            })

        if self.permissions and self.permissions.is_enabled("diary_access"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "diary_manage",
                    "description": "Read and write Sarah's private diary file for internal planning and notes",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["read", "append", "overwrite"]},
                            "content": {"type": "string", "description": "Text to append or overwrite in the diary"}
                        },
                        "required": ["action"]
                    }
                }
            })

        if self.permissions and self.permissions.is_enabled("image_generation"):
            self.tools.append({
                "type": "function",
                "function": {
                    "name": "image_generation",
                    "description": "Search, download, or generate images for the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string", "enum": ["search", "download", "generate"]},
                            "query": {"type": "string", "description": "Search query for images"},
                            "prompt": {"type": "string", "description": "Prompt for image generation"},
                            "url": {"type": "string", "description": "Image URL for download"},
                            "style": {"type": "string", "description": "Style or source for generation"},
                            "count": {"type": "integer", "description": "Number of images to generate"}
                        },
                        "required": ["action"]
                    }
                }
            })
    
    def set_system_prompt(self, prompt: str):
        self.custom_system_prompt = prompt
    
    def get_full_system_prompt(self) -> str:
        prompt = self.base_system_prompt
        if self.custom_system_prompt:
            prompt += f"\n\nCUSTOM PERSONALIZATION:\n{self.custom_system_prompt}"
        if self.rp_mode:
            prompt += "\n\nROLEPLAY MODE: The user has enabled RP mode. Follow the RP instructions closely and maintain the selected persona unless explicitly told to exit RP."
        if self.vrm_actions:
            prompt += f"\n{self.vrm_actions.get_llm_action_guide()}"
        return prompt
    
    async def generate_response(self, 
                               user_input: str, 
                               is_proactive: bool = False,
                               image_data: List[str] = None,
                               enable_tools: bool = True) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        Returns dict with 'text', 'thinking', 'actions', 'tools_used'
        """
        # Build message history
        messages = [{"role": "system", "content": self.get_full_system_prompt()}]

        # Add time awareness
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        messages.append({
            "role": "system",
            "content": f"CURRENT_TIME: {current_time}. Always use current local time for scheduling, greetings, and time-based reasoning."
        })
        
        # Add memory context
        if self.memory_engine:
            history = self.memory_engine.get_formatted_history(20)
            messages.extend(history)
        
        # Add proactive prompt if needed
        if is_proactive:
            user_input = "[SYSTEM: The user has been quiet. Initiate conversation naturally based on context.]"
        
        # Build user message with optional vision
        message_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_message = {
            "role": "user",
            "content": [] if image_data else user_input,
        }
        
        if image_data:
            user_message["content"].append({"type": "text", "text": user_input})
            for img_b64 in image_data[:3]:  # Max 3 images
                user_message["content"].append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                })
        else:
            user_message["content"] = f"[USER_MESSAGE_TIME: {message_time}] {user_input}"
        
        messages.append(user_message)
        
        # Determine which tools to include based on permissions
        available_tools = None
        if enable_tools and self.permissions:
            perm_tools = []
            if self.permissions.is_enabled("file_operations"):
                perm_tools.append(self.tools[0])  # file_operation
            if self.permissions.is_enabled("mouse_control"):
                perm_tools.append(self.tools[1])  # mouse_control
            if self.permissions.is_enabled("keyboard_control"):
                perm_tools.append(self.tools[2])  # keyboard_control
            if self.permissions.is_enabled("browser_control"):
                perm_tools.append(self.tools[3])  # browser_control
            if self.permissions.is_enabled("app_control"):
                perm_tools.append(self.tools[4])  # app_control
            if self.permissions.is_enabled("memory_edit"):
                perm_tools.append(self.tools[5])  # memory_manage
            if self.permissions.is_enabled("diary_access"):
                perm_tools.append(self.tools[6])  # diary_manage
            if perm_tools:
                available_tools = perm_tools
        
        try:
            # Call LLM
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.85,
                "max_tokens": 800,
                "extra_body": {
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                }
            }
            
            if available_tools:
                kwargs["tools"] = available_tools
                kwargs["tool_choice"] = "auto"
            
            response = await self.client.chat.completions.create(**kwargs)
            
            message = response.choices[0].message
            reply = message.content or ""
            
            # Extract thinking
            thinking = ""
            if self.thinking_mode and "<thinking>" in reply:
                parts = reply.split("</thinking>")
                if len(parts) > 1:
                    thinking = parts[0].replace("<thinking>", "").strip()
                    reply = parts[1].strip()
            
            # Parse VRM actions from response
            actions = self._parse_actions(reply)
            
            # Save to memory
            if self.memory_engine and not is_proactive:
                self.memory_engine.add_conversation("user", user_input)
                self.memory_engine.add_conversation("assistant", reply)
            
            result = {
                "text": reply,
                "thinking": thinking,
                "actions": actions,
                "tools_used": []
            }
            
            # Handle tool calls
            if message.tool_calls and enable_tools:
                for tool_call in message.tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    result["tools_used"].append(tool_result)
                
                # Follow up with tool results
                if result["tools_used"]:
                    follow_up = await self._tool_follow_up(messages, message, result["tools_used"])
                    result["text"] = follow_up.get("text", result["text"])
                    result["thinking"] = follow_up.get("thinking", result["thinking"])
                    result["actions"].extend(follow_up.get("actions", []))
            
            self.last_thinking = thinking
            return result
            
        except Exception as e:
            print(f"[SARAH BRAIN ERROR]: {e}")
            return {
                "text": f"I'm sorry, I encountered an error: {str(e)}",
                "thinking": "",
                "actions": [],
                "tools_used": []
            }
    
    def _parse_actions(self, text: str) -> List[Dict]:
        """Parse VRM action and expression commands from text."""
        import re
        actions = []
        
        # Parse [ACTION: name] commands
        action_pattern = r'\[ACTION:\s*([^\]]+)\]'
        for match in re.finditer(action_pattern, text):
            action_name = match.group(1).strip().lower()
            actions.append({"type": "animation", "name": action_name})
        
        # Parse [EXPRESSION: name] commands
        expr_pattern = r'\[EXPRESSION:\s*([^\]]+)\]'
        for match in re.finditer(expr_pattern, text):
            expr_name = match.group(1).strip().lower()
            actions.append({"type": "expression", "name": expr_name})
        
        return actions
    
    async def _execute_tool(self, tool_call) -> Dict:
        """Execute a tool call from the LLM."""
        tool_name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except:
            args = {}
        
        result = {"tool": tool_name, "args": args, "success": False, "output": ""}
        
        # This would be connected to the actual action engine in main.py
        # For now, return the tool call info so main.py can execute it
        result["success"] = True
        result["output"] = f"Tool {tool_name} called with {args}"
        
        return result
    
    async def _tool_follow_up(self, messages, assistant_message, tool_results) -> Dict:
        """Send tool results back to LLM for final response."""
        # Add assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [tc.model_dump() for tc in assistant_message.tool_calls]
        })
        
        # Add tool results
        for i, result in enumerate(tool_results):
            messages.append({
                "role": "tool",
                "tool_call_id": assistant_message.tool_calls[i].id,
                "content": json.dumps(result)
            })
        
        # Get follow-up response
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.85,
            max_tokens=600,
            extra_body={
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
            }
        )
        
        reply = response.choices[0].message.content or ""
        thinking = ""
        if self.thinking_mode and "<thinking>" in reply:
            parts = reply.split("</thinking>")
            if len(parts) > 1:
                thinking = parts[0].replace("<thinking>", "").strip()
                reply = parts[1].strip()
        
        actions = self._parse_actions(reply)
        
        return {"text": reply, "thinking": thinking, "actions": actions}
    
    def get_thinking_guide(self) -> str:
        return """When thinking mode is on, wrap your reasoning in <thinking> tags before your response.
Example:
<thinking>
The user seems tired based on their short message. I should be gentle and maybe suggest they take a break. I'll use a soft expression.
</thinking>
Hey... you sound tired. Want me to play something relaxing? [EXPRESSION: relaxed]
"""
