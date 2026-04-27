import json
import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from jinja2 import Environment, FileSystemLoader
import uvicorn

app = FastAPI()
_env = Environment(loader=FileSystemLoader("scripts/trading/templates"), cache_size=0)
templates = Jinja2Templates(env=_env)
STATE_FILE = "scripts/trading/state.json"
EMERGENCY_FLAG = "scripts/trading/emergency_close.flag"
LOGS_FILE = "scripts/trading/logs.json"


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"capital": 0, "positions": {}}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"state": load_state()}
    )


@app.get("/api/state")
async def get_state():
    return load_state()


@app.get("/api/logs")
async def get_logs():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE) as f:
            return json.load(f)
    return []


@app.post("/api/emergency-close")
async def emergency_close():
    with open(EMERGENCY_FLAG, "w") as f:
        f.write("1")
    return {"status": "emergency close requested"}


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
