# TODO: Interactive Shader App Enhancements

This document outlines the next steps to extend the Streamlit-based shader demo.

## 1. JSON-Driven Streamlit Controls
Allow adding new UI widgets entirely via the `controls.json` schema.
  - Define a new entry in `controls.json`:
    ```json
    {
      "name": "myParam",
      "label": "My Parameter",
      "widget": "selectbox",   # e.g., slider, selectbox, text_input, color_picker
      "type": "float",         # or "int", "str" depending on widget
      "options": [0.1, 0.5, 1.0], # for selectbox/multiselect
      "min": 0.0,               # for number_input or slider
      "max": 2.0,
      "step": 0.1,
      "default": 0.5
    }
    ```
  - In `streamlit_app.py`, extend the widget factory loop:
    - Map `widget` + `type` to the corresponding Streamlit API (`st.sidebar.slider`,
      `st.sidebar.selectbox`, `st.sidebar.text_input`, `st.sidebar.color_picker`, etc.).
    - Read `options` for dropdowns, parse numeric types for `number_input`,
      use `text_input` for free-form strings.
  - Store returned values in `values[name]` and inject into the shader HTML via regex.

## 2. Dynamic JSON & HTML Upload
Enable end users to upload their own control schemas and shader HTML at runtime.
  - Add two file uploader widgets in the sidebar:
    ```python
    json_uploader = st.sidebar.file_uploader("Upload controls.json", type=["json"])
    html_uploader = st.sidebar.file_uploader("Upload fractal.html", type=["html"])
    ```
  - Loading logic:
    1. If `json_uploader` is provided, parse its content as JSON;
       otherwise fallback to local `controls.json`.
    2. If `html_uploader` is provided, read its text;
       otherwise fallback to local `fractal.html`.
  - Continue to build UI and inject uniforms exactly as before,
    but now using the uploaded files for template and schema.

## 3. Video Wall Synchronization (Phone → Raspberry Pi)
Mirror user interactions and parameter changes from a mobile Streamlit UI to a remote shader instance driving a video wall.
  1. **Refactor Shader to Use Uniforms**
     - Replace hard-coded `const float …` declarations in `fractal.html` with
       `uniform float <name>;` for all adjustable parameters (`uvOffset`,
       `uvFractalScale`, `iterations`, mouse coords, etc.).
  2. **Choose a Messaging Layer** (WebSocket or MQTT):
     - *WebSocket*: Deploy a WS server; both phone app and Pi app connect.
     - *MQTT*: Use a public or private broker; publish/subscriber model.
  3. **Phone-Side Publisher**:
     - In Streamlit or embedded JS, whenever a slider changes or mouse/key event
       fires, send a JSON message: `{"type":"uvOffset","value":0.75}`.
  4. **Pi-Side Subscriber**:
     - Run a small Python or JS client that listens to the same topic/server,
       receives updates, and sets `shader_material.uniforms['uvOffset'].value`
       (and others) before re-rendering.
  5. **Synchronization**:
     - Ensure low-latency and ordered delivery; consider adding sequence numbers
       or a full-state "sync" message when a new client connects.
  6. **Deployment**:
     - Host the broker on the same local network or in the cloud.
     - Launch the Pi in kiosk mode (browser or native GL), connecting to the broker.

With these steps, you'll have a fully dynamic, schema-driven Streamlit UI,
runtime shader uploads, and real-time remote synchronization to your video wall.