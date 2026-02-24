import traceback
from typing import List
from io import BytesIO

from collections import defaultdict

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path

from processor import *

def detectDataset(fname):
    name = Path(fname).stem.lower()

    if "passes" in name:
        return "passes", "Touchmaps"
    elif "defensive blocks" in name:
        return "defense", "Defensive Blocks"
    elif "player stats" in name:
        return "pstats", "Player Stats"
    elif "points" in name:
        return "points", "Points"
    elif "possessions" in name:
        return "possessions", "Possessions"
    elif "stall outs against" in name:
        return "stalls", "Stall Outs Against"
    else:
        raise ValueError(f"Unknown dataset: {fname}")

app = FastAPI(title="Demo")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def uploadFiles(request: Request, files: List[UploadFile] = File(...)):
    player_graphs = defaultdict(list)

    dataset_frames = defaultdict(list)
    dataset_labels = {}

    # read files and group them
    for file in files:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))

        key, label = detectDataset(file.filename)
        dataset_frames[key].append(df)
        dataset_labels[key] = label

    # process combined datasets
    for key, dfs in dataset_frames.items():
        df = pd.concat(dfs, ignore_index=True)
        name = dataset_labels[key]

    for key, dfs in dataset_frames.items():
        df = pd.concat(dfs, ignore_index=True)
        name = dataset_labels[key]

        if key == "passes":
            results = processTouchmaps(df)
        # elif key == "defense":
        #     results = processDefense(df)
        # elif key == "pstats":
        #     results = processPStats(df)
        # elif key == "points":
        #     results = processPoints(df)
        # elif key == "possessions":
        #     results = processPossessions(df)
        # elif key == "stalls":
        #     results = processStalls(df)

        for player, figs in results.items():
            for fig in figs:
                player_graphs[player].append((name, fig))

    # building the html
    sections = []

    for player, items in sorted(player_graphs.items()):
        chart_blocks = []

        for i, (dataset, fig) in enumerate(items):
            chart_html = fig.to_html(
                full_html=False,
                include_plotlyjs=False,
                config={"displayModeBar": True, "responsive": True},
            )

            chart_blocks.append(
                f"""
                <div class="chart-wrapper">
                    {chart_html}
                </div>
                """
            )

        sections.append(
            f"""
            <section class="file-result success">
                <div class="file-header">
                    <span class="filename">{player}</span>
                    <span class="badge ok">{len(items)} charts</span>
                </div>
                <div class="charts">
                    {''.join(chart_blocks)}
                </div>
            </section>
            """
        )

    return HTMLResponse("".join(sections))
