import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.title("Interactive Shader Demo V3")
st.write("This Streamlit app embeds a WebGL shader demo (Three.js & GLSL). Use sidebar controls or upload files to set parameters.")

# -- Dynamic file uploads: allow override controls schema or shader HTML
st.sidebar.header("Upload Shader Files")
json_uploader = st.sidebar.file_uploader("Upload controls.json", type=["json"])
html_uploader = st.sidebar.file_uploader("Upload fractal.html", type=["html", "htm"])

# Read & embed parameters into HTML (uploaded or local)
html_content = None

# Shader HTML selection
html_files = [
    f.name
    for f in Path(__file__).parent.glob("*.html")
    if f.name not in ("streamlit_app.py", "index.html")
]
config_path = Path(__file__).parent / "config.json"
if config_path.exists():
    cfg = json.loads(config_path.read_text())
    default_shader = cfg.get("default_shader", html_files[0] if html_files else None)
else:
    default_shader = html_files[0] if html_files else None

shader_file = st.sidebar.selectbox(
    "Shader HTML",
    html_files,
    index=html_files.index(default_shader) if default_shader in html_files else 0,
)

# Allow uploading a custom HTML override
if html_uploader is not None:
    try:
        html_content = html_uploader.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Failed to read uploaded HTML: {e}")
        html_content = None
else:
    html_path = Path(__file__).parent / shader_file
    if html_path.exists():
        html_content = html_path.read_text()

# Load per-shader control schema (e.g. fire2.json or waterfall.json)
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
            idx = options.index(default)
        except (ValueError, TypeError):
            idx = 0
        val = st.sidebar.selectbox(label, options, idx)

    elif widget_type == "multiselect":
        options = ctrl.get("options", []) or []
        val = st.sidebar.multiselect(label, options, default=ctrl.get("default", []))

    elif widget_type == "text_input":
        val = st.sidebar.text_input(label, str(default) if default is not None else "")

    elif widget_type == "color_picker":
        val = st.sidebar.color_picker(label, default if isinstance(default, str) else None)

    else:
        val = default

    values[name] = val

# WebSocket URI for remote display (optional)
ws_uri = st.sidebar.text_input("WebSocket URI", "ws://localhost:8765")
try:
    import asyncio, websockets

    async def publish():
        async with websockets.connect(ws_uri) as ws:
            for n, v in values.items():
                data = {"type": n, "value": v}
                await ws.send(json.dumps(data))

    asyncio.run(publish())
except Exception as e:
    st.sidebar.warning(f"WebSocket publish failed: {e}")

# Save default shader selection
if st.sidebar.button("Save Default Shader"):
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}
    cfg["default_shader"] = shader_file
    cfg.setdefault("values", values)
    config_path.write_text(json.dumps(cfg, indent=2))
    st.sidebar.success(f"Saved default shader '{shader_file}' to config.json")

# Save current control values + selected shader
if st.sidebar.button("Save Control Values"):
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
        except Exception:
            cfg = {}
    else:
        cfg = {}
    cfg["values"] = values
    cfg["default_shader"] = shader_file
    config_path.write_text(json.dumps(cfg, indent=2))
    st.sidebar.success("Saved control values to config.json")

# Inject control values into the HTML and render
if html_content:
    for ctrl in controls:
        name = ctrl["name"]
        dtype = ctrl.get("type")
        val = values.get(name)
        val_str = f"{val}.0" if dtype == "int" else f"{val}"
        html_content = re.sub(
            rf"(const float {name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)",
            lambda m: m.group(1) + val_str + m.group(3),
            html_content,
        )
        html_content = re.sub(
            rf"(let\s+{name}\s*=\s*)([-+]?[0-9]*\.?[0-9]+)(\s*;)",
            lambda m: m.group(1) + val_str + m.group(3),
            html_content,
        )
    components.html(html_content, height=800, scrolling=True)
else:
    st.error("Could not find or read the selected shader HTML.")