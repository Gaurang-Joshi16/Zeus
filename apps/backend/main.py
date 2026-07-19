import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Add root directory to path to allow importing core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import core runtime components
from core.logging.logger import CoreLogger
from core.runtime.bootstrap import bootstrap_runtime, shutdown_runtime
from core.runtime.health import health_manager

# We use the core logger
logger = CoreLogger.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FastAPI Host starting...")
    await bootstrap_runtime()
    yield
    # Shutdown
    logger.info("FastAPI Host shutting down...")
    await shutdown_runtime()


app = FastAPI(title="Zeus Backend", version="0.0.1", lifespan=lifespan)

# SQLite Database Setup (Foundation)
SQLALCHEMY_DATABASE_URL = "sqlite:///./zeus.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Ensure the database tables are created (empty for now)
Base.metadata.create_all(bind=engine)


from fastapi import WebSocket, WebSocketDisconnect

from core.ipc.adapter import ipc_adapter


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ipc_adapter.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"[Backend] WebSocket endpoint received message: {data}")
            if "type" in data:
                command_type = data["type"]
                payload = data.get("payload", {})
                try:
                    result = await ipc_adapter.invoke(command_type, payload)
                    if "request_id" in data:
                        response = {"request_id": data["request_id"], "result": result}
                        logger.info(
                            f"[Backend] WebSocket broadcasting response: {response}"
                        )
                        await websocket.send_json(response)
                except Exception as e:
                    logger.error(f"Command {command_type} failed: {e}")
                    if "request_id" in data:
                        await websocket.send_json(
                            {"request_id": data["request_id"], "error": str(e)}
                        )
    except WebSocketDisconnect:
        ipc_adapter.disconnect(websocket)


@app.get("/health")
async def health_check():
    # The /health endpoint should simply request information from the Runtime Health Manager
    # rather than implementing health logic itself.
    runtime_health = await health_manager.get_system_health()
    return runtime_health

if __name__ == "__main__":
    import uvicorn
    import socket
    import urllib.request
    import json
    
    # Check if port is already in use
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        is_occupied = s.connect_ex(('127.0.0.1', 8000)) == 0
        
    if is_occupied:
        try:
            req = urllib.request.Request("http://127.0.0.1:8000/health")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode())
                # If we get a valid health response, it's our Zeus backend
                logger.info("Zeus backend already running, reusing.")
                sys.exit(0)
        except Exception:
            pass
            
        logger.error("Port 8000 is blocked by another application. Please free the port and try again.")
        sys.exit(1)

    # Start the backend via uvicorn if script is executed directly
    logger.info("Starting Uvicorn server on port 8000...")
    uvicorn.run("apps.backend.main:app", host="0.0.0.0", port=8000, reload=False)
