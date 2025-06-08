#!/usr/bin/env python3
"""
Simple WebSocket server for broadcasting shader control messages
Usage: python3 ws_server.py
"""
import asyncio
import json
import websockets

clients = set()

async def handler(websocket, path=None):
    # Register client
    client_addr = websocket.remote_address
    print(f"Client connected: {client_addr}")
    clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received message from {client_addr}: {message}")
            for client in list(clients):
                try:
                    await client.send(message)
                    print(f"Broadcasted to {client.remote_address}: {message}")
                except Exception as e:
                    print(f"Error sending to {client.remote_address}: {e}")
                    clients.discard(client)
    except Exception as e:
        print(f"Error with client {client_addr}: {e}")
    finally:
        clients.remove(websocket)
        print(f"Client disconnected: {client_addr}")

async def main():
    port = 8765
    print(f"Starting WebSocket server on ws://0.0.0.0:{port}")
    # Create and run the WebSocket server indefinitely
    async with websockets.serve(handler, '0.0.0.0', port):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
