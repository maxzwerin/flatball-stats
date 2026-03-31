import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from .constants import *

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

    fig = make_subplots(
        rows=4, cols=1,
        horizontal_spacing=0.04,
        vertical_spacing=0.04,
    )

    total_non_scoring = sum(df["type"]=="non_scoring")
    total_assists = sum(df["type"]=="assist")
    total_turnovers = sum(df["type"]=="turnover")
    total_throws = sum(passes["Thrower"]!=None)

    fig.add_trace(go.Histogram(
            x=df["dist"], 
            bingroup="stack",
            # f"All Throws ({total_throws})"
        ),
        row=1, col=1
    )

    fig.add_trace(go.Histogram(
            x=df[df["type"] == "non_scoring"]["dist"], 
            marker=dict(color=BLUE),
            # f"Non-scoring Completions ({total_non_scoring})",
        ),
        row=2, col=1
    )

    fig.add_trace(go.Histogram(
            x=df[df["type"] == "assist"]["dist"], 
            marker=dict(color=GREEN),
            # f"Assists ({total_assists})",
        ),
        row=3, col=1
    )

    fig.add_trace(go.Histogram(
            x=df[df["type"] == "turnover"]["dist"], 
            marker=dict(color=RED),
            # f"Turnovers ({total_turnovers})",
        ),
        row=4, col=1
    )

    # TODO: figure out how to name each subgraph

    # TODO: plots these 3 lines for final fig
    # completion %: liklihood of a successful throw
    # assist %: liklihood of a successful assist
    # turn %: liklihood of a turn

    # TODO: make shit look nice

    fig.update_layout(
        title=title,
        showlegend=False,
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        height=1000,
        bargap=0.1,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    fig.update_xaxes(range=[-20,80]),

    return fig
