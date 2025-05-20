import json
import re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.title("Interactive Shader Demo")
st.write("This Streamlit app embeds a WebGL shader demo (Three.js & GLSL). Use sidebar controls or upload files to set parameters.")
# -- Dynamic file uploads: allow user to override controls schema or shader HTML
st.sidebar.header("Upload Shader Files")
json_uploader = st.sidebar.file_uploader("Upload controls.json", type=["json"])
html_uploader = st.sidebar.file_uploader("Upload fractal.html", type=["html", "htm"])

"""
Load & embed the fractal.html demo, injecting parameters via controls.json.
"""
# Load control definitions from upload or local fallback
if json_uploader is not None:
    try:
        raw = json_uploader.getvalue().decode('utf-8')
        controls = json.loads(raw)
    except Exception as e:
        st.error(f"Failed to parse uploaded controls.json: {e}")
        controls = []
else:
    config_path = Path(__file__).parent / "controls.json"
    try:
        controls = json.loads(config_path.read_text())
    except Exception as e:
        st.error(f"Failed to load controls.json: {e}")
        controls = []

# Create sidebar widgets dynamically
st.sidebar.header("Shader Controls")
values = {}
for ctrl in controls:
    name = ctrl["name"]
    label = ctrl.get("label", name)
    widget = ctrl.get("widget")
    dtype = ctrl.get("type")
    default = ctrl.get("default")
    # Slider widget
    if widget == "slider":
        if dtype == "float":
            val = st.sidebar.slider(
                label,
                min_value=ctrl.get("min", 0.0),
                max_value=ctrl.get("max", 1.0),
                value=default,
                step=ctrl.get("step", 0.01)
            )
        elif dtype == "int":
            val = st.sidebar.slider(
                label,
                min_value=int(ctrl.get("min", 0)),
                max_value=int(ctrl.get("max", 10)),
                value=int(default),
                step=1
            )
        else:
            val = default
    # Number input widget
    elif widget == "number_input":
        if dtype == "float":
            val = st.sidebar.number_input(
                label,
                min_value=ctrl.get("min", None),
                max_value=ctrl.get("max", None),
                value=default,
                step=ctrl.get("step", None)
            )
        elif dtype == "int":
            val = st.sidebar.number_input(
                label,
                min_value=int(ctrl.get("min", 0)),
                max_value=int(ctrl.get("max", 10)),
                value=int(default),
                step=int(ctrl.get("step", 1))
            )
        else:
            val = default
    # Select box widget
    elif widget == "selectbox":
        options = ctrl.get("options", []) or []
        try:
            index = options.index(default)
        except (ValueError, TypeError):
            index = 0
        val = st.sidebar.selectbox(label, options, index=index)
    # Multiselect widget
    elif widget == "multiselect":
        options = ctrl.get("options", []) or []
        val = st.sidebar.multiselect(label, options, default=ctrl.get("default", []))
    # Text input widget
    elif widget == "text_input":
        val = st.sidebar.text_input(label, value=str(default) if default is not None else "")
    # Color picker widget
    elif widget == "color_picker":
        val = st.sidebar.color_picker(label, value=default if isinstance(default, str) else None)
    # Fallback to default value
    else:
        val = default
    values[name] = val

# Read and inject parameters into HTML (uploaded or local)
html_content = None
if html_uploader is not None:
    try:
        html_content = html_uploader.getvalue().decode('utf-8')
    except Exception as e:
        st.error(f"Failed to read uploaded HTML: {e}")
        html_content = None
else:
    html_path = Path(__file__).parent / "fractal.html"
    if html_path.exists():
        html_content = html_path.read_text()

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