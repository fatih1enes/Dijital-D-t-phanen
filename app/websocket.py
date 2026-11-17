"""WebSocket connection manager."""

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections with connection limit."""

    MAX_CONNECTIONS = 50

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept and store WebSocket connection. Returns False if limit reached."""
        if len(self.active_connections) >= self.MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Max connections reached")
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        try:
            self.active_connections.remove(websocket)
        except ValueError as e:
            import logging

            logging.debug("WebSocket connection already removed: %s", e)

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connections concurrently with per-socket timeout protection."""
        connections = list(self.active_connections)
        if not connections:
            return

        tasks = [
            asyncio.wait_for(conn.send_json(message), timeout=3.0)
            for conn in connections
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for conn, result in zip(connections, results, strict=True):
            if isinstance(result, Exception):
                self.disconnect(conn)
