from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from agents.LogCleanupAgent import LogCleanupAgent
import asyncio
import threading
import queue

router = APIRouter()

# Thread-safe queue for log lines
data_queue = queue.Queue()

# Background thread function for log cleanup and streaming
def log_cleanup_thread():
    agent = LogCleanupAgent()
    log_path = "logs/app.log"
    last_pos = 0
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            with open(log_path, "r") as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                last_pos = f.tell()
            if new_lines:
                # Use the agent to clean up logs
                response = loop.run_until_complete(agent.process({"raw_logs": new_lines}))
                cleaned = response.data.get("cleaned_logs", [])
                for line in cleaned:
                    data_queue.put(line + "\n")
            loop.run_until_complete(asyncio.sleep(1))
        except Exception as e:
            data_queue.put(f"Error streaming logs: {str(e)}\n")
            loop.run_until_complete(asyncio.sleep(2))

# Start the background thread only once
def start_log_thread_once():
    if not hasattr(start_log_thread_once, "started"):
        t = threading.Thread(target=log_cleanup_thread, daemon=True)
        t.start()
        start_log_thread_once.started = True

async def log_streamer():
    start_log_thread_once()
    while True:
        try:
            line = data_queue.get()
            yield line
        except Exception as e:
            yield f"Error streaming logs: {str(e)}\n"
            await asyncio.sleep(2)

@router.get("/logs/stream")
async def stream_logs():
    """Stream cleaned agent logs in a chunked HTTP response."""
    return StreamingResponse(log_streamer(), media_type="text/plain")
