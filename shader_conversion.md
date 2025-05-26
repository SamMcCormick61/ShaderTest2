     # Shader Conversion Guide

        This document outlines how to wrap a raw GLSL fragment
    shader into an interactive HTML + JSON pair with custom
    controls driven over WebSockets.
        Name this file `shader_conversion.md`.

        ## Overview
        1. Create a standalone HTML file that loads your shader
    (e.g. with p5.js or Three.js).
        2. Generate a `controls.json` schema declaring parameters
     (name, type, widget, min/max/default).
        3. Embed a WebSocket server (`ws_server.py`) to broadcast
     control messages.
        4. Add a WebSocket client in the HTML to receive `{type,
    value}` JSON messages and update GLSL uniforms.
        5. Build a Streamlit app (`streamlit_app.py`) that reads
    `controls.json`, renders sidebar widgets, and publishes
    messages to the WS server.
        6. Incrementally add new controls: edit `controls.json`,
    verify via WebSocket logs, observe live shader updates.

        ## Prerequisites
        - Python 3.7+ with:
          ```bash
          pip install websockets streamlit

        * p5.js (or Three.js) in the browser.
        * Basic familiarity with GLSL, JavaScript, and Python.

    -------------------------------------------------------------
    ---

    ## 1. Basic HTML Shader Wrapper

    Create shader.html:

        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><title>My
    Shader</title></head>
        <body>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.
    js/1.7.0/p5.min.js"></script>
          <script id="frag" type="x-shader/x-fragment">
          // your GLSL code here
          void main() { gl_FragColor = vec4(1.0); }
          </script>
          <script>
          let myShader;
          function setup() {
            createCanvas(windowWidth, windowHeight, WEBGL);
            const fs =
    document.getElementById('frag').textContent;
            myShader = createShader(`
              void main() {
                gl_Position = projectionMatrix * modelViewMatrix
    * vec4(position, 1.0);
              }`, fs);
          }
          function draw() {
            shader(myShader);
            quad(-1,-1,1,-1,1,1,-1,1);
          }
          </script>
        </body>
        </html>

    Serve it:

        cd /path/to/dir
        python3 -m http.server 8000
        # open http://localhost:8000/shader.html

    -------------------------------------------------------------
    ---

    ## 2. Create controls.json

    Start with no controls:

        []

    After first pass add one control:

        [
          {
            "name": "fireHeight",
            "label": "Fire Height",
            "widget": "slider",
            "type": "float",
            "min": 0.1,
            "max": 5.0,
            "step": 0.1,
            "default": 1.0
          }
        ]

    -------------------------------------------------------------
    ---

    ## 3. WebSocket Broker (ws_server.py)

        import asyncio, json, websockets

        clients = set()

        async def handler(ws, path):
            clients.add(ws)
            print("Client connected:", ws.remote_address)
            try:
                async for msg in ws:
                    print("Received:", msg)
                    for c in clients:
                        if c.open:
                            await c.send(msg)
                            print("Broadcasted to",
    c.remote_address)
            finally:
                clients.remove(ws)
                print("Client disconnected:", ws.remote_address)

        async def main():
            async with websockets.serve(handler, "0.0.0.0",
    8765):
                await asyncio.Future()  # run forever

        if __name__=="__main__":
            asyncio.run(main())

    Run:

        python3 ws_server.py

    -------------------------------------------------------------
    ---

    ## 4. Add WebSocket Client to HTML

    In your HTML <script> section:

        const socket = new WebSocket("ws://" + location.hostname
    + ":8765");
        socket.onopen = () => console.log("WS connected to",
    socket.url);
        socket.onmessage = e => {
          console.log("WS msg:", e.data);
          const { type, value } = JSON.parse(e.data);
          myShader.setUniform("u_" + type, value);
        };

    Make sure your draw() loop pushes those uniforms each frame:

        function draw() {
          myShader.setUniform("u_fireHeight", fireHeight);
          // ... other uniforms ...
          shader(myShader);
          quad(-1,-1,1,-1,1,1,-1,1);
        }

    -------------------------------------------------------------
    ---

    ## 5. Streamlit Control Panel (streamlit_app.py)

        import json, asyncio, websockets, streamlit as st
        from pathlib import Path

        st.sidebar.header("Shader Controls")
        controls = json.loads(Path("controls.json").read_text())
        values = {}

        for ctrl in controls:
            name, label = ctrl["name"], ctrl["label"]
            if ctrl["widget"] == "slider":
                values[name] = st.sidebar.slider(label,
                    ctrl["min"], ctrl["max"], ctrl["default"],
    ctrl["step"])
            elif ctrl["widget"] == "color_picker":
                values[name] = st.sidebar.color_picker(label,
    ctrl["default"])

        ws_uri = st.sidebar.text_input("WebSocket URI",
    "ws://localhost:8765")

        async def publish():
            async with websockets.connect(ws_uri) as ws:
                for k, v in values.items():
                    msg = json.dumps({"type": k, "value": v})
                    print("Publishing:", msg)
                    await ws.send(msg)

        if st.sidebar.button("Send updates"):
            asyncio.run(publish())

    Install & run:

        pip install -r requirements.txt
        streamlit run streamlit_app.py --server.address 0.0.0.0
        # browse to http://<your-pi-ip>:8501

    -------------------------------------------------------------
    ---

    ## 6. Incremental Control Addition

        1. Start with **no** controls: verify HTML renders
    normally.
        2. Add one JSON entry (`fireHeight`), reload Streamlit,
    click **Send updates** → check WS server logs.
        3. Reload your shader page → observe flame height change.

        4. Repeat for `centerPower`, `noiseScale`, `baseColor`.

    -------------------------------------------------------------
    ---

    ## 7. Useful Prompts

        * “Wrap my fragment shader in a p5.js HTML template.”
        * “Add WebSocket support to this HTML to update GLSL
    uniforms.”
        * “Generate a controls.json schema with sliders for
    [fireHeight, noiseScale].”
        * “Write a Streamlit app that reads controls.json and
    pushes updates over WebSocket.”

    -------------------------------------------------------------
    ---

    ## 8. Debugging Tips

        * Open browser DevTools → Console for incoming WS logs.
        * Print statements in `ws_server.py` for introspection.
        * Use grayscale debug in GLSL (`gl_FragColor =
    vec4(vec3(x),1.0)`) to isolate behavior.
        * Temporarily amplify uniform values in GLSL to validate
    (e.g., multiply height by 5×).

    -------------------------------------------------------------
    ---

    This guide provides a repeatable workflow to turn any GLSL
    shader into a live, remotely‐controlled web demo. Enjoy
    experimenting!