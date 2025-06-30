import subprocess
import time
import webbrowser
import requests
import os

SERVER_HOST = "http://127.0.0.1"
SERVER_PORT = 8000
SERVER_URL = f"{SERVER_HOST}:{SERVER_PORT}"
TEST_ENDPOINT = f"{SERVER_URL}/api/test"
HTML_PATH = "index.html"  # adjust if your file is elsewhere

def start_server():
    print("[*] Starting FastAPI server with uvicorn...")
    return subprocess.Popen(
        ["./venv/python.exe", "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

def wait_for_server():
    print("[*] Waiting for server to be ready...")
    while True:
        try:
            res = requests.get(TEST_ENDPOINT, timeout=1)
            if res.status_code == 200:
                print("[+] Server is up!")
                return
        except requests.exceptions.ConnectionError:
            print("[!] Still waiting...")
        time.sleep(1)

def open_browser():
    filepath = os.path.abspath(HTML_PATH)
    print(f"[*] Opening browser to {filepath}")
    webbrowser.open(f"file://{filepath}")

if __name__ == "__main__":
    server_proc = start_server()
    try:
        wait_for_server()
        open_browser()
        server_proc.wait()  # Keeps the script running with the server
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
        server_proc.terminate()
