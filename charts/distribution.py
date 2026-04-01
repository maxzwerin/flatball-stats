import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .constants import *

BIN_SIZE = 5
X_MIN, X_MAX = -20, 80

def genDistribution(passes, title):
    completions = passes[passes["Turnover?"] != 1]
    turnovers   = passes[passes["Turnover?"] == 1]
    assists     = passes[passes["Assist?"]   == 1]
    non_scoring = completions[completions["Assist?"] != 1]

    df = pd.concat([
        turnovers.assign(type="turnover"),
        assists.assign(type="assist"),
        non_scoring.assign(type="non_scoring"),
    ])[["type", "Forward distance (m)"]].rename(columns={"Forward distance (m)": "dist"})

    total_non_scoring = (df["type"] == "non_scoring").sum()
    total_assists = (df["type"] == "assist").sum()
    total_turnovers  = (df["type"] == "turnover").sum()
    total_throws = (passes["Thrower"] != None).sum()

    bins = list(range(X_MIN, X_MAX + BIN_SIZE, BIN_SIZE))
    bin_centers = [b + BIN_SIZE / 2 for b in bins[:-1]]

    df["bin"] = pd.cut(df["dist"], bins=bins, labels=bin_centers, right=False)
    bin_counts = (
        df.groupby(["bin", "type"], observed=True)
        .size()
        .unstack(fill_value=0)
    )

    bin_total = bin_counts.sum(axis=1)
    completion_pct = bin_counts.get("non_scoring", 0) / bin_total * 100
    assist_pct = bin_counts.get("assist", 0) / bin_total * 100
    turn_pct = bin_counts.get("turnover", 0) / bin_total * 100

    subplot_titles = (
        f"All Throws ({total_throws})",
        f"Non-scoring Completions ({total_non_scoring})",
        f"Assists ({total_assists})",
        f"Turnovers ({total_turnovers})",
    )

    fig = make_subplots(
        rows=5, cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.05,
    )

    stacked_cfg = [
        (df[df["type"] == "non_scoring"]["dist"], BLUE,  "Non-scoring"),
        (df[df["type"] == "assist"]["dist"],      GREEN, "Assist"),
        (df[df["type"] == "turnover"]["dist"],    RED,   "Turnover"),
    ]
    for x_data, color, name in stacked_cfg:
        fig.add_trace(
            go.Histogram(
                x=x_data, name=name,
                marker=dict(color=color),
                bingroup=1,
                xbins=dict(start=X_MIN, end=X_MAX, size=BIN_SIZE),
                showlegend=False,
            ),
            row=1, col=1,
        )

    hist_cfg = [
        (df[df["type"] == "non_scoring"]["dist"], BLUE,  2),
        (df[df["type"] == "assist"]["dist"],      GREEN, 3),
        (df[df["type"] == "turnover"]["dist"],    RED,   4),
    ]
    for x_data, color, row in hist_cfg:
        fig.add_trace(
            go.Histogram(
                x=x_data, marker=dict(color=color), showlegend=False,
                xbins=dict(start=X_MIN, end=X_MAX, size=BIN_SIZE),
            ),
            row=row, col=1,
        )

    line_cfg = [
        (completion_pct, "Non-Scoring Completion %", BLUE, "circle"),
        (assist_pct, "Assist %", GREEN, "square"),
        (turn_pct, "Turnover %", RED, "diamond"),
    ]
    for y_data, name, color, symbol in line_cfg:
        fig.add_trace(go.Scatter(
                x=bin_centers,
                y=y_data.fillna(0).values,
                name=name,
                mode="lines+markers",
                marker_symbol=symbol,
                line=dict(color=color, width=2),
                marker=dict(size=10),
            ),
            row=5, col=1,
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        showlegend=True, 
        legend=dict(orientation="h", x=0.30, y=0.18, borderwidth=0),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE, height=1400, width=1000,
        barmode="stack", bargap=0.1, margin=dict(l=60, r=60, t=60, b=40),
    )

    fig.update_xaxes(range=[X_MIN, X_MAX])
    fig.update_xaxes(title_text="Forward Distance (m)", row=5, col=1)

    for row in range(1, 5):
        fig.update_yaxes(
            title_text="Num. Passes", row=row, col=1,
            showgrid=True, gridcolor=LIGHTGRAY,
        )

    fig.update_yaxes(
        title_text="Likelihood Per Distance", row=5, col=1,
        showgrid=True, gridcolor=LIGHTGRAY, range=[0, 100],
    )

    for ann in fig.layout.annotations:
        ann.update(font=dict(size=12))

    return fig
