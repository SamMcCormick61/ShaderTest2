import json
import re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import asyncio
import websockets

# The main area (title/description) appears only when 'Show Shader Preview' is checked
# st.title and st.write will be shown in the preview block below

# -- Dynamic file uploads: allow user to override controls schema or shader HTML
json_uploader = None
html_uploader = None

# WebSocket URI input
# Load default from config.json if available
config_path = Path(__file__).parent / "config.json"
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_ws_uri = cfg.get("websocket_uri", "ws://localhost:8765")
else:
    default_ws_uri = "ws://localhost:8765"
websocket_uri = st.sidebar.text_input("WebSocket URI", value=default_ws_uri)

# ----------------------------------------------------------------------
# Optional preview toggle (default OFF)
show_preview = st.sidebar.checkbox("Show Shader Preview", value=False)
# ----------------------------------------------------------------------
# Hide or show the main content area via CSS
if not show_preview:
    # Show only the sidebar and hide all other content
    st.markdown(
        """
        <style>
        /* Hide all direct children of the app container except the sidebar */
        [data-testid="stAppViewContainer"] > *:not([data-testid="stSidebar"]) {
            display: none !important;
        }
        /* Expand the sidebar to full width */
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Show title and description only when preview is enabled
if show_preview:
    st.title("Interactive Shader Demo")
    st.write(
        "This Streamlit app embeds a WebGL shader demo (Three.js & GLSL). "
        "Use sidebar controls or upload files to set parameters."
    )


html_content = None
controls = []
html_files = [
    f.name for f in Path(__file__).parent.glob("*.html")
    if f.name not in ("streamlit_app.py", "index.html")
]
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_shader = cfg.get("default_shader", html_files[0] if html_files else None)
else:
    default_shader = html_files[0] if html_files else None

shader_file = st.sidebar.selectbox("Shader HTML", html_files, index=html_files.index(default_shader) if default_shader in html_files else 0)

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
            fallback = Path(__file__).parent / "controls.json"
            try:
                controls = json.loads(fallback.read_text())
            except Exception as e:
                st.error(f"Failed to load controls.json: {e}")
                controls = []

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
                    val = st.sidebar.slider(label, min_value=ctrl.get("min", 0.0), max_value=ctrl.get("max", 1.0), value=default, step=ctrl.get("step", 0.01))
                elif dtype == "int":
                    val = st.sidebar.slider(label, min_value=int(ctrl.get("min", 0)), max_value=int(ctrl.get("max", 10)), value=int(default), step=1)
                else:
                    val = default
            elif widget_type == "number_input":
                if dtype == "float":
                    val = st.sidebar.number_input(label, min_value=ctrl.get("min", None), max_value=ctrl.get("max", None), value=default, step=ctrl.get("step", None))
                elif dtype == "int":
                    val = st.sidebar.number_input(label, min_value=int(ctrl.get("min", 0)), max_value=int(ctrl.get("max", 10)), value=int(default), step=int(ctrl.get("step", 1)))
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
        except Exception as e:
            st.sidebar.error(f"Error sending WS message: {e}")
            st.session_state.ws_connected = False
            st.session_state.ws_client = None

# Manual reconnect button
if st.sidebar.button("Reconnect WebSocket"):
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
        asyncio.run(send_ws_message(message))

# Save default selection
if st.sidebar.button("Save Default Shader"):
    # Update config.json to point at new default shader
    cfg = {"default_shader": shader_file}
    config_path.write_text(json.dumps(cfg, indent=2))
    st.sidebar.success(f"Saved default shader '{shader_file}' to config.json")

    # Update schema defaults for this shader
    schema_path = Path(__file__).parent / f"{Path(shader_file).stem}.json"
    try:
        for ctrl in controls:
            name = ctrl.get("name")
            if name in values:
                ctrl["default"] = values[name]
        schema_path.write_text(json.dumps(controls, indent=2))
        st.sidebar.success(f"Updated default values in {schema_path.name}")
    except Exception as e:
        st.sidebar.error(f"Failed to update schema {schema_path.name}: {e}")

    # Notify connected clients (including index.html) to reload
    if st.session_state.ws_connected:
        asyncio.run(send_ws_message({"type": "__reload__", "value": ""}))


    
# Render the shader preview (or error) only when 'Show Shader Preview' is checked
if show_preview:
    if html_content:
        for ctrl in controls:
            name = ctrl["name"]
            dtype = ctrl.get("type")
            val = values.get(name)
            val_str = f"{val}.0" if dtype == "int" else f"{val}"
            const_pattern = rf"(const float {name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)"
            html_content = re.sub(
                const_pattern,
                lambda m, val_str=val_str: m.group(1) + val_str + m.group(3),
                html_content
            )
            let_pattern = rf"(let\s+{name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)"
            html_content = re.sub(
                let_pattern,
                lambda m, val_str=val_str: m.group(1) + val_str + m.group(3),
                html_content
            )
        components.html(html_content, height=800, scrolling=True)
    else:
        st.error(f"Could not find shader file: {shader_file}")
