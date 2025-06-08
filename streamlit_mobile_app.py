import json
import asyncio
from pathlib import Path

import streamlit as st
import websockets

# Load default WebSocket URI from config.json
base_dir = Path(__file__).parent
config_path = base_dir / "config.json"
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_ws_uri = cfg.get("websocket_uri", "ws://localhost:8765")
else:
    default_ws_uri = "ws://localhost:8765"
websocket_uri = st.text_input("WebSocket URI", value=default_ws_uri)

# Select shader HTML file
shader_dir = base_dir / "shaders"
html_files = [str(f.relative_to(base_dir)) for f in shader_dir.glob("*.html")]
if not html_files:
    st.error("No shader HTML files found in shaders/ directory.")
    st.stop()
if config_path.exists():
    default_shader = cfg.get("default_shader", html_files[0])
else:
    default_shader = html_files[0]
shader_file = st.selectbox(
    "Shader HTML",
    html_files,
    index=html_files.index(default_shader) if default_shader in html_files else 0,
)

# Load controls schema for selected shader
schema_path = base_dir / Path(shader_file).with_suffix(".json")
try:
    controls = json.loads(schema_path.read_text())
except Exception as e:
    st.error(f"Failed to load controls schema {schema_path.name}: {e}")
    controls = []

# Display shader controls
st.header("Shader Controls")
values = {}
for ctrl in controls:
    name = ctrl.get("name")
    label = ctrl.get("label", name)
    widget_type = ctrl.get("widget")
    dtype = ctrl.get("type")
    default = ctrl.get("default")

    if widget_type == "slider":
        if dtype == "float":
            val = st.slider(label,
                            min_value=ctrl.get("min", 0.0),
                            max_value=ctrl.get("max", 1.0),
                            value=default,
                            step=ctrl.get("step", 0.01))
        elif dtype == "int":
            val = st.slider(label,
                            min_value=int(ctrl.get("min", 0)),
                            max_value=int(ctrl.get("max", 10)),
                            value=int(default),
                            step=1)
        else:
            val = default
    elif widget_type == "number_input":
        if dtype == "float":
            val = st.number_input(label,
                                   min_value=ctrl.get("min", None),
                                   max_value=ctrl.get("max", None),
                                   value=default,
                                   step=ctrl.get("step", None))
        elif dtype == "int":
            val = st.number_input(label,
                                   min_value=int(ctrl.get("min", 0)),
                                   max_value=int(ctrl.get("max", 10)),
                                   value=int(default),
                                   step=int(ctrl.get("step", 1)))
        else:
            val = default
    elif widget_type == "selectbox":
        options = ctrl.get("options", []) or []
        try:
            idx = options.index(default)
        except (ValueError, TypeError):
            idx = 0
        val = st.selectbox(label, options, index=idx)
    elif widget_type == "multiselect":
        options = ctrl.get("options", []) or []
        val = st.multiselect(label, options, default=ctrl.get("default", []))
    elif widget_type == "text_input":
        val = st.text_input(label, value=str(default) if default is not None else "")
    elif widget_type == "color_picker":
        val = st.color_picker(label, value=default if isinstance(default, str) else None)
    else:
        val = default

    values[name] = val

# WebSocket client state
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False
if "ws_client" not in st.session_state:
    st.session_state.ws_client = None

async def connect_ws(uri):
    try:
        st.session_state.ws_client = await websockets.connect(uri)
        st.session_state.ws_connected = True
        st.success(f"Connected to WebSocket: {uri}")
    except Exception as e:
        st.session_state.ws_connected = False
        st.session_state.ws_client = None
        st.error(f"Failed to connect to WebSocket: {e}")

async def send_ws_message(message):
    if st.session_state.ws_connected and st.session_state.ws_client:
        try:
            await st.session_state.ws_client.send(json.dumps(message))
        except Exception as e:
            st.error(f"Error sending WS message: {e}")
            st.session_state.ws_connected = False
            st.session_state.ws_client = None

# Connect to WebSocket if not already connected
if not st.session_state.ws_connected:
    asyncio.run(connect_ws(websocket_uri))

# Manual reconnect button
if st.button("Reconnect WebSocket"):
    st.session_state.ws_connected = False
    st.session_state.ws_client = None
    asyncio.run(connect_ws(websocket_uri))

## Send all control values over WebSocket
if st.session_state.ws_connected:
    for name, val in values.items():
        message = {"type": name, "value": val}
        asyncio.run(send_ws_message(message))

# Save default shader selection and control defaults
if st.button("Save Default Shader"):
    # Update config.json with new default shader
    try:
        # Persist the selected default shader
        cfg = {"default_shader": shader_file}
        config_path.write_text(json.dumps(cfg, indent=2))
        st.success(f"Saved default shader '{shader_file}' to config.json")
    except Exception as e:
        st.error(f"Failed to update config.json: {e}")
    # Update schema defaults for this shader
    schema_path = base_dir / Path(shader_file).with_suffix('.json')
    try:
        for ctrl in controls:
            name = ctrl.get("name")
            if name in values:
                ctrl["default"] = values[name]
        schema_path.write_text(json.dumps(controls, indent=2))
        st.success(f"Updated default control values in {schema_path.name}")
    except Exception as e:
        st.error(f"Failed to update schema {schema_path.name}: {e}")
    # Notify any connected clients to reload
    if st.session_state.ws_connected:
        asyncio.run(send_ws_message({"type": "__reload__", "value": ""}))