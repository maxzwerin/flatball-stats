import uuid

from fastapi import FastAPI, File, Request, UploadFile, Response
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

import plotly.io as pio

from charts.init import getCharts
import processor

app = FastAPI()
templates = Environment(loader=FileSystemLoader("templates"), cache_size=0)

SESSIONS: dict[str, dict] = {}

TEAM_VIEWS = ["Touchmaps", "Play Time", "Efficiency", "Distribution"]

def renderPlotly(fig, static=False):
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs=True,
        config={"responsive": True, "displayModeBar": False, "staticPlot": static}
    )

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

    games = processor.getGameList(data)
    players = processor.getPlayerList(data)

    status_html = f"""
    <div id="upload-status" hx-swap-oob="true" class="upload-success">
        ✓ {file_count} file{"s" if file_count != 1 else ""} uploaded
    </div> """

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

    stats_html = ""
    title_html = ""
    charts_html = ""

    try:
        title, figs = getCharts(data, game, player)
    except Exception as exc:
        charts_html = f'<p class="error-msg">Chart error: {exc}</p>'
    else:
        if title:
            title_html = f'<div class="chart-title">{title}</div>'
        if figs:
            stats_html = f'<div class="stats">{renderPlotly(figs[0], True)}</div>'
            figs = figs[1:]

            divs = "\n".join(
                f'<div class="chart-wrapper">{renderPlotly(f)}</div>'
                for f in figs
            )
            charts_html = f'<div class="charts">{divs}</div>'
        else:
            charts_html = '<p class="error-msg">No charts returned.</p>'


    games_bar = buildGamesBar(session_id, games, game, player)
    players_panel = buildPlayersPanel(session_id, players, game, player)

    return HTMLResponse(title_html + stats_html + charts_html + games_bar + players_panel)

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
        </button>
        """

    buttons = btn("All Games", "All")
    for g in games:
        buttons += btn(g, g)

    return f"""
    <div id="games-bar"
         class="team-bar"
         hx-swap-oob="true">
        {buttons}
    </div>
    """

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
        </button>
        """

    team_buttons   = "".join(pbtn(v) for v in TEAM_VIEWS)
    player_buttons = "".join(pbtn(p) for p in players)

    return f"""
    <aside id="players-panel"
           class="selector-panel"
           hx-swap-oob="true">

        <div class="selector-group">
            <div class="selector-label">TEAM</div>
            {team_buttons}
        </div>

        <div class="selector-divider"></div>

        <div class="selector-group">
            <div class="selector-label">PLAYERS</div>
            {player_buttons}
        </div>

    </aside>
    """

def sidebarHtml(session_id, games, players, warnings, active_game, active_player):
    warn_html = ""
    if warnings:
        items = "\n".join(f"<li>{w}</li>" for w in warnings)
        warn_html = f"""
        <div class="warnings-block">
          <div class="warn-title">⚠ WARNINGS</div>
          <ul class="warn-list">{items}</ul>
        </div>
        """

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
    </div>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
