import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

import pandas as pd
import plotly.graph_objects as go

BACKGROUND = "#0d0f14"
WHITE = "#ffffff"
BLUE = "#6495ed"
LIGHTBLUE = "#89cff0"
GREEN = "#00ff40"
RED = "#e23d28"
PURPLE = "#df73ff"

def detectDataset(fname: str) -> str | None:
    name = Path(fname).stem.lower()
    if "passes" in name:             return "passes"
    if "defensive blocks" in name:   return "defense"
    if "player stats" in name:       return "pstats"
    if "points" in name:             return "points"
    if "possessions" in name:        return "possessions"
    if "stall outs against" in name: return "stalls"
    return None

def extractGame(fname: str) -> str:
    match = re.search(r'vs\.\s+(.+?)\s+\d{4}-\d{2}-\d{2}', Path(fname).stem)
    return match.group(1).strip() if match else "Unknown"

def datasetLabel(key: str) -> str:
    return {
        "passes": "Touchmaps",
        "defense": "Defensive Blocks",
        "pstats": "Player Stats",
        "points": "Points",
        "possessions": "Possessions",
        "stalls": "Stall Outs Against",
    }.get(key, key)

X_MIN, X_MAX = 0, 40
Y_MIN, Y_MAX = 0, 110

STARTX = 'Start X (0 -> 1 = left sideline -> right sideline)'
STARTY = 'Start Y (0 -> 1 = back of opponent endzone -> back of own endzone)'
ENDX = 'End X (0 -> 1 = left sideline -> right sideline)'
ENDY = 'End Y (0 -> 1 = back of opponent endzone -> back of own endzone)'

def createFigureNormalized(title: str) -> go.Figure:
    fig = go.Figure() # go figure

    fig.update_layout(
        title=title,
        width=450,
        height=600,
        xaxis=dict(range=[-20, 20], showticklabels=False, showgrid=False, linecolor="black", zerolinecolor="black"),
        yaxis=dict(range=[-20, 60], showticklabels=False, showgrid=False, linecolor="black", zerolinecolor="black"),
    )

    return fig

def createFigure(title: str) -> go.Figure:
    fig = go.Figure() # go figure

    fig.update_layout(
        title=title,
        width=450,
        height=800,
        plot_bgcolor = WHITE,
        paper_bgcolor = WHITE,
        xaxis=dict(range=[0, 40], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        yaxis=dict(range=[0, 110], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        shapes=[
            dict(type="line", x0=0, x1=40, y0=20, y1=20, line=dict(width=3, color="black"), layer="below"),
            dict(type="line", x0=0, x1=40, y0=90, y1=90, line=dict(width=3, color="black"), layer="below"),
            dict(type="rect", x0=0, x1=40, y0=0, y1=110, line=dict(width=4, color="black"), layer="below"),
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=[20, 20], y=[40, 70], mode="markers",
            marker=dict( symbol="x", size=10, color="gray"),
            showlegend=False, hoverinfo="skip",
        )
    )

    return fig

def processTouchmap(df, player_col, label, normalized=False):
    results = {}

    for player, group in df.groupby(player_col):
        fig = (
            createFigureNormalized(f"{player} {label}")
            if normalized
            else createFigure(f"{player} {label}")
        )

        catch_traces = []
        assist_traces = []
        drop_traces = []
        throwaway_traces = []

        short_threshold = 10

        if label == "Throws": c = ( RED, PURPLE, GREEN, LIGHTBLUE, BLUE )
        else: c = ( PURPLE, RED, GREEN, LIGHTBLUE, BLUE )

        for _, row in group.iterrows():
            dist = row['Distance (m)']
            if row['Thrower error?']: line_color = c[0]
            elif row['Receiver error?']: line_color = c[1]
            elif row['Assist?']: line_color = c[2]
            elif dist < short_threshold: line_color = c[3]
            else: line_color = c[4]

            if normalized:
                start_x = 0
                start_y = 0
                end_x = (row[ENDX] - row[STARTX]) * (X_MAX - X_MIN)
                end_y = (row[ENDY] - row[STARTY]) * (Y_MIN - Y_MAX)
            else:
                start_x = X_MIN + row[STARTX] * (X_MAX - X_MIN)
                start_y = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
                end_x = X_MIN + row[ENDX] * (X_MAX - X_MIN)
                end_y = Y_MAX + row[ENDY] * (Y_MIN - Y_MAX)

            trace = go.Scatter(
                x=[start_x, end_x],
                y=[start_y, end_y],
                line=dict(width=2, color=line_color),
                mode="lines+markers",
                marker=dict(size=10, symbol="arrow-wide", angleref="previous"),
                showlegend=False,
            )

            if row['Thrower error?']: throwaway_traces.append(trace)
            elif row['Receiver error?']: drop_traces.append(trace)
            elif row['Assist?']: assist_traces.append(trace)
            else: catch_traces.append(trace)

        for trace in catch_traces + assist_traces + drop_traces + throwaway_traces:
            fig.add_trace(trace)

        results[player] = [fig]

    return results

def processTouchmaps(df):
    """ return 4 graphs: passes, receptions + normalized variants """
    combined = defaultdict(list)

    configs = [
        ("Thrower", "Throws", False),
        ("Receiver", "Receptions", False),
        ("Thrower", "Throws", True),
        ("Receiver", "Receptions", True),
    ]

    for player_col, label, normalized in configs:
        results = processTouchmap(df, player_col, label, normalized)

        for player, figs in results.items():
            combined[player].extend(figs)

    return combined

def run(key: str, df: pd.DataFrame) -> Dict[str, List[go.Figure]]:
    if key == "passes":      return processTouchmaps(df)
    # if key == "defense":     return processDefense(df)
    # if key == "pstats":      return processPStats(df)
    # if key == "points":      return processPoints(df)
    # if key == "possessions": return processPossessions(df)
    # if key == "stalls":      return processStalls(df)
    return {}

def processFiles(file_data: list) -> dict:
    buckets = defaultdict(list)
    for fname, df in file_data:
        key = detectDataset(fname)
        if key is None:
            print(f"Skipping bad file: {fname}")
            continue
        df = df.copy()
        df["_game"] = extractGame(fname)
        buckets[key].append(df)

    player_graphs: Dict[str, list] = defaultdict(list)
    team_graphs: list = []

    for key, dfs in buckets.items():
        combined = pd.concat(dfs, ignore_index=True)
        results = run(key, combined)
        label = datasetLabel(key)
        for player, figs in results.items():
            for fig in figs:
                if player == "__team__":
                    team_graphs.append((label, fig))
                else:
                    player_graphs[player].append((label, fig))

    return {"players": dict(player_graphs), "team": team_graphs}
