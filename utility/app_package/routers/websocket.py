from typing import List, Dict, Tuple
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, APIRouter, Depends, HTTPException, FastAPI
from sqlalchemy.orm import Session
import json
from .. import oauth2, database

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_ids: Dict[WebSocket, Tuple[str, str]] = {}
        self.groups: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, location_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.user_ids[websocket] = (user_id, location_id)
        await self.broadcast_user_list()
        await self.broadcast_user_count()

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            del self.user_ids[websocket]
            await self.broadcast_user_list()
            await self.broadcast_user_count()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def send_user_list(self, websocket: WebSocket):
        users = [f"{user_id}@{location_id}" for user_id, location_id in self.user_ids.values()]
        message = json.dumps({
            "type": "user_list",
            "users": users
        })
        await self.send_personal_message(message, websocket)

    async def broadcast_user_list(self):
        users = [f"{user_id}@{location_id}" for user_id, location_id in self.user_ids.values()]
        message = json.dumps({
            "type": "user_list",
            "users": users
        })
        await self.broadcast(message)

    async def broadcast_user_count(self):
        user_count = len(self.user_ids)
        message = json.dumps({
            "type": "user_count",
            "count": user_count
        })
        await self.broadcast(message)

    async def add_to_group(self, group_name: str, websocket: WebSocket):
        if group_name not in self.groups:
            self.groups[group_name] = []
        self.groups[group_name].append(websocket)

    async def remove_from_group(self, group_name: str, websocket: WebSocket):
        if group_name in self.groups:
            self.groups[group_name].remove(websocket)
            if not self.groups[group_name]:
                del self.groups[group_name]

    async def broadcast_to_group(self, group_name: str, message: str):
        if group_name in self.groups:
            for connection in self.groups[group_name]:
                await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(database.get_db)):
    token = websocket.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        await websocket.close(code=1008)
        return

    token = token.split(" ")[1]
    try:
        current_user = oauth2.get_current_user(token, db)
        user_id = current_user.user_id
        location_id = current_user.location_id
        await manager.connect(websocket, user_id, location_id)
    except HTTPException as e:
        await websocket.close(code=1008)
        return

    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("request_user_list"):
                await manager.send_user_list(websocket)
            elif data.startswith("pm:"):
                _, recipient_user_id, message = data.split(":", 2)
                recipient_ws = None
                for ws, (uid, loc_id) in manager.user_ids.items():
                    if uid == recipient_user_id:
                        recipient_ws = ws
                        break
                if recipient_ws:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "personal_message",
                            "sender": user_id,
                            "message": message
                        }), recipient_ws)
                else:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": f"User {recipient_user_id} not found"
                        }), websocket)
            elif data.startswith("group:"):
                _, group_name, message = data.split(":", 2)
                await manager.broadcast_to_group(group_name, json.dumps({
                    "type": "group_message",
                    "group": group_name,
                    "sender": user_id,
                    "message": message
                }))
            elif data.startswith("join_group:"):
                _, group_name = data.split(":", 1)
                await manager.add_to_group(group_name, websocket)
                await manager.send_personal_message(
                    json.dumps({
                        "type": "info",
                        "message": f"Joined group {group_name}"
                    }), websocket)
            elif data.startswith("leave_group:"):
                _, group_name = data.split(":", 1)
                await manager.remove_from_group(group_name, websocket)
                await manager.send_personal_message(
                    json.dumps({
                        "type": "info",
                        "message": f"Left group {group_name}"
                    }), websocket)
            else:
                await manager.broadcast(json.dumps({
                    "type": "broadcast",
                    "sender": user_id,
                    "message": data
                }))
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        print(f"Client {user_id} disconnected")
    except WebSocketException as e:
        print(f"Error occurred with client {user_id}: {e}")
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"Unexpected error: {e}")
        await manager.disconnect(websocket)
