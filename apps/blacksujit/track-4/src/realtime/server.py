"""WebSocket server for real-time call coaching.

Provides a WebSocket endpoint that clients can connect to for live
coaching during calls. Analyzes speech segments as they arrive and
sends real-time coaching prompts to connected clients.
"""

import asyncio
import json
import time
from typing import Any

from src.realtime.analyzer import RealtimeAnalyzer


class RealtimeCoachingServer:
    """WebSocket server for real-time coaching.

    Clients connect to this server to receive live coaching prompts
    during calls. The server analyzes speech segments as they arrive
    and sends real-time feedback to all connected clients.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.analyzer = RealtimeAnalyzer()
        self.clients: set = set()
        self.is_running = False

    async def start(self):
        """Start the WebSocket server."""
        try:
            import websockets
        except ImportError:
            print("  [ERROR] websockets package required. Install with: pip install websockets")
            return

        self.is_running = True
        print(f"  Real-time coaching server starting on ws://{self.host}:{self.port}")

        async with websockets.serve(self._handle_client, self.host, self.port):
            print(f"  Server running. Waiting for connections...")
            await asyncio.Future()  # Run forever

    async def _handle_client(self, websocket, path):
        """Handle a new client connection."""
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"  Client {client_id} connected. Total clients: {len(self.clients)}")

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "welcome",
                "message": "Connected to CallCoach-AI real-time coaching",
                "timestamp": time.time()
            }))

            # Send current stats
            await websocket.send(json.dumps({
                "type": "stats",
                "data": self.analyzer.get_live_stats()
            }))

            # Handle incoming messages
            async for message in websocket:
                await self._handle_message(websocket, message)

        except Exception as e:
            print(f"  Client {client_id} error: {e}")
        finally:
            self.clients.discard(websocket)
            print(f"  Client {client_id} disconnected. Total clients: {len(self.clients)}")

    async def _handle_message(self, websocket, message: str):
        """Handle an incoming message from a client."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "segment":
                # New speech segment received
                segment = data.get("segment", {})
                result = self.analyzer.add_segment(segment)

                # Broadcast to all clients
                await self._broadcast({
                    "type": "analysis",
                    "data": result
                })

            elif msg_type == "get_stats":
                # Client requesting current stats
                await websocket.send(json.dumps({
                    "type": "stats",
                    "data": self.analyzer.get_live_stats()
                }))

            elif msg_type == "get_summary":
                # Client requesting call summary
                await websocket.send(json.dumps({
                    "type": "summary",
                    "data": self.analyzer.get_summary()
                }))

            elif msg_type == "reset":
                # Reset the analyzer
                self.analyzer = RealtimeAnalyzer()
                await self._broadcast({
                    "type": "reset",
                    "message": "Analyzer reset"
                })

        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))

    async def _broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return

        message_json = json.dumps(message)
        disconnected = set()

        for client in self.clients:
            try:
                await client.send(message_json)
            except Exception:
                disconnected.add(client)

        # Remove disconnected clients
        self.clients -= disconnected

    def add_segment(self, segment: dict[str, Any]) -> dict[str, Any]:
        """Add a speech segment and get analysis (non-WebSocket API)."""
        return self.analyzer.add_segment(segment)

    def get_live_stats(self) -> dict[str, Any]:
        """Get live statistics."""
        return self.analyzer.get_live_stats()

    def get_summary(self) -> dict[str, Any]:
        """Get call summary."""
        return self.analyzer.get_summary()


def create_app():
    """Create a simple HTTP app for the coaching dashboard."""
    from flask import Flask, jsonify, request

    app = Flask(__name__)
    server = RealtimeCoachingServer()

    @app.route("/")
    def index():
        return "CallCoach-AI Real-Time Coaching Server"

    @app.route("/api/stats")
    def stats():
        return jsonify(server.get_live_stats())

    @app.route("/api/summary")
    def summary():
        return jsonify(server.get_summary())

    @app.route("/api/segment", methods=["POST"])
    def add_segment():
        segment = request.json
        result = server.add_segment(segment)
        return jsonify(result)

    return app


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Run HTTP server
        app = create_app()
        app.run(host="localhost", port=5001)
    else:
        # Run WebSocket server
        server = RealtimeCoachingServer()
        asyncio.run(server.start())
