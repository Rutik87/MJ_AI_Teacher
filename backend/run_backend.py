import uvicorn
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    is_prod = os.getenv("ENVIRONMENT", "development").lower() == "production"
    reload_flag = not is_prod
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"[BOOT] Starting MPSC AI Backend (Host: {host}, Port: {port}, Environment: {os.getenv('ENVIRONMENT', 'development')}, Reload: {reload_flag})")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_flag)
