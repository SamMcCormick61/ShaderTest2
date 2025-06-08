This is a journal file i will get codex to updaste this fiel with it progress descripbieng what it has been doing

Request from sam
ok so what iwant to do next is to move the shader files i to thier own folder off the main folder, san we call this
folder shaders and move the fire2, waterfall,template, fractal shader html and json  to this folder we need to adjust
the code to refere to this folder
  
## 2025-06-07 Progress
- Created a new `shaders/` directory and moved the following files into it:
  - fire2.html, fire2.json
  - fractal.html, fractal.json
  - template.html, template.json
  - waterfall.html, waterfall.json
- Updated `config.json` to set `default_shader` to `shaders/fire2.html`.
- Refactored `streamlit_app.py`:
  - Changed shader discovery to read from `shaders/` subfolder.
  - Updated paths for loading and saving JSON schema files in the new folder.
- Adjusted `ws_server.py` handler signature to `async def handler(websocket, path=None):` for compatibility with the current `websockets` API.
- Verified that all Python files compile without errors and that the Streamlit app will correctly reference the relocated shaders.
- Fixed ws_server.py to remove the use of the non-existent `client.open` attribute; now catches send exceptions and discards disconnected clients to prevent crashes when reconnecting.
- Added a new shader conversion for "Sunset":
  - shaders/sunset.json: control schema exposing all adjustable parameters (brightness, color base, vector components, wave settings, etc.).
  - shaders/sunset.html: Three.js wrapper inlining the converted GLSL as a `mainImage` function, defining uniforms for each control, and wiring a WebSocket client for live updates.
  - Updated shader HTML wrappers (e.g., generated from Shadertoy or vertex/fragment files) to determine the WebSocket server host dynamically using `window.parent.location.hostname` instead of hard-coding `localhost`. Ensure this pattern is applied to all future shader conversions.

## 2025-06-08 Progress
- Added a new mobile-focused Streamlit application (`streamlit_mobile_app.py`) that exposes only JSON-based shader controls without any preview.
- Rendered all controls directly in the main view (no sidebar CSS hacks or preview toggle) using standard Streamlit widgets.
- Implemented WebSocket client logic with automatic connection and a manual reconnect button to send control updates to the shader server.
- Retained the original `streamlit_app.py` for desktop users with shader preview functionality.
- Documented usage: launch via `streamlit run streamlit_mobile_app.py`.
- Added a new "Sine Wave" shader:
  - `shaders/sinewave1.json`: control schema defining sliders for speed, height, orientation (horizontal/vertical), line width, blur, and a color picker.
  - `shaders/sinewave1.html`: Three.js wrapper rendering a sinusoidal line based on these parameters and wiring a WebSocket client for live updates.

## 2025-06-09 Progress
- Updated `shaders/sinewave1.html`:
  - Integrated GLSL snippet using `Line` and `mainImage` functions to render multiple sine waves.
  - Added `wavesCount` uniform controlling number of sine waves.
  - Removed previous per-wave uniforms (speed, height, vertical, lineWidth, blur, color).
  - WebSocket handler now listens for `wavesCount` messages.
- Updated `shaders/sinewave1.json`:
  - Added slider control for `wavesCount` (min=1, max=20, default=6).
- Verified shader loops correctly render the specified number of waves.
- Removed unused JSON controls (speed, height, vertical, lineWidth, blur, color) from `shaders/sinewave1.json` to align with GLSL uniforms.