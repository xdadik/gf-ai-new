# pyre-ignore-all-errors
import os  # type: ignore  # pyre-ignore
import asyncio  # type: ignore  # pyre-ignore
from datetime import datetime  # type: ignore  # pyre-ignore
from typing import Dict, List, Any, Optional  # type: ignore  # pyre-ignore
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request  # type: ignore  # pyre-ignore
from fastapi.responses import HTMLResponse, JSONResponse  # type: ignore  # pyre-ignore
from fastapi.staticfiles import StaticFiles  # type: ignore  # pyre-ignore
from fastapi.templating import Jinja2Templates  # type: ignore  # pyre-ignore
import psutil  # type: ignore  # pyre-ignore

from config import SETTINGS  # type: ignore  # pyre-ignore
from db import ConversationStore  # type: ignore  # pyre-ignore

# Import personality system
try:
    from personalities import get_all_personalities, get_personality, PERSONALITIES  # type: ignore  # pyre-ignore
    PERSONALITY_AVAILABLE = True
except ImportError:
    PERSONALITY_AVAILABLE = False

# Bot state reference - will be set by the main runner
bot_state: Dict[str, Any] = {  # type: ignore  # pyre-ignore
    "running": True,
    "user_memory": {},
    "conversation_logs": {},
    "user_personalities": {},
    "log_file": SETTINGS.nova_log_file,
}

app = FastAPI(title="Lily Bot Dashboard")
db_store = ConversationStore(SETTINGS.sqlite_path)


@app.on_event("startup")
async def _startup():
    await db_store.open()


@app.on_event("shutdown")
async def _shutdown():
    await db_store.close()  # type: ignore  # pyre-ignore

# Create templates directory and mount static files
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)

templates = Jinja2Templates(directory=templates_dir)

# WebSocket connections for live updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []  # type: ignore  # pyre-ignore

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get current system stats."""
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    
    return {
        "cpu_percent": cpu_usage,
        "ram_percent": ram.percent,
        "ram_used_mb": ram.used // (1024*1024),
        "ram_total_mb": ram.total // (1024*1024),
        "disk_percent": disk.percent,
        "disk_used_gb": disk.used // (1024**3),
        "disk_total_gb": disk.total // (1024**3),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/memory")
async def get_memory():
    """Get all user memories."""
    memory_data: dict[str, list] = {}  # type: ignore  # pyre-ignore
    for user_id in await db_store.list_user_ids():
        messages = await db_store.get_recent_messages_all_chats(user_id=user_id, limit=20)
        if messages:
            memory_data[str(user_id)] = messages
    return memory_data

@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str):
    """Get specific user memory."""
    messages = await db_store.get_recent_messages_all_chats(user_id=int(user_id), limit=20)
    return {"user_id": user_id, "messages": messages}

@app.post("/api/memory/{user_id}/clear")
async def clear_user_memory(user_id: str):
    """Clear memory for a specific user."""
    await db_store.clear_user_history(user_id=int(user_id))
    bot_state["user_memory"].pop(user_id, None)
    await manager.broadcast({"type": "memory_cleared", "user_id": user_id})
    return {"success": True, "message": f"History cleared for user {user_id}"}

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries."""
    log_file = bot_state.get("log_file", "lily.log")
    logs = []
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                logs = all_lines[-lines:]  # type: ignore  # pyre-ignore
    except Exception as e:
        return {"error": str(e), "logs": []}  # type: ignore  # pyre-ignore
    return {"logs": logs}

@app.get("/api/conversations")
async def get_conversations():
    """Get conversation logs per user."""
    return bot_state.get("conversation_logs", {})

@app.get("/api/bot/status")
async def get_bot_status():
    """Get bot running status."""
    return {"running": bot_state["running"]}  # type: ignore  # pyre-ignore

@app.post("/api/bot/toggle")
async def toggle_bot():
    """Toggle bot on/off."""
    bot_state["running"] = not bot_state["running"]
    await manager.broadcast({"type": "bot_status", "running": bot_state["running"]})  # type: ignore  # pyre-ignore
    return {"running": bot_state["running"]}  # type: ignore  # pyre-ignore

@app.get("/api/personalities")
async def get_personalities():
    """Get all available personalities."""
    if not PERSONALITY_AVAILABLE:
        return {"available": False, "personalities": {}}
    
    from personalities import get_public_personalities  # type: ignore  # pyre-ignore
    
    personalities_data = {}
    for key, p in get_public_personalities().items():
        personalities_data[key] = {
            "name": p.name,
            "display_name": p.display_name,
            "emoji": p.emoji,
            "description": p.description,
            "voice_style": p.voice_style,
            "catchphrases": p.catchphrases,
            "quirks": p.quirks,
            "emotional_tone": p.emotional_tone,
            "response_patterns": p.response_patterns,
            "secret": p.secret
        }
    return {"available": True, "personalities": personalities_data, "has_secrets": True}

@app.get("/api/personalities/user/{user_id}")
async def get_user_personality_endpoint(user_id: str):
    """Get current personality for a user."""
    current = (await db_store.get_personality(user_id=int(user_id))) or bot_state.get("user_personalities", {}).get(user_id, "lily")
    if PERSONALITY_AVAILABLE:
        p = get_personality(current)
        return {
            "user_id": user_id,
            "personality_key": current,
            "personality": {
                "name": p.name,
                "display_name": p.display_name,
                "emoji": p.emoji,
                "description": p.description
            }
        }
    return {"user_id": user_id, "personality_key": current}

@app.post("/api/personalities/user/{user_id}/set/{personality_key}")
async def set_user_personality_endpoint(user_id: str, personality_key: str):
    """Set personality for a user."""
    if not PERSONALITY_AVAILABLE:
        return {"success": False, "error": "Personality system not available"}
    
    if personality_key.lower() not in PERSONALITIES:
        return {"success": False, "error": f"Unknown personality: {personality_key}"}
    
    bot_state["user_personalities"][user_id] = personality_key.lower()
    await db_store.set_personality(user_id=int(user_id), personality=personality_key.lower())
    p = get_personality(personality_key.lower())
    
    await manager.broadcast({
        "type": "personality_changed",
        "user_id": user_id,
        "personality": p.name,
        "display_name": p.display_name,
        "emoji": p.emoji
    })
    
    return {
        "success": True,
        "user_id": user_id,
        "personality": p.name,
        "display_name": p.display_name,
        "emoji": p.emoji,
        "description": p.description
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            stats = await get_stats()
            await websocket.send_json({"type": "stats", "data": stats})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

def log_conversation(user_id: str, role: str, message: str):
    """Log a conversation entry - called by the bot."""
    if user_id not in bot_state["conversation_logs"]:  # type: ignore  # pyre-ignore
        bot_state["conversation_logs"][user_id] = []
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "role": role,
        "message": message[:500]  # Truncate long messages  # type: ignore  # pyre-ignore
    }
    bot_state["conversation_logs"][user_id].append(entry)
    
    # Keep only last 100 entries per user
    if len(bot_state["conversation_logs"][user_id]) > 100:  # type: ignore  # pyre-ignore
        bot_state["conversation_logs"][user_id] = bot_state["conversation_logs"][user_id][-100:]  # type: ignore  # pyre-ignore
    
    # Broadcast to connected dashboard clients
    if manager.active_connections:
        asyncio.create_task(manager.broadcast({
            "type": "new_message",
            "user_id": user_id,
            "data": entry
        }))

def update_user_memory(user_id: str, memory: list):
    """Update user memory reference - called by the bot."""
    bot_state["user_memory"][user_id] = memory
    if manager.active_connections:
        asyncio.create_task(manager.broadcast({
            "type": "memory_update",
            "user_id": user_id,
            "count": len([m for m in memory if m.get("role") != "system"])  # type: ignore  # pyre-ignore
        }))
