"""
WebSocket handler for real-time session updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

router = APIRouter()

# In-memory store of active WebSocket connections per session
# In production, you'd use Redis for multi-instance support
active_connections: Dict[str, Set[WebSocket]] = {}

async def notify_session(session_id: str, message: dict):
    """Send a message to all clients watching a session"""
    if session_id in active_connections:
        disconnected = set()
        for websocket in active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
        # Clean up disconnected clients
        active_connections[session_id] -= disconnected
        if not active_connections[session_id]:
            del active_connections[session_id]

@router.websocket("/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time session updates"""
    await websocket.accept()
    
    # Add to active connections
    if session_id not in active_connections:
        active_connections[session_id] = set()
    active_connections[session_id].add(websocket)
    
    print(f"[WS] Client connected to session: {session_id}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                    
            except asyncio.TimeoutError:
                # Send a ping to keep connection alive
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
                    
    except WebSocketDisconnect:
        print(f"[WS] Client disconnected from session: {session_id}")
    except Exception as e:
        print(f"[WS] Error in session {session_id}: {e}")
    finally:
        # Remove from active connections
        if session_id in active_connections:
            active_connections[session_id].discard(websocket)
            if not active_connections[session_id]:
                del active_connections[session_id]
