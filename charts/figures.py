import plotly.graph_objects as go
from .constants import *

PASS_LEGEND = {
    "Throwaway":  RED,
    "Drop":       PURPLE,
    "Assist":     GREEN,
    "Short Pass": LIGHTBLUE,
    "Long Pass":  BLUE,
}

RECEP_LEGEND = {
    "Drop":       RED,
    "Throwaway":  PURPLE,
    "Goal":       GREEN,
    "Short Pass": LIGHTBLUE,
    "Long Pass":  BLUE,
}

def createFigure(title):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        width=450, height=800,
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        xaxis=dict(range=[0, 40], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        yaxis=dict(range=[0, 110], showticklabels=False, showgrid=False, showline=False, zeroline=False),
        shapes=[
            dict(type="line", x0=0, x1=40, y0=20,  y1=20,  line=dict(width=3, color=BACKGROUND), layer="below"),
            dict(type="line", x0=0, x1=40, y0=90,  y1=90,  line=dict(width=3, color=BACKGROUND), layer="below"),
            dict(type="rect", x0=0, x1=40, y0=0,   y1=110, line=dict(width=4, color=BACKGROUND), layer="below"),
        ],
    )
    fig.add_trace(go.Scatter(
        x=[20, 20], y=[40, 70], mode="markers",
        marker=dict(symbol="x-thin", size=12, color=GRAY, line=dict(width=1, color=GRAY)),
        showlegend=False, hoverinfo="skip",
    ))
    return fig

def addLegend(fig, entries: dict):
    for name, color in entries.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=color, width=3),
            name=name, legendgroup=name, showlegend=True,
        ))

def makeTrace(sx, sy, ex, ey, color, group):
    return go.Scatter(
        x=[sx, ex], y=[sy, ey],
        line=dict(width=2, color=color),
        mode="lines+markers",
        marker=dict(size=10, symbol="arrow-wide", angleref="previous"),
        legendgroup=group,
        showlegend=False,
    )

def buildFig(title, data, render_order, legend, thrower=True):
    fig     = createFigure(title)
    buckets = {c: [] for c in render_order}

    # reverse lookup: color -> legend label
    color_to_group = {color: name for name, color in legend.items()}

    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)
        short = row['Distance (m)'] < 10 or sy > ey

        if     thrower and row['Thrower error?']:     color = RED
        elif   thrower and row['Receiver error?']:    color = PURPLE
        elif not thrower and row['Receiver error?']:  color = PURPLE
        elif not thrower and row['Thrower error?']:   color = RED
        elif row['Assist?']:                          color = GREEN
        elif short:                                   color = LIGHTBLUE
        else:                                         color = BLUE

        group = color_to_group.get(color, "other")
        buckets[color].append(makeTrace(sx, sy, ex, ey, color, group))

    for color in render_order:
        for trace in buckets[color]:
            fig.add_trace(trace)

    addLegend(fig, legend)
    return fig

def genPasses(data):
    return buildFig(
        title="Passes",
        data=data,
        render_order=(BLUE, LIGHTBLUE, GREEN, PURPLE, RED),
        legend=PASS_LEGEND,
        thrower=True,
    )

def genReceptions(data):
    return buildFig(
        title="Receptions",
        data=data,
        render_order=(BLUE, LIGHTBLUE, GREEN, RED, PURPLE),
        legend=RECEP_LEGEND,
        thrower=False,
    )

def genTeamPasses(data):
    sideline = data['From sideline?'] == 1
    huck     = data['Huck?'] == 1
    redzone  = data[STARTY] <= 0.35

    masks = {
        "Midfield Huck Passes":   huck & ~sideline,
        "Sideline Huck Passes":   huck &  sideline,
        "Sideline Short Passes": ~huck &  sideline,
        "Redzone Passes":         redzone,
        "Other Passes":          ~huck & ~sideline & ~redzone,
    }

    return [
        buildFig(
            title=title,
            data=data[mask],
            render_order=(BLUE, LIGHTBLUE, GREEN, PURPLE, RED),
            legend=PASS_LEGEND,
        )
        for title, mask in masks.items()
    ]
