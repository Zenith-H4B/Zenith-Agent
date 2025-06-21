from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse, JSONResponse
from agents.LogCleanupAgent import LogCleanupAgent
import asyncio
import threading
import os
import time
from logs.log_buffer import log_buffer

router = APIRouter()

LOG_FILE = "logs/app.log"
CACHE_FILE = "logs/log_cache.txt"

# Background thread: tail app.log into cache file
def log_cache_updater():
    last_pos = 0
    while True:
        try:
            with open(LOG_FILE, "r") as src, open(CACHE_FILE, "a+") as cache:
                src.seek(last_pos)
                lines = src.readlines()
                last_pos = src.tell()
                if lines:
                    cache.writelines(lines)
                    cache.flush()
            time.sleep(1)
        except Exception:
            time.sleep(2)

# Ensure single background thread
def start_log_cache_thread_once():
    if not hasattr(start_log_cache_thread_once, "started"):
        t = threading.Thread(target=log_cache_updater, daemon=True)
        t.start()
        start_log_cache_thread_once.started = True

# Async generator: read cache, clean via agent, stream as SSE
async def log_streamer():
    start_log_cache_thread_once()
    agent = LogCleanupAgent()
    last_pos = 0
    while True:
        try:
            if not os.path.exists(CACHE_FILE):
                await asyncio.sleep(1)
                continue

            with open(CACHE_FILE, "r") as f:
                f.seek(last_pos)
                new_lines = f.readlines()
                last_pos = f.tell()

            if new_lines:
                # Clean the raw logs
                cleaned_resp = await agent.process({"raw_logs": new_lines})
                cleaned = cleaned_resp.data.get("cleaned_logs", [])
                for ln in cleaned:
                    # Format as SSE message
                    yield f"data: {ln}\n\n"

            await asyncio.sleep(1)
        except Exception as e:
            yield f"data: Error streaming logs: {str(e)}\n\n"
            await asyncio.sleep(2)

@router.get("/logs/stream")
async def stream_logs():
    """Stream cleaned logs as Server-Sent Events (SSE) from cache."""
    return StreamingResponse(
        log_streamer(),
        media_type="text/event-stream",
    )

@router.get("/logs/all")
async def get_all_logs():
    """Return all cleaned logs as a JSON array for frontend display."""
    agent = LogCleanupAgent()
    if not os.path.exists(CACHE_FILE):
        return JSONResponse(content={"logs": []})
    with open(CACHE_FILE, "r") as f:
        raw_logs = f.readlines()
    response = await agent.process({"raw_logs": raw_logs})
    cleaned_logs = response.data.get("cleaned_logs", [])
    return JSONResponse(content={"logs": cleaned_logs})

@router.get("/logs/showcase")
async def get_logs():
    log_buffer.seek(0)
    logs = log_buffer.read()
    return Response(content=logs, media_type="text/plain")
