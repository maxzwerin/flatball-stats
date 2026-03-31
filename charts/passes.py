import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .constants import *

PASS_LEGEND = {
    "Throwaways": RED,
    "Drops":      PURPLE,
    "Assists":    GREEN,
    "Short":      LIGHTBLUE,
    "Long":       BLUE,
}

RECEP_LEGEND = {
    "Drops":      RED,
    "Throwaways": PURPLE,
    "Goals":      GREEN,
    "Short":      LIGHTBLUE,
    "Long":       BLUE,
}

TEAM_MASKS = {
    "Midfield Huck":  lambda h, s, r:  h & ~s,
    "Sideline Huck":  lambda h, s, r:  h &  s,
    "Sideline Short": lambda h, s, r: ~h &  s,
    "Redzone":        lambda h, s, r:  r,
    "Other":          lambda h, s, r: ~h & ~s & ~r,
}

CENTER_MARKER = go.Scatter(
    x=[20, 20], y=[40, 70], mode="markers",
    marker=dict(symbol="x-thin", size=12, color=GRAY, line=dict(width=1, color=GRAY)),
    showlegend=False, hoverinfo="skip",
)

FIELD_SHAPES = [
    dict(type="line", x0=0, x1=40, y0=20,  y1=20,  line=dict(width=3, color=BACKGROUND)),
    dict(type="line", x0=0, x1=40, y0=90,  y1=90,  line=dict(width=3, color=BACKGROUND)),
    dict(type="rect", x0=0, x1=40, y0=0,   y1=110, line=dict(width=4, color=BACKGROUND)),
]

def color(row, thrower):
    if     thrower and row['Thrower error?']:  return RED
    if     thrower and row['Receiver error?']: return PURPLE
    if not thrower and row['Receiver error?']: return PURPLE
    if not thrower and row['Thrower error?']:  return RED
    if row['Assist?']:                         return GREEN
    short = row['Distance (m)'] < 10 or (
        Y_MAX + row[STARTY] * (Y_MIN - Y_MAX) > Y_MAX + row[ENDY] * (Y_MIN - Y_MAX)
    )
    return LIGHTBLUE if short else BLUE

def makeTrace(sx, sy, ex, ey, color, group):
    return go.Scatter(
        x=[sx, ex], y=[sy, ey],
        mode="lines+markers",
        line=dict(width=2, color=color),
        marker=dict(size=10, symbol="arrow-wide", angleref="previous"),
        legendgroup=group, showlegend=False,
    )

def addFieldStyle(fig, row=None, col=None):
    kw = dict(row=row, col=col) if row else {}
    for shape in FIELD_SHAPES:
        fig.add_shape(**shape, layer="below", **kw)
    fig.add_trace(go.Scatter(**CENTER_MARKER.to_plotly_json()), **kw)
    axes_kw = dict(showticklabels=False, showgrid=False, showline=False, zeroline=False)
    fig.update_xaxes(**axes_kw, range=[0, 40],  **kw)
    fig.update_yaxes(**axes_kw, range=[0, 110], **kw)

def buildBuckets(data, legend, thrower, render_order):
    color_to_group = {c: n for n, c in legend.items()}
    buckets = {c: [] for c in render_order}
    for _, row in data.iterrows():
        sx = X_MIN + row[STARTX] * (X_MAX - X_MIN)
        sy = Y_MAX + row[STARTY] * (Y_MIN - Y_MAX)
        ex = X_MIN + row[ENDX]   * (X_MAX - X_MIN)
        ey = Y_MAX + row[ENDY]   * (Y_MIN - Y_MAX)
        c  = color(row, thrower)
        buckets[c].append(makeTrace(sx, sy, ex, ey, c, color_to_group[c]))
    return buckets

def buildFig(title, data, render_order, legend, thrower=True):
    fig = go.Figure()
    fig.update_layout(
        title=dict(text=title, x=0.12, y=0.96, font=dict(size=15)),
        width=400, height=700,
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        margin=dict(l=50, r=0, t=50, b=50),
    )
    addFieldStyle(fig)

    buckets = buildBuckets(data, legend, thrower, render_order)
    for c in render_order:
        for trace in buckets[c]:
            fig.add_trace(trace)

    total = sum(len(v) for v in buckets.values())
    fig.update_layout(title=dict(text=f"{title} ({total})"))

    counts = {c: len(v) for c, v in buckets.items()}
    for name, color in legend.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=color, width=3),
            name=f"{name} ({counts.get(color, 0)})",
            legendgroup=name, showlegend=True,
        ))

    return fig

def buildTeamFig(fig, title, data, row, col):
    render_order = (BLUE, LIGHTBLUE, GREEN, PURPLE, RED)
    buckets = buildBuckets(data, PASS_LEGEND, thrower=True, render_order=render_order)

    for c in render_order:
        for trace in buckets[c]:
            fig.add_trace(trace, row=row, col=col)

    total = sum(len(v) for v in buckets.values())
    title = f"{title} ({total})"

    fig.layout.annotations[col - 1].text = title
    fig.layout.annotations[col - 1].font.size=15
    addFieldStyle(fig, row=row, col=col)

def genPasses(data):
    fig = buildFig("Passes", data,
          render_order=(BLUE, LIGHTBLUE, GREEN, PURPLE, RED),
          legend=PASS_LEGEND, thrower=True)
    return fig

def genReceptions(data):
    fig = buildFig("Receptions", data,
          render_order=(BLUE, LIGHTBLUE, GREEN, RED, PURPLE),
          legend=RECEP_LEGEND, thrower=False)
    return fig

def genTeamPasses(data, header):
    h = data['Huck?'] == 1
    s = data['From sideline?'] == 1
    r = data[STARTY] <= 0.35
    masks = {name: fn(h, s, r) for name, fn in TEAM_MASKS.items()}

    fig = make_subplots(
        rows=1, cols=len(masks),
        subplot_titles=list(masks.keys()),
        horizontal_spacing=0.01, # reduce gap between subplots
    )
    fig.update_layout(
        title=dict(text=header, x=0.01, y=0.96, font=dict(size=15)),
        plot_bgcolor=WHITE, paper_bgcolor=WHITE,
        width=900, height=700,
        margin=dict(l=10, r=10, t=80, b=20),
        legend=dict(orientation="h", x=0.01, y=-0.01)
    )

    for col, (title, mask) in enumerate(masks.items(), start=1):
        buildTeamFig(fig, title, data[mask], row=1, col=col)

    for name, color in PASS_LEGEND.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="lines",
            line=dict(color=color, width=3),
            name=name, legendgroup=name, showlegend=True,
        ))

    return fig
