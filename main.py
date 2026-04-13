import asyncio
import uuid

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

import plotly.io as pio

from charts.init import getCharts
import processor

app = FastAPI()
templates = Environment(loader=FileSystemLoader("templates"), cache_size=0)

SESSIONS: dict[str, dict] = {}
CHART_CACHE: dict[tuple, str] = {}   # (session_id, game, player) -> content HTML

TEAM_VIEWS = ["Touchmaps", "Play Time", "Efficiency", "Distribution"]


def renderPlotly(fig, static=False):
    return pio.to_html(
        fig, full_html=False, include_plotlyjs=False,
        config={"responsive": True, "displayModeBar": False, "staticPlot": static}
    )


def buildContentHtml(data, game, player) -> str:
    """Render charts for one (game, player) combo. Returns the inner content HTML."""
    title_html = charts_html = stats_html = ""
    try:
        title, figs = getCharts(data, game, player)
    except Exception as exc:
        return f'<p class="error-msg">Chart error: {exc}</p>'

    if title:
        title_html = f'<div class="chart-title">{title}</div>'
    if figs:
        stats_html = f'<div class="stats">{renderPlotly(figs[0], True)}</div>'
        divs = "\n".join(
            f'<div class="chart-wrapper">{renderPlotly(f)}</div>'
            for f in figs[1:]
        )
        charts_html = f'<div class="charts">{divs}</div>'
    else:
        charts_html = '<p class="error-msg">No charts returned.</p>'

    return title_html + stats_html + charts_html


async def preloadSession(session_id: str):
    """
    Background task: render every (game, player) combo after upload.
    Yields to the event loop between renders so the server stays responsive.
    """
    data = SESSIONS.get(session_id)
    if data is None:
        return

    games   = ["All"] + processor.getGameList(data)
    players = TEAM_VIEWS + processor.getPlayerList(data)

    for game in games:
        for player in players:
            key = (session_id, game, player)
            if key not in CHART_CACHE:
                # run the CPU-bound render in a thread so we don't block
                loop = asyncio.get_event_loop()
                content = await loop.run_in_executor(
                    None, buildContentHtml, data, game, player
                )
                CHART_CACHE[key] = content
            await asyncio.sleep(0)   # yield between each render


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    html = templates.get_template("index.html").render(request=request)
    return HTMLResponse(html)


@app.post("/upload", response_class=HTMLResponse)
async def upload(files: list[UploadFile] = File(...)):
    file_list = [(f.filename or "unknown", await f.read()) for f in files]
    file_count = len(file_list)

    data, warnings = processor.processUploads(file_list)

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = data

    games   = processor.getGameList(data)
    players = processor.getPlayerList(data)

    # kick off background preloading — doesn't block the upload response
    asyncio.create_task(preloadSession(session_id))

    status_html = f"""
    <div id="upload-status" hx-swap-oob="true" class="upload-success">
        ✓ {file_count} file{"s" if file_count != 1 else ""} uploaded
    </div>"""

    return HTMLResponse(
        status_html +
        sidebarHtml(
            session_id=session_id,
            games=games,
            players=players,
            warnings=warnings,
            active_game="All",
            active_player="Touchmaps",
        )
    )


@app.get("/charts/{session_id}", response_class=HTMLResponse)
async def charts_view(session_id, game: str = "All", player: str = "Touchmaps"):
    data = SESSIONS.get(session_id)
    if data is None:
        return HTMLResponse('<p class="error-msg">Session expired. Re-upload files.</p>')

    games   = processor.getGameList(data)
    players = processor.getPlayerList(data)

    key = (session_id, game, player)

    if key not in CHART_CACHE:
        # preloader hasn't reached this combo yet — render it now and cache it
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None, buildContentHtml, data, game, player
        )
        CHART_CACHE[key] = content

    games_bar     = buildGamesBar(session_id, games, game, player)
    players_panel = buildPlayersPanel(session_id, players, game, player)

    return HTMLResponse(CHART_CACHE[key] + games_bar + players_panel)


# ── nav helpers (unchanged) ──────────────────────────────────────────────────

def buildGamesBar(session_id, games, active_game, player):
    def btn(label, game_value):
        active = "active" if game_value == active_game else ""
        url = f"/charts/{session_id}?game={game_value}&player={player}"
        return f"""
        <button class="selector-btn {active}"
            hx-get="{url}"
            hx-target="#chart-area"
            hx-swap="innerHTML"
            hx-indicator="#loading">
            {label}
        </button>"""

    buttons = btn("All Games", "All") + "".join(btn(g, g) for g in games)
    return f"""
    <div id="games-bar" class="team-bar" hx-swap-oob="true">
        {buttons}
    </div>"""


def buildPlayersPanel(session_id, players, game, active_player):
    def pbtn(name, extra_class=""):
        active = "active" if name == active_player else ""
        url    = f"/charts/{session_id}?game={game}&player={name}"
        return f"""
        <button class="selector-btn {extra_class} {active}"
            hx-get="{url}"
            hx-target="#chart-area"
            hx-swap="innerHTML"
            hx-indicator="#loading">
            {name}
        </button>"""

    team_buttons   = "".join(pbtn(v) for v in TEAM_VIEWS)
    player_buttons = "".join(pbtn(p) for p in players)

    return f"""
    <aside id="players-panel" class="selector-panel" hx-swap-oob="true">
        <div class="selector-group">
            <div class="selector-label">TEAM</div>
            {team_buttons}
        </div>
        <div class="selector-divider"></div>
        <div class="selector-group">
            <div class="selector-label">PLAYERS</div>
            {player_buttons}
        </div>
    </aside>"""


def sidebarHtml(session_id, games, players, warnings, active_game, active_player):
    warn_html = ""
    if warnings:
        items = "\n".join(f"<li>{w}</li>" for w in warnings)
        warn_html = f"""
        <div class="warnings-block">
          <div class="warn-title">⚠ WARNINGS</div>
          <ul class="warn-list">{items}</ul>
        </div>"""

    games_bar = buildGamesBar(
        session_id, games, active_game, active_player
    ).replace('hx-swap-oob="true"', "")

    players_panel = buildPlayersPanel(
        session_id, players, active_game, active_player
    ).replace('hx-swap-oob="true"', "")

    return f"""
    {warn_html}
    {games_bar}
    <div class="workspace">
        {players_panel}
        <section class="chart-section">
            <div id="chart-area" class="chart-area"
                 hx-get="/charts/{session_id}?game={active_game}&player={active_player}"
                 hx-trigger="load"
                 hx-swap="innerHTML">
                <p class="loading-pulse">Loading...</p>
            </div>
        </section>
    </div>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
