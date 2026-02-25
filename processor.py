import re
from io import BytesIO
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple

import pandas as pd
import plotly.graph_objects as go

BACKGROUND = "#0d0f14"
WHITE = "#ffffff"
BLUE = "#6495ed"
LIGHTBLUE = "#89cff0"
GREEN = "#00ff40"
RED = "#e23d28"
PURPLE = "#df73ff"

EXPECTED_TYPES = {
    "defensive blocks",
    "passes",
    "player stats",
    "points",
    "possessions",
    "stalls out against",
}

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

X_MIN, X_MAX = 0, 40
Y_MIN, Y_MAX = 0, 110

STARTX = 'Start X (0 -> 1 = left sideline -> right sideline)'
STARTY = 'Start Y (0 -> 1 = back of opponent endzone -> back of own endzone)'
ENDX = 'End X (0 -> 1 = left sideline -> right sideline)'
ENDY = 'End Y (0 -> 1 = back of opponent endzone -> back of own endzone)'

def addLegend(fig: go.Figure, label: str) -> go.Figure:
    if label == "Throws":
        items = [
            ("Throwaway", RED),
            ("Assist", GREEN),
            ("Drop", PURPLE),
            ("Short Pass", LIGHTBLUE),
            ("Long Pass", BLUE),
        ]
    else:
        items = [
            ("Drop", RED),
            ("Throwaway", PURPLE),
            ("Goal", GREEN),
            ("Short Catch", LIGHTBLUE),
            ("Long Catch", BLUE),
        ]
    for name, color in items:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="lines",
            line=dict(color=color, width=3),
            name=name,
            showlegend=True,
        ))
    return fig

def createFigureNormalized(title: str) -> go.Figure:
    fig = go.Figure() # go figure

    fig.update_layout(
        title=title,
        width=450,
        height=600,
        xaxis=dict(range=[-20, 20], showticklabels=True, showgrid=False, showline=False, zerolinecolor="black"),
        yaxis=dict(range=[-20, 60], showticklabels=True, showgrid=False, showline=False, zerolinecolor="black"),
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
        addLegend(fig, label)

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

# def processFiles(file_data: list) -> dict:
#     buckets = defaultdict(list)
#     for fname, df in file_data:
#         key = detectDataset(fname)
#         if key is None:
#             print(f"Skipping bad file: {fname}")
#             continue
#         df = df.copy()
#         df["_game"] = extractGame(fname)
#         buckets[key].append(df)
#
#     player_graphs: Dict[str, list] = defaultdict(list)
#     team_graphs: list = []
#
#     for key, dfs in buckets.items():
#         combined = pd.concat(dfs, ignore_index=True)
#         results = run(key, combined)
#         label = datasetLabel(key)
#         for player, figs in results.items():
#             for fig in figs:
#                 if player == "__team__":
#                     team_graphs.append((label, fig))
#                 else:
#                     player_graphs[player].append((label, fig))
#
#     return {"players": dict(player_graphs), "team": team_graphs}


def parseFilename(fname: str) -> Tuple[str | None, str | None]:
    """'Passes vs. Opponent 2026-02-18_22-57-28.csv' -> ('passes', 'Opponent')"""
    stem = Path(fname).stem
    match = re.match(r'^(.+?)\s+vs\.\s+(.+?)\s+\d{4}-\d{2}-\d{2}', stem, re.IGNORECASE)
    if not match:
        return None, None
    return match.group(1).strip().lower(), match.group(2).strip()

def datasetLabel(key: str) -> str:
    return {
        "passes":              "Touchmaps",
        "defensive blocks":    "Defensive Blocks",
        "player stats":        "Player Stats",
        "points":              "Points",
        "possessions":         "Possessions",
        "stalls out against":  "Stall Outs Against",
    }.get(key, key)


def intakeFiles(raw: List[Tuple[str, bytes]]) -> Tuple[List[Tuple[str, pd.DataFrame]], List[str]]:
    game_buckets: Dict[str, Dict[str, pd.DataFrame]] = defaultdict(dict)
    warnings = []

    for fname, contents in raw:
        suffix = Path(fname).suffix.lower()
        if suffix != ".csv":
            warnings.append(f"Skipped non-CSV file: {fname}")
            continue

        dataset_type, opponent = parseFilename(fname)
        if dataset_type is None or opponent is None:
            warnings.append(f"Unrecognised filename (expected 'Type vs. Opponent YYYY-MM-DD'): {fname}")
            continue

        df = pd.read_csv(BytesIO(contents))
        df.columns = df.columns.str.strip()
        df["Game"] = opponent
        game_buckets[opponent][dataset_type] = df

    # Check for missing file types per game
    for opponent, type_map in sorted(game_buckets.items()):
        missing = EXPECTED_TYPES - set(type_map.keys())
        if missing:
            warnings.append(f"<b>{opponent}</b>: missing {', '.join(sorted(missing))}")

    # Combine each dataset type across all games into one df
    combined: Dict[str, List[pd.DataFrame]] = defaultdict(list)
    for type_map in game_buckets.values():
        for dataset_type, df in type_map.items():
            combined[dataset_type].append(df)

    filedata = [
        (dtype, pd.concat(dfs, ignore_index=True))
        for dtype, dfs in combined.items()
    ]

    return filedata, warnings

# ── Public entry point ─────────────────────────────────────────────────────────

def processFiles(filedata: List[Tuple[str, pd.DataFrame]]) -> dict:
    player_graphs: Dict[str, list] = defaultdict(list)
    team_graphs: list = []
    games: set = set()

    for dataset_type, df in filedata:
        if "Game" in df.columns:
            games.update(df["Game"].unique())

        results = _run(dataset_type, df)
        label = datasetLabel(dataset_type)

        for player, figs in results.items():
            for fig in figs:
                if player == "__team__":
                    team_graphs.append((label, fig))
                else:
                    player_graphs[player].append((label, fig))

    return {
        "players": dict(player_graphs),
        "team":    team_graphs,
        "games":   games,
    }

# ── Dataset router ─────────────────────────────────────────────────────────────

def _run(key: str, df: pd.DataFrame) -> Dict[str, List[go.Figure]]:
    if key == "passes":           return processTouchmaps(df)
    # if key == "defensive blocks": return processDefense(df)
    # if key == "player stats":     return processPStats(df)
    # if key == "points":           return processPoints(df)
    # if key == "possessions":      return processPossessions(df)
    # if key == "stalls out against": return processStalls(df)
    return {}

# ── Your processing functions below ───────────────────────────────────────────
# ...
