import sys
import argparse
import subprocess

def run_streamlit_app(port=8050):
    """Launches the Streamlit Sydney Transport Intelligence Platform web application."""
    print(f"\n==================================================")
    print(f" Sydney Transport Intelligence Platform Streamlit App")
    print(f" Launching Streamlit web application on port {port}...")
    print(f"==================================================\n")

    cmd = [
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sydney Transport Foot Traffic Streamlit Platform Launcher")
    parser.add_argument("--port", type=int, default=8050, help="Port to run Streamlit server on")
    args = parser.parse_args()

    run_streamlit_app(port=args.port)
