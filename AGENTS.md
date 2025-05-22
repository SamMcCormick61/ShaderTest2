Say Hello Sam i am in the project now

# Agents in ShaderTest2

This document describes the main "agents" (components) that make up the ShaderTest2 system.

## 1. WebSocket Server Agent
- **Script**: `ws_server.py`
- **Role**: Acts as a real-time message broker. Listens on `ws://<host>:8765` and relays parameter updates from the Streamlit UI to connected shader clients (browsers or Pi video wall).

## 2. Streamlit UI Agent
- **Script**: `streamlit_app.py`
- **Role**: Provides a user interface for adjusting shader parameters via sliders, inputs, and color pickers. Runs at `http://localhost:8501` and publishes updates to the WebSocket Server Agent.

## 3. Browser Agent
- **Files**: `waterfall.html`, `fractal.html`, `fire2.html`, etc.
- **Role**: Hosts the WebGL/HTML-based shader demos. Connects to the WebSocket Server Agent to receive live uniform updates and re-renders the shader accordingly.

## 4. Standalone Shader Agent
- **Script**: `shad1.py`
- **Role**: Runs the shader locally using ModernGL and Pygame (outside a browser). Useful for development and testing without a web UI.

## 5. Future/Federated Agents
- **MQTT Broker Agent**: Potential alternative messaging layer for phone ↔ Pi synchronization.
- **Pi Kiosk Launcher Agent**: Shell or Python script to automate launching Chromium in kiosk mode with the correct display settings.
- **Agent Configuration Loader**: Dynamically load control schemas (`controls.json`) and shader templates at runtime.

---

Each agent can be run independently or in concert to achieve a fully interactive, distributed shader demo across devices (desktop, mobile, and Pi-powered video walls).
