# from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
# from typing import List, Dict
#
# from .. import oauth2, utils
#
# router = APIRouter()
#
#
# class Location:
#     def __init__(self, country: str, state: str, region: str, group: str, location: str):
#         self.country = country
#         self.state = state
#         self.region = region
#         self.group = group
#         self.location = location
#
#
# class Notification:
#     def __init__(self, data_id: str, message: str, location: Location):
#         self.data_id = data_id
#         self.message = message
#         self.location = location
#
#
# class ConnectionManager:
#     def __init__(self):
#         self.active_connections: List[WebSocket] = []
#         self.user_locations: Dict[str, Location] = {}  # Maps user_id to their Location object
#
#     async def connect(self, websocket: WebSocket, current_user: dict, location_data: str):
#         await websocket.accept()
#         self.active_connections.append(websocket)
#         # Parse location data and store user location
#         location_parts = location_data.split("-")
#         if len(location_parts) == 5:
#             self.user_locations[current_user["id"]] = Location(*location_parts)
#         else:
#             print(f"Invalid location data format for user {current_user['id']}")
#
#     def disconnect(self, websocket: WebSocket):
#         user_id = self.get_user_id(websocket)
#         if user_id:
#             del self.user_locations[user_id]
#         self.active_connections.remove(websocket)
#
#     async def send_personal_message(self, message: str, websocket: WebSocket):
#         await websocket.send_text(message)
#
#     async def broadcast_notification(self, notification: Notification):
#         # Filter connections based on user location hierarchy
#         for connection in self.active_connections:
#             user_id = self.get_user_id(connection)
#             if user_id and self.has_access(notification.location, self.user_locations.get(user_id)):
#                 notification_message = f"Data notification (ID: {notification.data_id}): {notification.message}"
#                 await connection.send_text(notification_message)
#
#     def get_user_id(self, websocket: WebSocket) -> str:
#         return getattr(websocket, "user_id", None)
#
#     def has_access(self, target_location: Location, user_location: Location):
#         if not user_location:
#             return False
#         return (
#                 target_location.country == user_location.country
#                 and target_location.state == user_location.state
#                 and target_location.region == user_location.region
#                 and target_location.group == user_location.group
#                 and target_location.location == user_location.location
#         )
#
#
# manager = ConnectionManager()
#
#
# @router.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, current_user: str = Depends(oauth2.get_current_user)):
#     user_id = current_user.id
#     location_data = websocket.query_params.get("location")  # Get location data from query params
#     await manager.connect(websocket, user_id, location_data)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             # Process data with its id (implement your data handling logic here)
#             data_id = "123"  # Placeholder data ID
#             location = manager.user_locations.get(user_id)
#             if location:
#                 # Prepare notification object
#                 notification = Notification(data_id, data, location)
#                 await manager.broadcast_notification(notification)
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)


from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from typing import List

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process data if needed (e.g., extract notification details)
            await manager.send_message(data, websocket)  # Send received data back to the client
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
