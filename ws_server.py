#!/usr/bin/env python3
"""
Simple WebSocket server for broadcasting shader control messages
Usage: python3 ws_server.py
"""
import asyncio
import json
import websockets

clients = set()

async def handler(websocket, path):
    # Register client
    clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast received message to all connected clients
            for client in clients:
                if client.open:
                    await client.send(message)
    finally:
        clients.remove(websocket)

async def main():
    port = 8765
    print(f"Starting WebSocket server on ws://0.0.0.0:{port}")
    # Create and run the WebSocket server indefinitely
    async with websockets.serve(handler, '0.0.0.0', port):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
