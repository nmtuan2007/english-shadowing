import subprocess
import sys
import os
import signal
import time

def run_app():
    # Get the current directory
    root_dir = os.getcwd()
    frontend_dir = os.path.join(root_dir, "frontend")

    print("🚀 Starting English Shadowing System...")

    # 1. Start the Backend (FastAPI)
    print("📡 Starting Backend on http://localhost:8000")
    backend_process = subprocess.Popen(
        [sys.executable, "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # 2. Start the Frontend (Next.js)
    print("💻 Starting Frontend on http://localhost:3000")
    # Use shell=True for npm to work across Windows/Mac/Linux
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True if os.name == 'nt' else False
    )

    try:
        # Keep the script running and print backend logs
        while True:
            line = backend_process.stdout.readline()
            if line:
                print(f"[Backend] {line.strip()}")
            
            # Check if processes are still alive
            if backend_process.poll() is not None:
                print("❌ Backend stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend stopped unexpectedly.")
                break
                
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down processes...")
        # Terminate both processes on Ctrl+C
        backend_process.terminate()
        frontend_process.terminate()
        
        # On Windows, we sometimes need to force kill npm sub-processes
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(frontend_process.pid)], capture_output=True)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(backend_process.pid)], capture_output=True)
            
        print("👋 Goodbye!")

if __name__ == "__main__":
    run_app()
