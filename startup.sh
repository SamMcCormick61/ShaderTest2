 #!/usr/bin/env bash
        #
        # Reference startup script for ShaderTest2 on Raspberry Pi
        # Place in /home/sam/shadertest2 and make executable: chmod +x startup.sh

        # 0) Change to project directory
        cd /home/sam/shadertest2

        # 1) Activate Python virtual environment if present
        if [ -f .venv/bin/activate ]; then
            source .venv/bin/activate
        elif [ -f venv/bin/activate ]; then
            source venv/bin/activate
        fi

        # 2) Start WebSocket server
        python3 ws_server.py &

        # 3) Start HTTP server on port 8000
        python3 -m http.server 8000 &

        # 4) Start Streamlit control interface
        streamlit run streamlit_app.py --server.address=0.0.0.0 &

        # Give services time to initialize
        sleep 5

        # 5) Launch Chromium in kiosk mode, pointing to the landing page
        DISPLAY=:0 chromium-browser \
          --kiosk \
          --disable-infobars \
          --noerrdialogs \
          --disable-session-crashed-bubble \
          http://localhost:8000/index.html