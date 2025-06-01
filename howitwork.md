 # How It Works

 This document outlines the key components and flow of the live-shader injection system.

 ## 1. Landing Page (index.html)
 - On load, index.html fetches:
   - config.json (default_shader and values)
   - default shader HTML (fire2.html or template.html)
 - Replaces location.hostname references
 - Injects JS variables for each value in config.json before the marker comment
 - Embeds modified HTML via iframe srcdoc

 ## 2. Shader Client (e.g. fire2.html)
 - Imports p5.js
 - Defines shaders in script tags
 - Contains a script that:
   1. Declares globals and contains an injection marker
   2. setup(): compiles shader from DOM, sets uniforms from injected vars, opens WebSocket
   3. WebSocket onmessage: parses type and value, updates uniforms and local vars, updates color picker
   4. draw(): each frame sets uniforms from current state and renders a full-screen quad

 ## 3. WebSocket Messaging
 - ws_server.py listens on port 8765 and relays messages to clients
 - streamlit_app.py publishes JSON messages of the form
     { type: uniformName, value: newValue }
   for slider and color picker updates

 ## 4. Generic Template (template.html and template.json)
 - template.html is a minimal p5.js shader wrapper with uniforms u_radius, u_color, u_resolution
 - template.json defines the control schema for those uniforms:
   name, label, widget, type, default, min, max, step, etc.
 - To create a new shader:
   1. Copy template.html to myShader.html and adjust GLSL code and uniforms
   2. Copy template.json to myShader.json and adjust the controls schema
   3. On the Pi (or remote device), update config.json:
      default_shader: myShader.html
      values: provide default values matching myShader.json entries
   4. Point index.html (or kiosk) at the landing page; it will inject defaults and live-update uniforms

## 5. Streamlit UI Agent (streamlit_app.py)
- Role: Provides a dynamic control panel in Streamlit, publishes uniform updates, and manages default shader selection.
- Features:
  - Dynamically loads and renders `<shader>.html` and its `<shader>.json` control schema.
  - `Show Shader Preview` toggle to embed or fully collapse the shader view via injected CSS.
  - Publishes JSON messages `{ type: uniformName, value: newValue }` over WebSocket to the broker.
  - `Save Default Shader` button:
      - Persists only `default_shader` in `config.json` (no separate `values` block).
      - Writes current control default values back into the matching shader JSON schema file (`<shader>.json`).
      - Broadcasts a special `{ type: "__reload__" }` message to trigger hot-reload on remote clients.
  - Removed the separate “Save Control Values” button; control defaults now live in `<shader>.json` and are loaded by index.html.
  - On Pi landing page (`index.html`), initial uniform defaults are now loaded from the shader’s JSON schema, falling back to `config.json` only if the schema load fails.
  - Remote clients (both `index.html` and standalone demos) listen for `{ type: "__reload__" }` on WebSocket and call `window.location.reload()` to refresh the page and load new defaults.


 -- End of Document