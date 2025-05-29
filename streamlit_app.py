import json
import re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import asyncio
import websockets

st.title("Interactive Shader Demo")
st.write("This Streamlit app embeds a WebGL shader demo (Three.js & GLSL). Use sidebar controls or upload files to set parameters.")
# -- Dynamic file uploads: allow user to override controls schema or shader HTML
st.sidebar.header("Upload Shader Files")
json_uploader = st.sidebar.file_uploader("Upload controls.json", type=["json"])
html_uploader = st.sidebar.file_uploader("Upload fractal.html", type=["html", "htm"])

# WebSocket URI input
# Load default from config.json if available
config_path = Path(__file__).parent / "config.json" # Redefine config_path here for scope
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_ws_uri = cfg.get("websocket_uri", "ws://localhost:8765")
else:
    default_ws_uri = "ws://localhost:8765"
websocket_uri = st.sidebar.text_input("WebSocket URI", value=default_ws_uri)

"""
Load & embed the fractal.html demo, injecting parameters via controls.json.
"""


# Read and inject parameters into HTML (uploaded or local)
html_content = None
controls = [] # Initialize controls to an empty list
# Shader HTML selection
html_files = [
    f.name
    for f in Path(__file__).parent.glob("*.html")
    if f.name not in ("streamlit_app.py", "index.html")
]
# config_path = Path(__file__).parent / "config.json" # Already defined above
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_shader = cfg.get("default_shader", html_files[0] if html_files else None)
else:
    default_shader = html_files[0] if html_files else None
shader_file = st.sidebar.selectbox("Shader HTML", html_files, index=html_files.index(default_shader) if default_shader in html_files else 0)
# Allow uploading a custom HTML override
if html_uploader is not None:
    try:
        html_content = html_uploader.getvalue().decode('utf-8')
    except Exception as e:
        st.error(f"Failed to read uploaded HTML: {e}")
        html_content = None
else:
    html_path = Path(__file__).parent / shader_file
    if html_path.exists():
        html_content = html_path.read_text()
# Load control schema based on selected shader
        schema_path = Path(__file__).parent / f"{Path(shader_file).stem}.json"
        if json_uploader is not None:
            try:
                raw = json_uploader.getvalue().decode("utf-8")
                controls = json.loads(raw)
            except Exception as e:
                st.error(f"Failed to parse uploaded controls.json: {e}")
                controls = []
        elif schema_path.exists():
            try:
                controls = json.loads(schema_path.read_text())
            except Exception as e:
                st.error(f"Failed to load {schema_path.name}: {e}")
                controls = []
        else:
            # fallback to controls.json
            fallback = Path(__file__).parent / "controls.json"
            try:
                controls = json.loads(fallback.read_text())
            except Exception as e:
                st.error(f"Failed to load controls.json: {e}")
                controls = []

        # Create sidebar widgets dynamically
        st.sidebar.header("Shader Controls")
        values = {}
        for ctrl in controls:
            name = ctrl["name"]
            label = ctrl.get("label", name)
            widget_type = ctrl.get("widget")
            dtype = ctrl.get("type")
            default = ctrl.get("default")

            if widget_type == "slider":
                if dtype == "float":
                    val = st.sidebar.slider(
                        label,
                        min_value=ctrl.get("min", 0.0),
                        max_value=ctrl.get("max", 1.0),
                        value=default,
                        step=ctrl.get("step", 0.01),
                    )
                elif dtype == "int":
                    val = st.sidebar.slider(
                        label,
                        min_value=int(ctrl.get("min", 0)),
                        max_value=int(ctrl.get("max", 10)),
                        value=int(default),
                        step=1,
                    )
                else:
                    val = default
            elif widget_type == "number_input":
                if dtype == "float":
                    val = st.sidebar.number_input(
                        label,
                        min_value=ctrl.get("min", None),
                        max_value=ctrl.get("max", None),
                        value=default,
                        step=ctrl.get("step", None),
                    )
                elif dtype == "int":
                    val = st.sidebar.number_input(
                        label,
                        min_value=int(ctrl.get("min", 0)),
                        max_value=int(ctrl.get("max", 10)),
                        value=int(default),
                        step=int(ctrl.get("step", 1)),
                    )
                    
                else:
                    val = default
            elif widget_type == "selectbox":
                options = ctrl.get("options", []) or []
                try:
                    index = options.index(default)
                except (ValueError, TypeError):
                    index = 0
                val = st.sidebar.selectbox(label, options, index=index)
            elif widget_type == "multiselect":
                options = ctrl.get("options", []) or []
                val = st.sidebar.multiselect(label, options, default=ctrl.get("default", []))
            elif widget_type == "text_input":
                val = st.sidebar.text_input(label, value=str(default) if default is not None else "")
            elif widget_type == "color_picker":
                val = st.sidebar.color_picker(label, value=default if isinstance(default, str) else None)
            else:
                val = default

            values[name] = val

# WebSocket client logic
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False
if "ws_client" not in st.session_state:
    st.session_state.ws_client = None

async def connect_ws(uri):
    try:
        st.session_state.ws_client = await websockets.connect(uri)
        st.session_state.ws_connected = True
        st.sidebar.success(f"Connected to WebSocket: {uri}")
    except Exception as e:
        st.session_state.ws_connected = False
        st.session_state.ws_client = None
        st.sidebar.error(f"Failed to connect to WebSocket: {e}")

async def send_ws_message(message):
    if st.session_state.ws_connected and st.session_state.ws_client:
        try:
            await st.session_state.ws_client.send(json.dumps(message))
            # st.sidebar.info(f"Sent: {message['type']} = {message['value']}") # Too verbose
        except Exception as e:
            st.sidebar.error(f"Error sending WS message: {e}")
            st.session_state.ws_connected = False
            st.session_state.ws_client = None

# Connect to WebSocket if not already connected
if not st.session_state.ws_connected:
    asyncio.run(connect_ws(websocket_uri))

# Send all current values on every rerun (Streamlit's reactive model)
if st.session_state.ws_connected:
    for name, val in values.items():
        if name == "baseColor":
            message = {"type": "baseColor", "value": val}
        else:
            message = {"type": name, "value": val}
        asyncio.run(send_ws_message(message)) # This might block briefly


# Save default selection
if st.sidebar.button("Save Default Shader"):
    # Load existing config.json if present, else start fresh
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}
    cfg["default_shader"] = shader_file
    # Preserve existing values if present; otherwise initialize with current values
    cfg.setdefault("values", values)
    config_path.write_text(json.dumps(cfg, indent=2))
    st.sidebar.success(f"Saved default shader '{shader_file}' to config.json")

# Save current control values
if st.sidebar.button("Save Control Values"):
    # Load existing config.json if present, else start fresh
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}
    cfg["values"] = values
    # Update default_shader to current selection
    cfg["default_shader"] = shader_file
    # Save WebSocket URI
    cfg["websocket_uri"] = websocket_uri
    config_path.write_text(json.dumps(cfg, indent=2))
    st.sidebar.success("Saved control values to config.json")

if html_content:
    # Inject control values into HTML (both GLSL consts and JS let declarations)
    for ctrl in controls:
        name = ctrl["name"]
        dtype = ctrl.get("type")
        # get sidebar value for this control
        val = values.get(name)
        # Format numeric literal: ints get .0 suffix
        val_str = f"{val}.0" if dtype == "int" else f"{val}"
        # 1) Replace GLSL const float definitions
        const_pattern = rf"(const float {name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)"
        # Replace GLSL const and JS let via a callable to avoid backreference ambiguity
        html_content = re.sub(
            const_pattern,
            lambda m, val_str=val_str: m.group(1) + val_str + m.group(3),
            html_content
        )
        # 2) Replace JS let initialization (e.g. let fireHeight = 1.0;)
        let_pattern = rf"(let\s+{name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)"
        html_content = re.sub(
            let_pattern,
            lambda m, val_str=val_str: m.group(1) + val_str + m.group(3),
            html_content
        )
    components.html(html_content, height=800, scrolling=True)
else:
    st.error("Could not find or read 'fractal.html'. Please ensure it exists or upload one.")
