import traceback
from typing import List
from io import BytesIO
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path
import uuid

from processor import processFiles

SESSIONS = {}

app = FastAPI(title="Demo")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def uploadFiles(request: Request, files: List[UploadFile] = File(...)):
    session_id = uuid.uuid4().hex
    try:
        filedata = []
        for file in files:
            contents = await file.read()
            if not file.filename: continue

            suffix = Path(file.filename).suffix.lower()
            if suffix in (".csv"):
                df = pd.read_csv(BytesIO(contents))
            else:
                print(f"ERR: Unknown file type: {file.filename}")
                continue

            df.columns = df.columns.str.strip()
            filedata.append((file.filename, df))

        results = processFiles(filedata)

        SESSIONS[session_id] = results

        # Build the selector HTML that gets swapped into the page
        player_names = sorted(results["players"].keys())
        has_team = len(results["team"]) > 0

        player_buttons = "".join(
            f'<button class="selector-btn player-btn" onclick="selectPlayer(this, \'{session_id}\', {repr(p)})">{p}</button>'
            for p in player_names
        )
        team_btn = (
            f'<button class="selector-btn team-btn" onclick="selectPlayer(this, \'{session_id}\', \'__team__\')">Team Stats</button>'
        ) if has_team else ""

        return HTMLResponse(f"""
            <div class="selector-panel">
                {'<div class="selector-group">' + team_btn + '</div><div class="selector-divider">Players</div>' if has_team else '<div class="selector-divider" style="border-top:none;padding-top:0">Players</div>'}
                <div class="selector-group">
                    {player_buttons}
                </div>
            </div>
            <div id="chart-area"></div>
        """)

    except Exception as exc:
        tb = traceback.format_exc()
        return HTMLResponse(f'<pre class="error-msg">{exc}\n\n{tb}</pre>')


@app.get("/charts/{session_id}/{player}", response_class=HTMLResponse)
async def getCharts(session_id: str, player: str):
    session = SESSIONS.get(session_id)
    if not session:
        return HTMLResponse('<p class="error-msg">Session expired. Please re-upload your files.</p>')

    items = session["team"] if player == "__team__" else session["players"].get(player, [])
    title = "Team Stats" if player == "__team__" else player

    if not items:
        return HTMLResponse(f'<p class="error-msg">No charts found for {title}.</p>')

    chart_blocks = "".join(f"""
        <div class="chart-wrapper">
            <div class="chart-header"></div>
            {fig.to_html(full_html=False, include_plotlyjs=False)}
        </div>
    """ for _, fig in items)

    return HTMLResponse(f"""
        <div class="chart-area-header">
            <span class="chart-area-title">{title}</span>
        </div>
        <div class="charts">{chart_blocks}</div>
    """)
