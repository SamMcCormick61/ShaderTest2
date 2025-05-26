 # ShaderTest2 Setup Instructions

 This document guides you through setting up and running the ShaderTest2 project both locally and on a Raspberry Pi driving a video wall at 1028×1088 resolution.

 ## Prerequisites
 - Python 3.7+ (3.9 recommended)
 - git
 - On Pi: Raspberry Pi 4, HDMI cable, video wall panel supporting 1028×1088

 ## 1. Local Development
 1. **Clone the repository**
    ```bash
    git clone <your-repo-url> ShaderTest2
    cd ShaderTest2
    ```
 2. **(Optional) Create a virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
 3. **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```
 4. **Start the WebSocket server**
    ```bash
    python3 ws_server.py
    ```
 5. **Launch the Streamlit app**
    ```bash
    streamlit run streamlit_app.py
    ```
    Open http://localhost:8501 in your browser.
 6. **Run the standalone OpenGL shader demo** (optional)
    ```bash
    pip install pygame-ce moderngl numpy
    python3 shad1.py
    ```

 ## 2. Raspberry Pi Video Wall Setup
 To display the shader on a video wall at 1028×1088 on a Pi:

 1. **Configure custom HDMI resolution**
    Edit `/boot/config.txt` (requires `sudo`) and add:
    ```text
    hdmi_force_hotplug=1
    hdmi_group=2
    hdmi_mode=87
    hdmi_cvt=1028 1088 60 6 0 0 0
    ```
    Then reboot the Pi:
    ```bash
    sudo reboot
    ```

 2. **(Optional) Create and activate a Python virtual environment**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

 3. **Serve HTML files**
    ```bash
    cd ShaderTest2
    python3 -m http.server 8000
    ```

 4. **Start the WebSocket server**
    In another terminal:
    ```bash
    python3 ws_server.py
    ```

 5. **Launch in kiosk mode**
    ```bash
    DISPLAY=:0 chromium-browser --kiosk --window-size=1028,1088 http://localhost:8000/fire2.html
    ```
    (or replace `waterfall.html` with `fractal.html`)

 6. **Control via WebSocket**
    - On a remote machine (e.g., your phone or laptop), run the Streamlit app:
      ```bash
      streamlit run streamlit_app.py --server.address=0.0.0.0

    - In the Streamlit sidebar, set **WebSocket URI** to `ws://<pi-ip>:8765`
    - Adjust controls; updates will stream live to the Pi display.




    what does -server.address do in streamlit run streamlit_app.py --server.address 0.0.0.0

    codex
    The --server.address flag tells Streamlit which network interface to bind its HTTP server to.

    By default Streamlit will bind to localhost (i.e. 127.0.0.1), which means only processes on the same machine can connect. If you want to be able to open
    the Streamlit UI from another device on your LAN (e.g. your phone, laptop, etc.), you need to bind to an interface that’s reachable externally—most
    commonly 0.0.0.0, which means “all interfaces.”

    So:

    • streamlit run streamlit_app.py
      → listens on localhost:8501 only

    • streamlit run streamlit_app.py --server.address 0.0.0.0
      → listens on 0.0.0.0:8501, i.e. all network interfaces, so you can point your browser at http://<pi-ip-address>:8501

    You can also override the port with --server.port 1234 if you need a different one.