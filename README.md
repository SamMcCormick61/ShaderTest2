 # Shader Demo
 
 This project demonstrates an interactive WebGL shader demo (Three.js & GLSL) embedded in a Streamlit app.
 
# Files
- `shad1.py`: Pygame + ModernGL (OpenGL) standalone flame shader demo.
- `fractal.html`: HTML + Three.js shader demo used by the Streamlit app.
- `streamlit_app.py`: Streamlit app embedding `fractal.html`.
- `requirements.txt`: Project dependencies.
 
# Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Launch the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```
  
# Deployment
For cloud deployment (e.g. Streamlit Cloud or Heroku), ensure you launch the Streamlit app instead of the Pyglet demo:
1. Add a `Procfile` at the project root with:
   ```text
   web: streamlit run streamlit_app.py --server.port $PORT --server.headless true
   ```
2. Push your repo to your cloud platform; it will run the Streamlit app as the web process.

## Converting an Existing Shader to Dynamic Upload Format

When you have a raw GLSL (Three.js) or p5.js shader that you’d like to plug into this app, use the following prompt template with Codex-CLI to generate a self-contained HTML and matching `controls.json` schema:

```text
Hi Codex-CLI!
I have a shader (attach your .frag/.vert, or include the code below).
Please:

1. Extract all `uniform` and `const float` (or `#define`) parameters.
2. For each parameter, propose:
   - A human-friendly name & label
   - A Streamlit widget type (e.g., slider, color_picker, number_input, selectbox)
   - Reasonable default, min, max, and step (for numeric), or options list (for selects).
3. Ask me to confirm which parameters to expose externally; leave the rest as internal (but document them in a sidebar legend).
4. Generate:
   a) `controls.json` with only the externally exposed parameters.
   b) A self-contained `shader.html` (or `p5.html`) that:
      - Inlines your vertex and fragment GLSL (or `<script type="x-shader">` tags)
      - Loads the schema & HTML via Streamlit’s file_uploader fallback
      - Injects external values into shader constants or JS `let` defaults
      - Renders the shader in a canvas using Three.js (or p5.js)
      - Displays a sidebar legend of “Internal Controls” (e.g., Time, Resolution, Mouse X/Y)
      - Integrates with the existing `streamlit_app.py` logic for uploads & injection

Please walk me through the mapping of uniforms → widgets, let me confirm, then output the final `controls.json` and `shader.html` files.
```
## Raspberry Pi Video Wall Setup

To run the shader on a Raspberry Pi driving a video wall at 1028×1088 resolution:

1. **Configure custom HDMI resolution**  
   Edit `/boot/config.txt` on the Pi:
   ```text
   hdmi_force_hotplug=1
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=1028 1088 60 6 0 0 0
   ```
   Then reboot the Pi.

2. **Serve the display HTML**  
   From the project root on the Pi:
   ```bash
   python3 -m http.server 8000
   ```

3. **Start the WebSocket server**  
   In a separate terminal:
   ```bash
   python3 ws_server.py
   ```

4. **Launch in kiosk mode**  
   Use Chromium in kiosk mode:
   ```bash
   DISPLAY=:0 chromium-browser --kiosk --window-size=1028,1088 http://localhost:8000/waterfall.html
   ```
   (Replace with `fractal.html` if desired.)

5. **Control via WebSocket**  
- On your phone or remote machine, start the Streamlit app:
  ```bash
  streamlit run streamlit_app.py --server.address=0.0.0.0
  ```
- In the Streamlit sidebar, set the **WebSocket URI** to `ws://<pi-ip>:8765`.
- Adjust shader controls; updates will stream to the Pi display in real time.