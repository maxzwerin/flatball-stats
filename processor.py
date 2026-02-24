from pathlib import Path
from collections import defaultdict
import plotly.graph_objects as go

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
        width=500,
        height=700,
        xaxis=dict(range=[-25, 25], showticklabels=True, showgrid=False),
        yaxis=dict(range=[-20, 70], showticklabels=True, showgrid=False),
    )

    return fig

def createFigure(title: str) -> go.Figure:
    fig = go.Figure() # go figure

    fig.update_layout(
        title=title,
        width=500,
        height=900,
        xaxis=dict(range=[0, 40], showticklabels=False, showgrid=False),
        yaxis=dict(range=[0, 110], showticklabels=False, showgrid=False),
        shapes=[
            dict(type="line", x0=0, x1=40, y0=20, y1=20, line=dict(width=3, color="black"), layer="below"),
            dict(type="line", x0=0, x1=40, y0=90, y1=90, line=dict(width=3, color="black"), layer="below"),
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

def processDefense(df):
    return

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

        for _, row in group.iterrows():
            if row['Thrower error?']:
                # red is a throwaway, purple is a drop
                line_color = 'red' if label == "Throws" else 'purple'
            elif row['Receiver error?']:
                # purple is a throwaway, red is a drop
                line_color = 'purple' if label == "Throws" else 'red'
            elif row['Assist?']:
                line_color = 'green'
            else:
                line_color = 'blue'

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
                marker=dict(size=5, symbol="arrow-bar-up", angleref="previous"),
                showlegend=False,
            )

            if row['Thrower error?']:
                throwaway_traces.append(trace)
            elif row['Receiver error?']:
                drop_traces.append(trace)
            elif row['Assist?']:
                assist_traces.append(trace)
            else:
                catch_traces.append(trace)

        for trace in catch_traces + assist_traces + drop_traces + throwaway_traces:
            fig.add_trace(trace)

        results[player] = [fig]

    return results

def processPasses(df, normalized=False):
    return processTouchmap(df, "Thrower", "Throws", normalized)

def processReceptions(df, normalized=False):
    return processTouchmap(df, "Receiver", "Receptions", normalized)

def processPStats(df):
    return

def processPoints(df):
    return

def processPossessions(df):
    return

def processStalls(df):
    return

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

def processFiles(df, fname):
    name = Path(fname).stem.lower()

    if "passes" in name:
        return processTouchmaps(df), "Touchmaps"
    # elif "defensive blocks" in name:
    #     return processDefense(df), "Defensive Blocks"
    # elif "player stats" in name:
    #     return processPStats(df), "Player Stats"
    # elif "points" in name:
    #     return processPoints(df), "Points"
    # elif "possessions" in name:
    #     return processPossessions(df), "Possessions"
    # elif "stall outs against" in name:
    #     return processStalls(df), "Stall Outs Against"
    else:
        raise ValueError(f"Unknown dataset: {fname}")
